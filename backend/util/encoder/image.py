from __future__ import annotations

from .encoder import Encoder

from comcam.stream.profile import StreamFormat

import numpy as np
from PIL import Image
from io import BytesIO

from typing import Callable
from numpy.typing import NDArray


class JPEGEncoder(Encoder):
    """
    Default JPEG encoder.
    """

    def __init__(self, 
                 encoders : dict[StreamFormat, Callable[[NDArray], bytes]] | None = None,
                 quality: int = 85
                 ):
        
        super().__init__()

        # boundary check for quality
        if not 0 <= quality <= 100:
            raise RuntimeError("Quality for JPEG images must be between 0 and 100.")

        # store quality
        self.quality = quality

        # encoder map
        self._encoders: dict[StreamFormat, Callable[[NDArray], bytes]] = {
            StreamFormat.RGB8: self._rgb8,
            StreamFormat.GRAY8: self._gray8,
        } # default encoder

        if encoders is not None:
            # update encoder with provided one
            self._encoders.update(encoders)

    
    def encodable(self, format):
        return format in self._encoders


    def encode(self, data : NDArray, format : StreamFormat):
        return self._encoders[format](data)

    
    """
    Pre-defined encoders
    """

    def _rgb8(self, data : NDArray) -> bytes:
        
        image = Image.fromarray(
            data.astype(np.uint8),
            mode="RGB"
            )

        buffer = BytesIO()
        image.save(
            buffer, 
            format="JPEG", 
            quality=self.quality
            )

        return buffer.getvalue()


    def _gray8(self, data : NDArray) -> bytes:
        
        image = Image.fromarray(
            data.astype(np.uint8), 
            mode="L"
            )

        buffer = BytesIO()
        image.save(
            buffer, 
            format="JPEG", 
            quality=self.quality
            )

        return buffer.getvalue()