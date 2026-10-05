from dataclasses import dataclass
from pydantic import BaseModel


class MetricModel(BaseModel):
    current : float
    max : float | None = None


class DiskMetricsModel(BaseModel):
    usage : MetricModel


class RAMMetricsModel(BaseModel):
    usage : MetricModel


class CPUMetricsModel(BaseModel):
    usage : MetricModel
    temperature : MetricModel | None = None


class GPUMetricsModel(BaseModel):
    name : str | None = None
    usage : MetricModel | None = None
    temperature : MetricModel | None = None
    vram_usage : MetricModel | None = None
    power_usage : MetricModel | None = None
    clock : MetricModel | None = None
    fan_speed : MetricModel | None = None


class HardwareMetricsModel(BaseModel):
    disk : DiskMetricsModel
    ram : RAMMetricsModel
    cpu : CPUMetricsModel
    gpus: list[GPUMetricsModel] | None = None