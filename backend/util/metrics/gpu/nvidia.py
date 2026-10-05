from ....models.metrics import *

from threading import Lock # for thread-safe queries

# for testing & debugging
import logging
from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)


try:
    import pynvml
except ImportError:
    pynvml = None
    logger.info(
        "pynvml package is not installed. Nvidia GPUs will not be listed."
        )
except Exception:
    pynvml = None
    logger.exception(
        "NVML: An unexpected error occured while importing pynvml."
        "Nvidia GPUs will not be listed."
        )


_nvmi_stable = True

_lock_nvml = Lock()

def get_gpu_metrics() -> list[GPUMetricsModel] | None:

    def _critical_section():
        
        # check if any nvidia gpus exist
        try:
            n_devices = pynvml.nvmlDeviceGetCount()
            if n_devices < 1:
                return # no device exists
        except pynvml.NVMLError:
            logger.exception("NVML: Couldn't get device count.")
            return

        gpus = []

        for idx_dev in range(n_devices):

            try:
                hnd_dev = pynvml.nvmlDeviceGetHandleByIndex(idx_dev)
            except pynvml.NVMLError:
                logger.exception("NVML: Couldn't get device handle.")
                continue

            gpu_metrics = GPUMetricsModel()

            name_dev = None
            # gpu name
            try:
                name_dev = pynvml.nvmlDeviceGetName(hnd_dev)
                gpu_metrics.name = name_dev
            except pynvml.NVMLError:
                logger.exception("NVML: Couldn't get device name.")

            # gpu usage
            try:
                util_rates = pynvml.nvmlDeviceGetUtilizationRates(hnd_dev)
                gpu_metrics.usage = MetricModel(
                    current=float(util_rates.gpu),
                    max=100.0
                    )
            except pynvml.NVMLError:
                logger.exception(
                    "NVML: Couldn't get utilization rates of device: %s", 
                    "Unknown" if name_dev is None else name_dev
                    )

            # gpu temperature
            try:
                temp = pynvml.nvmlDeviceGetTemperatureV(
                    hnd_dev, 
                    pynvml.NVML_TEMPERATURE_GPU
                    )
                gpu_metrics.temperature = MetricModel(
                    current=float(temp)
                    )
            except pynvml.NVMLError:
                logger.exception(
                    "NVML: Couldn't get GPU temperature of device: %s", 
                    "Unknown" if name_dev is None else name_dev
                    )

            # vram usage
            try:
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(hnd_dev)
                gpu_metrics.vram_usage = MetricModel(
                    current = mem_info.used / 1_000_000, 
                    max = mem_info.total / 1_000_000
                    )
            except pynvml.NVMLError:
                logger.exception(
                    "NVML: Couldn't get memory information of device: %s", 
                    "Unknown" if name_dev is None else name_dev
                    )

            # power usage
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(hnd_dev)
                gpu_metrics.power_usage = MetricModel(
                    current = power_usage / 1000 # mW to W
                    )
            except pynvml.NVMLError:
                logger.exception(
                    "NVML: Couldn't get power usage of device: %s", 
                    "Unknown" if name_dev is None else name_dev
                    )

            # clock
            try:
                clock_cur = pynvml.nvmlDeviceGetClockInfo(
                    hnd_dev, 
                    pynvml.NVML_CLOCK_GRAPHICS
                    )
                clock_max = pynvml.nvmlDeviceGetMaxClockInfo(
                    hnd_dev,
                    pynvml.NVML_CLOCK_GRAPHICS
                    )
                gpu_metrics.clock = MetricModel(
                    current=float(clock_cur),
                    max=float(clock_max)
                    )
            except pynvml.NVMLError:
                logger.exception(
                    "NVML: Couldn't get clock information of device: %s", 
                    "Unknown" if name_dev is None else name_dev
                    )

            # fan speed
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(hnd_dev)
                gpu_metrics.fan_speed = MetricModel(
                    current=float(fan_speed)
                    )
            except pynvml.NVMLError:
                logger.exception(
                    "NVML: Couldn't get fan speed of device: %s", 
                    "Unknown" if name_dev is None else name_dev
                    )

            # add metrics for current gpu to the set
            gpus.append(gpu_metrics)

        return gpus

    with _lock_nvml:

        gpus = None

        if _is_pynvml_imported() and _nvmi_stable:

            _enter_safe()

            try:
                gpus = _critical_section()
            except Exception:
                logger.exception("An unexpected error occured.")

            _exit_safe()

        return gpus


def _is_pynvml_imported():
    return pynvml is not None


def _enter_safe():
    try:
        pynvml.nvmlInit()
    except pynvml.NVMLError:
        _exit_safe()
        logger.exception("NVML: Couldn't initialize.")


def _exit_safe():
    global _nvmi_stable
    try:
        pynvml.nvmlShutdown()
    except pynvml.NVMLError:
        _nvmi_stable = False
        logger.exception("NVML: Couldn't shutdown. Set as unstable.")