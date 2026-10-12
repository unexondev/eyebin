import { ssdb } from "@/lib/db";

import { useEffect, useState } from "react";
import { useLiveQuery } from "dexie-react-hooks"

import {
  Attachment,
  AttachmentAction,
  AttachmentActions,
  AttachmentContent,
  AttachmentDescription,
  AttachmentMedia,
  AttachmentTitle,
  AttachmentTrigger
} from "@/components/ui/attachment"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area";

import AnnotationPanel from "@/components/annotation-panel";

import { MdDeleteOutline } from "react-icons/md";
import { RiImageUploadLine } from "react-icons/ri";
import { LuMousePointerClick } from "react-icons/lu";


export default function FramesPanel() {

    const snapshots = useLiveQuery(
        () => ssdb.snapshots.orderBy("timestamp").reverse().toArray()
    );
    
    const [ image_urls, setImageUrls ] = useState<string[]>([]);

    const [ image_idx_selected, setImageIdxSelected ] = useState<number | null>(null);

    useEffect(() => {

        image_urls.forEach(URL.revokeObjectURL)
        
        setImageUrls(
            snapshots?.map(
                snapshot => URL.createObjectURL(snapshot.image)
            ) ?? []
        )

        return () => {
            image_urls.forEach(URL.revokeObjectURL);
            setImageUrls([])
        };

    }, [ snapshots ])

    return (
        <div className="@container flex flex-col h-full w-full gap-5 p-3">

            <div className="flex flex-row items-center justify-center gap-3 text-primary/50 text-lg">
                <LuMousePointerClick size="1.5rem"/>
                Click on an image to view annotation panel
            </div>

            <ScrollArea className="flex-1 min-h-0 px-5">

                <div className="grid grid-cols-2 gap-5">

                    {
                        snapshots ? (

                            snapshots.map((snapshot, idx) => (

                                <Attachment key={snapshot.id} orientation="horizontal" className="w-full">

                                    <AttachmentMedia variant="image">
                                        <img src={image_urls[idx]} alt={`${snapshot.sensor.device_name} - ${snapshot.sensor.device_serial_number}`}/>
                                    </AttachmentMedia>

                                    <AttachmentContent>
                                        <AttachmentTitle>{snapshot.sensor.device_name}</AttachmentTitle>
                                        <AttachmentDescription>{new Date(snapshot.timestamp).toLocaleString()}</AttachmentDescription>
                                    </AttachmentContent>

                                    <AttachmentActions>
                                        <AttachmentAction aria-label={`Remove ${snapshot.id}`} onClick={
                                            () => { ssdb.snapshots.delete(snapshot.id) }
                                            }>
                                            <MdDeleteOutline />
                                        </AttachmentAction>
                                    </AttachmentActions>

                                <AttachmentTrigger
                                    render={
                                        <a href="" onClick={(e) => {
                                            e.preventDefault();
                                            setImageIdxSelected(idx);
                                        }}/>
                                    }
                                />

                                </Attachment>

                            ))

                        ) : (
                            null
                        )
                    }

                </div>

            </ScrollArea>

            <Button className="py-5" variant="outline"><RiImageUploadLine/> Upload an image</Button>

            <Dialog open={image_idx_selected !== null} onOpenChange={open_state => !open_state && setImageIdxSelected(null)} >
                <DialogContent className="w-[90vw] h-[90vh] max-w-none sm:max-w-none">
                    <DialogHeader>
                        <DialogTitle>Annotate Snapshot</DialogTitle>
                        <DialogDescription>Annotations made on a snapshot then can be passed to a ML model.</DialogDescription>
                    </DialogHeader>
                    {
                        image_idx_selected !== null ? <AnnotationPanel image_url={image_urls[image_idx_selected]}/> : null
                    }
                    <DialogFooter>
                        <DialogClose render={<Button variant="outline" onClick={() => setImageIdxSelected(null)}>Cancel</Button>} />
                        <Button type="submit">Save changes</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

        </div>
    )

}