from .amd import get_gpu_metrics as get_gpu_metrics_amd
from .nvidia import get_gpu_metrics as get_gpu_metrics_nvidia
from .jetson import get_gpu_metrics as get_gpu_metrics_jetson


__all__ = [
    "get_gpu_metrics_amd",
    "get_gpu_metrics_nvidia",
    "get_gpu_metrics_jetson"
]