import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { AspectRatio } from "@/components/ui/aspect-ratio"

import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

export default function StreamPanel(props: any) {

    return (
        <div className="flex flex-col h-full w-full">

            <div className="flex-1 w-full flex flex-col justify-center">

                <AspectRatio ratio={16 / 9} className="bg-muted w-full">


                </AspectRatio>

                <div className="p-5 flex gap-5 items-center">

                    <Select items={props.stream_profiles}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="Select Stream Profile"/>
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                            {props.stream_profiles.map((stream_profile: any) => (
                                <SelectItem key={stream_profile.id} value={stream_profile.id}>
                                {stream_profile.label}
                                </SelectItem>
                            ))}
                            </SelectGroup>
                        </SelectContent>
                    </Select>

                    <div>
                        Sensor: XXX
                    </div>
                    <Separator orientation="vertical"/>
                    <div>
                        State: <span className="text-green-500">Running</span>
                    </div>
                    <Separator orientation="vertical"/>
                    <div>
                        Model: <span className="text-yellow-500">No model set</span>
                    </div>
                </div>

            </div>

            <div className="p-5 flex justify-end gap-3">

                <Button className="relative" size="lg">Refresh</Button>
                <Button className="relative" size="lg">Snapshot</Button>

            </div>

        </div>
    )

}