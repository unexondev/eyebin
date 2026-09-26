import axios from "axios"

import { useEffect, useState, useRef } from "react"

import { getStreamProfileLabel, SensorState, RENDERABLE_FORMATS, profilesEquivalent } from "@/lib/defs"
import type { SensorResponse, StreamProfileModelType, AppActions, StatusResponse, StreamModel } from "@/lib/defs"

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

import { FaCircle } from "react-icons/fa";
import { CgSpinnerTwoAlt } from "react-icons/cg";
import { AiOutlineDisconnect } from "react-icons/ai";
import { api } from "@/lib/api"


interface StreamPanelProps {
    appActions: AppActions
    sensors: SensorResponse[] | null
    loadSensors: () => void
}

export default function StreamPanel({ appActions, sensors, loadSensors }: StreamPanelProps) {

    const [ sensor_id_selected, setSensorIdSelected ] = useState<string | null>(null);

    const sensor_selected = sensors?.find((sensor) => sensor.id === sensor_id_selected);

    const profiles = sensor_selected?.supported_profiles ?? [];

    const [profile_idx_selected, setProfileIdxSelected] = useState<number | null>(null);

    const profile_selected = profile_idx_selected != null ? profiles[profile_idx_selected] : undefined 

    const socket = useRef<WebSocket | null>(null);

    function is_profile_active(profile : StreamProfileModelType): boolean | undefined {
        return is_selected_sensor_streaming() && sensor_selected?.config.entries.some((entry) => profilesEquivalent(profile, entry.profile));
    }

    function is_selected_sensor_streaming(): boolean | undefined {
        return sensor_selected?.state === SensorState.STREAMING;
    }

    async function startStream() {

		appActions.setLoading();

		try {
			
			await api.post<StatusResponse>("/stream/start", {
                sensor_id: sensor_id_selected as string,
                profiles: [profile_selected] as StreamProfileModelType[]
            });

            appActions.pushNotification("Stream has been started succesfully.")

		} catch (error: any) {
			
			if (axios.isAxiosError(error)) {
				appActions.pushError(
                    error.response?.data?.detail ?? 
                    "An error occurred while establishing connection."
                );
			}

			else {
				appActions.pushError("An unexpected error occurred.");
			}
		
		}

		finally {

            loadSensors()

			// appActions.setReady()

		}

    }

    async function stopStream() {

		appActions.setLoading();

		try {
			
			await api.post<StatusResponse>("/stream/stop", {
                sensor_id: sensor_id_selected as string,
                profiles: [profile_selected] as StreamProfileModelType[]
            });

            appActions.pushNotification("Stream has been stopped succesfully.")

		} catch (error: any) {
			
			if (axios.isAxiosError(error)) {
				appActions.pushError(
                    error.response?.data?.detail ?? 
                    "An error occurred while establishing connection."
                );
			}

			else {
				appActions.pushError("An unexpected error occurred.");
			}
		
		}

		finally {

            loadSensors()

			// appActions.setReady()

		}

    }

    useEffect(() => {
        setSensorIdSelected(null);
    }, [sensors]); // sensor selection determinism

    useEffect(() => {
        setProfileIdxSelected(null);
    }, [sensor_id_selected]); // profile selection determinism

    useEffect(() => { // connect to socket automatically

        if (profile_selected === undefined) return;

        if (!is_selected_sensor_streaming()) return;

        const entry_used = sensor_selected?.config.entries.find((entry) => profilesEquivalent(profile_selected, entry.profile))

        if (entry_used === undefined) return;

        const params = new URLSearchParams({
                id: entry_used.stream.id
            }).toString()

        const ws = socket.current = new WebSocket(`ws://localhost:8000/api/stream/consume?${params}`);

        ws.onclose = () => {

            appActions.pushNotification("Connection with the stream provider has been closed.");

        }

        ws.onerror = () => {

            appActions.pushError("An error occured while communicating with the stream provider.");

        }

        ws.onopen = () => {

            appActions.pushNotification("Connection established with the stream provider.")

        }

        return () => {
            if (ws.readyState < WebSocket.CLOSING) // [ CONNECTING, OPEN ]
                ws.close()
        }

    }, [profile_idx_selected])

    return (
        <div className="flex flex-col h-full w-full">

            <div className="flex-1 w-full flex flex-col p-5">

                <AspectRatio ratio={16 / 9} className="bg-muted w-full relative">
                    {
                        profile_selected && is_profile_active(profile_selected) && socket.current ? (
                            
                            socket.current.readyState === WebSocket.CONNECTING ? (
                                <div className="absolute inset-0 flex items-center justify-center">
                                    <CgSpinnerTwoAlt className="animate-spin" size="2.5rem"/>
                                </div>
                            ) : (
                                socket.current.readyState > WebSocket.CLOSING ? (
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <AiOutlineDisconnect size="2.5rem"/>
                                    </div>
                                ) : (
                                    <img></img>
                                )
                            )

                        ) : null
                    }
                </AspectRatio>

                <div className="mt-3 flex flex-col gap-3">

                    <div className="flex flex-col lg:flex-row gap-3">
                        <Select value={sensor_id_selected} onValueChange={setSensorIdSelected}>
                            <SelectTrigger className="lg:flex-1 w-full">
                                <SelectValue placeholder="Select Sensor">
                                    {
                                        sensor_selected ? (

                                            <>
                                                {
                                                    is_selected_sensor_streaming() ? (
                                                        <div className="flex justify-center items-center">
                                                            <FaCircle className="!w-2 text-green-500"/>
                                                        </div>
                                                    ) : null
                                                }

                                                {
                                                    sensor_selected.device_name
                                                }
                                            </>

                                        ) : undefined
                                    }
                                </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                {sensors?.map((sensor) => (
                                    <SelectItem key={sensor.id} value={sensor.id}>
                                        {
                                            sensor.state === SensorState.STREAMING ? (
                                                <div className="flex justify-center items-center">
                                                    <FaCircle className="!w-2 text-green-500"/>
                                                </div>
                                            ) : null
                                        }
                                        
                                        {
                                            sensor.device_name
                                        }
                                    </SelectItem>
                                ))}
                                </SelectGroup>
                            </SelectContent>
                        </Select>

                        <Separator orientation="vertical"/>
                        <Select value={profile_idx_selected} onValueChange={setProfileIdxSelected}>
                            <SelectTrigger className="lg:flex-1 w-full">
                                <SelectValue placeholder="Select Profile">
                                    {
                                        profile_selected ? (

                                            <>
                                                {
                                                    is_profile_active(profile_selected) ? (
                                                        <div className="flex justify-center items-center">
                                                            <FaCircle className="!w-2 text-green-500"/>
                                                        </div>
                                                    ) : null
                                                }

                                                {
                                                    getStreamProfileLabel(profile_selected)
                                                }
                                            </>

                                        ) : undefined
                                    }
                                </SelectValue>
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                {
                                    profiles.filter(profile => RENDERABLE_FORMATS.includes(profile.format))
                                        .map((profile, idx) => (
                                            <SelectItem key={idx} value={idx} disabled={is_selected_sensor_streaming() && !is_profile_active(profile)}>
                                                
                                                {
                                                    is_selected_sensor_streaming() && is_profile_active(profile) ? (
                                                        <div className="flex justify-center items-center">
                                                            <FaCircle className="!w-2 text-green-500"/>
                                                        </div>
                                                    ) : null
                                                }
                                                
                                                {
                                                    getStreamProfileLabel(profile)
                                                }
                                            
                                            </SelectItem>
                                        ))
                                }
                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    </div>

                    <Separator orientation="horizontal"/>

                    <div className="flex flex-row justify-end items-center gap-5">
                        
                        {
                            sensor_selected ? (
                                is_selected_sensor_streaming() ? (
                                    <div className="flex flex-row items-center gap-2 text-green-500 py-2">
                                        <FaCircle/> Streaming
                                    </div>
                                ) : (
                                    <div className="flex flex-row items-center gap-2 text-red-500 py-2">
                                        <FaCircle/> Not Streaming
                                    </div>
                                )
                            ) : null
                        }
                        
                        {
                            sensor_selected?.state != SensorState.STREAMING ? (
                                profile_selected ?
                                <Button size="lg" onClick={startStream} className="bg-green-700 text-white hover:bg-green-500">
                                    Start Stream
                                </Button> : null
                            ) : (
                                <Button size="lg" onClick={stopStream} className="bg-red-700 text-white hover:bg-red-500">
                                    Stop Stream
                                </Button>
                            )
                        }

                    </div>

                </div>

            </div>

            <div className="p-5 flex justify-end gap-3">

                <Button className="relative" size="lg" onClick={loadSensors}>Refresh</Button>
                <Button className="relative" size="lg">Snapshot</Button>

            </div>

        </div>
    )

}