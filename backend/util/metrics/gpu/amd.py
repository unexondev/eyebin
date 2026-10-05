"""
NOTE:   This module has not been tested properly and may be inconsistent.
        We'll appreciate your tests and PRs if you have any AMD GPUs mounted.
"""

from ....models.metrics import *

from threading import Lock # for thread-safe queries

# for testing & debugging
import logging
from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)


try:
    import amdsmi
except ImportError:
    amdsmi = None
    logger.info(
        "amdsmi package is not installed. AMD GPUs will not be listed."
        )
except Exception:
    amdsmi = None
    logger.exception(
        "AMDSMI: An unexpected error occured while importing amdsmi. "
        "AMD GPUs will not be listed."
        )

_amdsmi_stable = True

_lock_amdsmi = Lock()

def get_gpu_metrics() -> list[GPUMetricsModel] | None:

    def _critical_section():
        
        # get handles for all gpus
        try:
            hnd_procs = amdsmi.amdsmi_get_processor_handles()
        except amdsmi.AmdSmiException:
            logger.exception("AMDSMI: Couldn't get processor handles.")
            return

        gpus = []

        for hnd_proc in hnd_procs:

            try:
                if (amdsmi.amdsmi_get_processor_type(hnd_proc)["processor_type"] !=
                    amdsmi.AmdSmiProcessorType.AMDSMI_PROCESSOR_TYPE_AMD_GPU.name):
                    continue
            except amdsmi.AmdSmiException:
                logger.exception("AMDSMI: Couldn't get processor type.")
                continue

            gpu_metrics = GPUMetricsModel()

            name_proc = None
            # gpu name
            try:
                name_proc = amdsmi.amdsmi_get_gpu_asic_info(hnd_proc)["market_name"]
                gpu_metrics.name = name_proc
            except amdsmi.AmdSmiException:
                logger.exception("AMDSMI: Couldn't get GPU's ASIC information.")

            # gpu usage
            try:
                gpu_activity = amdsmi.amdsmi_get_gpu_activity(hnd_proc)["gfx_activity"]
                gpu_metrics.usage = MetricModel(
                    current=float(gpu_activity),
                    max=100.0
                    )
            except amdsmi.AmdSmiException:
                logger.exception(
                    "AMDSMI: Couldn't get GPU activity of device: %s", 
                    "Unknown" if name_proc is None else name_proc
                    )

            # gpu temperature
            try:
                temp = amdsmi.amdsmi_get_temp_metric(
                    hnd_proc,
                    amdsmi.AmdSmiTemperatureType.EDGE,
                    amdsmi.AmdSmiTemperatureMetric.CURRENT
                    )
                gpu_metrics.temperature = MetricModel(
                    current = temp / 1000 # millidegrees celcius to celcius
                    )
            except amdsmi.AmdSmiException:
                logger.exception(
                    "AMDSMI: Couldn't get GPU temperature of device: %s", 
                    "Unknown" if name_proc is None else name_proc
                    )

            # vram usage
            try:
                vram_total = amdsmi.amdsmi_get_gpu_memory_total(
                    hnd_proc,
                    amdsmi.AmdSmiMemoryType.VRAM
                    )
                vram_used = amdsmi.amdsmi_get_gpu_memory_usage(
                    hnd_proc,
                    amdsmi.AmdSmiMemoryType.VRAM
                    )
                gpu_metrics.vram_usage = MetricModel(
                    current= vram_used / 1_000_000, 
                    max = vram_total / 1_000_000
                    )
            except amdsmi.AmdSmiException:
                logger.exception(
                    "AMDSMI: Couldn't get VRAM usage of device: %s", 
                    "Unknown" if name_proc is None else name_proc
                    )

            # power usage
            try:
                power_usage = amdsmi.amdsmi_get_power_info(hnd_proc)["socket_power"]
                gpu_metrics.power_usage = MetricModel(
                    current=float(power_usage)
                    )
            except amdsmi.AmdSmiException:
                logger.exception(
                    "AMDSMI: Couldn't get power information of device: %s", 
                    "Unknown" if name_proc is None else name_proc
                    )

            # clock
            try:
                clock_info = amdsmi.amdsmi_get_clock_info(
                    hnd_proc,
                    amdsmi.AmdSmiClkType.GFX
                    )
                gpu_metrics.clock = MetricModel(
                    current=float(clock_info["clk"]),
                    max=float(clock_info["max_clk"])
                    )
            except amdsmi.AmdSmiException:
                logger.exception(
                    "AMDSMI: Couldn't get clock information of device: %s", 
                    "Unknown" if name_proc is None else name_proc
                    )

            # fan speed
            try:
                fan_speed_max = amdsmi.amdsmi_get_gpu_fan_speed_max(
                    hnd_proc,
                    0 # just the first sensor
                    )
                fan_speed = amdsmi.amdsmi_get_gpu_fan_speed(
                    hnd_proc,
                    0
                    )
                gpu_metrics.fan_speed = MetricModel(
                    current=float(fan_speed / fan_speed_max)
                    )
            except amdsmi.AmdSmiException:
                logger.exception(
                    "AMDSMI: Couldn't get fan speeds of device: %s", 
                    "Unknown" if name_proc is None else name_proc
                    )

            # add metrics for current gpu to the set
            gpus.append(gpu_metrics)

        return gpus

    with _lock_amdsmi:

        gpus = None

        if _is_amdsmi_imported() and _amdsmi_stable:

            _enter_safe()

            try:
                gpus = _critical_section()
            except Exception:
                logger.exception("An unexpected error occured.")

            _exit_safe()

        return gpus
    

def _is_amdsmi_imported():
    return amdsmi is not None


def _enter_safe():
    try:
        amdsmi.amdsmi_init(
            amdsmi.AmdSmiInitFlags.INIT_AMD_GPUS
            )
    except amdsmi.AmdSmiException:
        _exit_safe()
        return


def _exit_safe():
    global _amdsmi_stable
    try:
        amdsmi.amdsmi_shut_down()
    except amdsmi.AmdSmiException:
        _amdsmi_stable = False