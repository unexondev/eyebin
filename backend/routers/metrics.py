from fastapi import APIRouter

from ..models.metrics import *
from ..util.metrics.gpu import *

import psutil # for retrieving hardware metrics

import asyncio # for parallel execution

# for testing & debugging
import logging
from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/metrics")

@router.get("/all", response_model=HardwareMetricsModel)
async def get_hardware_metrics():

    logger.debug("Get all hardware metrics request received.")

    def _get_hardware_metrics():
        """
        Retrieving hardware metrics from OS / drivers can take much time,
        that's why we are executing them on a different thread so
        event loop doesn't get blocked while waiting responses from OS / drivers.  
        """

        # disk
        ps_disk_usage = psutil.disk_usage("/")
        disk = DiskMetricsModel(
            usage = MetricModel(
                current = ps_disk_usage.used / 1_000_000,
                max = ps_disk_usage.total / 1_000_000
                )
            )

        # ram
        ps_ram = psutil.virtual_memory()
        ram = RAMMetricsModel(
            usage = MetricModel(
                current = ps_ram.used / 1_000_000,
                max= ps_ram.total / 1_000_000
                )
            )

        # cpu
        ps_cpu_usage = psutil.cpu_percent()
        cpu_temperature = None # TODO
        cpu = CPUMetricsModel(
            usage = MetricModel(
                current=ps_cpu_usage,
                max=100.0
                ),
            temperature=cpu_temperature
            )

        # gpu metrics for all gpus
        gpus = []

        gpus_nvidia = get_gpu_metrics_nvidia()
        if gpus_nvidia is not None:
            gpus += gpus_nvidia

        gpus_amd = get_gpu_metrics_amd()
        if gpus_amd is not None:
            gpus += gpus_amd

        gpus_jetson = get_gpu_metrics_jetson()
        if gpus_jetson is not None:
            gpus += gpus_jetson

        return HardwareMetricsModel(
            disk=disk,
            ram=ram,
            cpu=cpu,
            gpus=gpus
            )

    # execute it parallelly
    return await asyncio.to_thread(_get_hardware_metrics)