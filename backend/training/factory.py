import torch
import numpy as np
from numpy.typing import NDArray

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

from dataclasses import dataclass

import pathlib

path = pathlib.Path(__file__)
dir_prj = path.parents[3]
dir_ckpts = dir_prj.joinpath("checkpoints/")
dir_cfgs = dir_prj.joinpath("configs/")


@dataclass
class MaskFactoryOptions:
    refine_iteratively : bool = True
    """
    TODO
    """


PointCoords = list[tuple[int, int]]
    
class MaskFactory:
    """
    Produces segmentation masks using a pre-trained SAM-2 model given on initialization.
    """

    def __init__(self, model, options : MaskFactoryOptions, logit_init : NDArray | None = None):

        # define the model
        self.model = model

        # define options
        self.opts = options

        # create the predictor object
        self.predictor = SAM2ImagePredictor(self.model)

        # we use this logit for iterative training FIXME better docstring
        self.logit_max = logit_init

        self.mask = None


    @classmethod
    def create(cls,
               ckpt_name_or_path : str,
               cfg_path : str,
               options : MaskFactoryOptions,
               device : str = None,
               logit_init : NDArray | None = None
               ):
        """
        Craete a MaskFactory instance with a SAM-2 model loaded.

        Args:
            ckpt_name_or_path: Name or full path of the checkpoint file located in `<PROJECTROOT>/checkpoints/` directory
            cfg_path: Path of the config file relative to the SAM-2 root directory, typically starts with `configs/...`

        Returns:
            A new `MaskFactory` instance.
        """
        # set the device if not given
        if not device:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        # build SAM-2 model
        is_abs_ckpt = pathlib.Path(ckpt_name_or_path).is_absolute()

        sam2_model = build_sam2(
            ckpt_path=str(dir_ckpts.joinpath(ckpt_name_or_path)) if not is_abs_ckpt else ckpt_name_or_path,
            config_file=cfg_path, # config file path is resolved internally
            device=device
            )
        
        return cls(
            model=sam2_model,
            options=options,
            logit_init=logit_init
            ) # return a new instance


    """
    Access functions
    """

    def get(self):
        return self.mask


    """
    Main functions
    """

    def produce(self,
                stream_data : NDArray[np.uint8],
                include_points : PointCoords,
                exclude_points : PointCoords,
                **predict_options
                ) -> NDArray:
        """
        Produces a segmentation mask using given image data.

        TODO better docstring
        """
        prd = self.predictor
        opts = self.opts

        # set image
        prd.set_image(stream_data)

        # concat points
        ndarr_pts = np.array(include_points + exclude_points)

        if ndarr_pts.size <= 0:
            return None # no points given

        # define labels
        ndarr_labels = np.concatenate([
            [1] * len(include_points),
            [0] * len(exclude_points)
            ])

        # perform a prediction
        masks, scores, logits = prd.predict(
            point_coords=ndarr_pts,
            point_labels=ndarr_labels,
            mask_input=self.logit_max[None] if self.logit_max is not None else self.logit_max,
            **predict_options # pass options
            )

        """
        
        The outputs are mapped by their first dimension:
            
            masks[i]  = segmentation mask of prediction i
            scores[i] = quality score of prediction i
            logits[i] = raw mask logits of prediction i
        
        """

        # get the max score index
        idx_best = np.argmax(scores)

        # get the max scored mask
        mask_max : NDArray[np.float32] = masks[idx_best]
        self.mask = mask_max.astype(np.bool)

        if opts.refine_iteratively:
            # get the max scored logit
            self.logit_max = logits[idx_best]

        return True
    

"""
TEST
"""    
def test():
    from PIL import Image
    import cv2

    maskfactory = MaskFactory.create(
        ckpt_name_or_path="sam2.1_hiera_tiny.pt",
        cfg_path="configs/sam2.1/sam2.1_hiera_t.yaml",
        options=MaskFactoryOptions(
            refine_iteratively=True
            )
        )

    include_coords : PointCoords = []
    exclude_coords : PointCoords = []

    def callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            include_coords.append((x, y))
            
        elif event == cv2.EVENT_MBUTTONDOWN:
            exclude_coords.append((x, y))

    fimage = Image.open("/home/cbsahmet/Dev/eyebin-clone/datasets/IMG-20260505-WA0137_jpg.rf.84f2adf308c8dcd6a4b37783cfaac18d.jpg")

    cv2.namedWindow("TEST-MASKFACTORY")
    cv2.setMouseCallback("TEST-MASKFACTORY", callback)

    while True:

        image = np.array(fimage)

        mask_cur = maskfactory.get()

        view = image
        if mask_cur is not None:
            # Maskeyi görüntüye uygula
            overlay = image.copy()
            overlay[mask_cur] = (0, 255, 0)
            view = cv2.addWeighted(
                image,
                0.6,
                overlay,
                0.4,
                0
            )
        cv2.imshow("TEST-MASKFACTORY", view)
        
        key = cv2.waitKey(500)

        if key == 27: # ESC
            # quit program
            break

        if key == 13: # Enter
            # perform a prediction
            maskfactory.produce(image, include_coords, exclude_coords)
            # then clear previous points
            include_coords.clear()
            exclude_coords.clear()