import {
  Progress,
  ProgressLabel,
  ProgressValue,
} from "@/components/ui/progress"
import { useEffect, useState, Fragment } from "react"

import { api } from "@/lib/api";
import type { HardwareMetricsModel, AppActions, MetricModel } from "@/lib/defs";

import axios from "axios";
import { Separator } from "@/components/ui/separator";

interface MonitorPanelProps {
    appActions: AppActions
}

export default function MonitorPanel({ appActions } : MonitorPanelProps) {

    const [ hardware_metrics, setHardwareMetrics ] = useState<HardwareMetricsModel | null>(null);


    useEffect(() => {

        let busy = false; // waiting for response?

        const getHardwareMetrics = async () => { 

            if (busy) return;

            busy = true;

            try {
                
                const res = await api.get<HardwareMetricsModel>("/metrics/all");
                
                setHardwareMetrics(res.data);
                
            } catch (error: any) {
                
                if (axios.isAxiosError(error)) {
                    appActions.pushError(
                        error.response?.data?.detail ??
                        "An error occured while establishing connection."
                    );
                }

                else {
                    appActions.pushError("An unexpected error occured.");
                }
            
            }

            finally {
                busy = false;
            }

        }

        const _init = async () => {

            appActions.setLoading();

            await getHardwareMetrics();

            appActions.setReady();

        }

        _init()

        const _interval = setInterval(
            getHardwareMetrics,
            1_000 // for every second
        )

        return () => clearInterval(_interval)

    }, [])

    const renderMetric = (metric : MetricModel | null, unit? : string, decimal_places = 1) => (
        <Progress value={
            metric?.max ? metric.current / metric.max * 100 : 0 
            } className="w-full">
            {
                unit ? (
                    <ProgressLabel>
                        {
                            metric ? (
                                `${metric.current.toFixed(decimal_places)}${unit}${metric.max ? ` / ${metric.max.toFixed(decimal_places)}${unit}` : ""}`
                            ) : "Not supported"
                        }
                    </ProgressLabel>
                ) : null
            }
            {
                metric?.max ? <ProgressValue/> : null
            }
        </Progress>
    )

    return (
        <div className="@container flex flex-col h-full w-full p-10 gap-10">

            {

                hardware_metrics ? (

                    <>
                    
                        <div className="flex flex-col gap-3">

                            <span className="text-xl">General Metrics</span>

                            <Separator/>

                        </div>

                        <div className="flex flex-col gap-10 @lg:flex-row @lg:gap-20">

                            <div className="flex-1 flex flex-col gap-5">

                                <h3>Disk Usage</h3>

                                { renderMetric(hardware_metrics.disk.usage, 'MB', 0) }

                            </div>

                            <div className="flex-1 flex flex-col gap-5">

                                <h3>RAM Usage</h3>

                                { renderMetric(hardware_metrics.ram.usage, 'MB', 0) }

                            </div>

                        </div>

                        <div className="flex flex-col gap-10 @lg:flex-row @lg:gap-20">


                            <div className="flex-1 flex flex-col gap-5">

                                <h3>CPU Usage</h3>

                                { renderMetric(hardware_metrics.cpu.usage) }

                            </div>


                            <div className="flex-1 flex flex-col gap-5">

                                <h3>CPU Temperature</h3>

                                { renderMetric(hardware_metrics.cpu.temperature, '°C') }

                            </div>

                        </div>

                        {

                            hardware_metrics.gpus?.map((gpu_metrics, idx) => (
                                
                                <Fragment key={idx}>
                                
                                    <div className="flex flex-col gap-3">

                                        <span className="text-xl">
                                            GPU Metrics <span className="text-primary/50">({ gpu_metrics.name ?? "Unknown" })</span>
                                            </span>

                                        <Separator/>

                                    </div>

                                    <div className="flex flex-col gap-10 @lg:flex-row @lg:gap-20">

                                        <div className="flex-1 flex flex-col gap-5">

                                            <h3>GPU Usage</h3>

                                            { renderMetric(gpu_metrics.usage) }

                                        </div>

                                        <div className="flex-1 flex flex-col gap-5">

                                            <h3>GPU Temperature</h3>

                                            { renderMetric(gpu_metrics.temperature, '°C') }

                                        </div>

                                        <div className="flex-1 flex flex-col gap-5">

                                            <h3>VRAM Usage</h3>

                                            { renderMetric(gpu_metrics.vram_usage, 'MB', 0) }

                                        </div>

                                    </div>

                                    <div className="flex flex-col gap-10 @lg:flex-row @lg:gap-20">

                                        <div className="flex-1 flex flex-col gap-5">

                                            <h3>GPU Power Usage</h3>

                                            { renderMetric(gpu_metrics.power_usage, 'W') }

                                        </div>

                                        <div className="flex-1 flex flex-col gap-5">

                                            <h3>GPU Clock</h3>

                                            { renderMetric(gpu_metrics.clock, 'MHz', 0) }

                                        </div>

                                        <div className="flex-1 flex flex-col gap-5">

                                            <h3>GPU Fan Speed</h3>

                                            { renderMetric(gpu_metrics.fan_speed, 'RPM') }

                                        </div>

                                    </div>
                                </Fragment>

                            ))

                        }
                    
                    </>
                    
                ) : null

            }

        </div>
    )

}