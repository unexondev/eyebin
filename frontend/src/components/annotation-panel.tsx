import { useState, useEffect, useRef } from "react";

import { Stage, Layer, Image } from "react-konva"
import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Button } from "@/components/ui/button";

import { MdOutlineZoomIn } from "react-icons/md";
import { MdOutlineZoomOut } from "react-icons/md";


export default function AnnotationPanel({ image_url } : { image_url : string }) {

    const [image_html, setImageHtml] = useState<HTMLImageElement | undefined>(undefined);

    const [container_size, setContainerSize] = useState({
        width: 0,
        height: 0,
    });

    const [image_attrs, setImageAttrs] = useState<{
        scale: number,
        x: number,
        y: number
    } | null>(null);

    let image_size : { width: number, height: number } | null = null;

    if (image_html && image_attrs) {

        image_size = {
            width: image_html.width * image_attrs.scale,
            height: image_html.height * image_attrs.scale
        }

    }

    const container_ref = useRef<HTMLDivElement>(null);

    function zoomIn() {

        if (!image_attrs) return;

        const scale_new = image_attrs.scale + 0.05

        setImageAttrs({ ...image_attrs, scale: scale_new })

    }


    function zoomOut() {

        if (!image_attrs) return;

        const scale_new = image_attrs.scale - 0.05

        setImageAttrs({ ...image_attrs, scale: scale_new })

    }


    useEffect(() => {

        const element = container_ref.current;

        if (!element) return;

        const observer = new ResizeObserver(([entry]) => {
            setContainerSize({
                width: entry.contentRect.width,
                height: entry.contentRect.height,
            });
        });

        observer.observe(element);

        return () => observer.disconnect();

    }, []);

    useEffect(() => {
        const img = new window.Image();

        img.onload = () => setImageHtml(img);
        img.src = image_url;

        return () => {
            img.onload = null;
        };
    }, [image_url]);

    useEffect(() => {

        if (!image_html) return;

        const scale = Math.min(
            container_size.width / image_html.width,
            container_size.height / image_html.height
        );

        const x = (container_size.width - image_html.width * scale) / 2;
        const y = (container_size.height - image_html.height * scale) / 2;

        setImageAttrs({ scale, x, y });

    }, [image_html])

    return (
        <AspectRatio ref={container_ref} ratio={16/9} className="w-full min-w-0 bg-muted max-h-full min-h-0">
            
            <div className="absolute flex flex-row gap-2 p-2 z-1">
                <Button className="size-10" onClick={zoomIn}><MdOutlineZoomIn className="size-8"/></Button>
                <Button className="size-10" onClick={zoomOut}><MdOutlineZoomOut className="size-8"/></Button>
            </div>
            
            {
                image_attrs ? (
                    <Stage width={container_size.width} height={container_size.height} className="m-auto">

                        <Layer>
                            <Image image={image_html} width={image_size?.width} height={image_size?.height} x={image_attrs.x} y={image_attrs.y}/>
                        </Layer>

                    </Stage>
                ) : null
            }
        </AspectRatio>
    )

}