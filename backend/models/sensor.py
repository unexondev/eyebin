from .stream import StreamProfileModel, StreamConfigModel, StreamConfigEntryModel, StreamModel, StreamProfileModelType
from ..util.cache import CacheManager

from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from comcam.core.sensor import Sensor, SensorState


class SensorModel(BaseModel):
    id : UUID = Field(default_factory=uuid4)
    device_name: str
    device_serial_number: str # identifier
    state: SensorState
    supported_profiles: list[
        StreamProfileModelType
    ]
    config: StreamConfigModel

    @classmethod
    def build(cls, sensor : Sensor, id : UUID):
        return cls(
            id = id,
            device_name = sensor.device.product_name,
            device_serial_number = sensor.device.serial_number,
            state = sensor.state,
            supported_profiles = [
                StreamProfileModel.build(profile) for profile in sensor.supported_stream_profiles()
            ],
            config = StreamConfigModel(
                entries = [
                    StreamConfigEntryModel(
                        profile = StreamProfileModel.build(profile),
                        stream = StreamModel(
                            id = CacheManager.cache(stream)
                            )
                        ) for profile, stream in sensor.config 
                ]
                )
        )