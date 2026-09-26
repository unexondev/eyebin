from comcam.core.sensor import Sensor, DeviceDesc, SensorOptions
from comcam.stream import StreamProfile, VideoStreamProfile, StreamType, StreamFormat


class MockSensor(Sensor):

    def __init__(self, device_desc, profiles : set[StreamProfile]):
        super().__init__(device_desc, SensorOptions())
        self._profiles = profiles

    def __hash__(self):
        return hash((self.device))

    def supported_stream_profiles(self):
        return self._profiles


MOCK_SENSORS : list[Sensor] = [

    MockSensor(
        device_desc=DeviceDesc(
            "MOCK_0 - Color",
            "0000-0000-0001"
        ),
        profiles={
            VideoStreamProfile(
                width=1920,
                height=1080,
                fps=60,
                stream_type=StreamType.COLOR,
                format=StreamFormat.RGB8
            )
        }
    ),

    MockSensor(
        device_desc=DeviceDesc(
            "MOCK_0 - Depth",
            "0000-0000-0001"
        ),
        profiles={
            VideoStreamProfile(
                width=1920,
                height=1080,
                fps=60,
                stream_type=StreamType.DEPTH,
                format=StreamFormat.DEPTH16
            )
        }
    ),

    MockSensor(
        device_desc=DeviceDesc(
            "MOCK_1 - Color",
            "0000-0000-0002"
        ),
        profiles={
            VideoStreamProfile(
                width=1920,
                height=1080,
                fps=60,
                stream_type=StreamType.COLOR,
                format=StreamFormat.RGB8
            )
        }
    ),

    MockSensor(
        device_desc=DeviceDesc(
            "MOCK_1 - Depth",
            "0000-0000-0002"
        ),
        profiles={
            VideoStreamProfile(
                width=1920,
                height=1080,
                fps=60,
                stream_type=StreamType.DEPTH,
                format=StreamFormat.DEPTH16
            )
        }
    ),

    MockSensor(
        device_desc=DeviceDesc(
            "MOCK_2 - Color",
            "0000-0000-0002"
        ),
        profiles={
            VideoStreamProfile(
                width=800,
                height=600,
                fps=60,
                stream_type=StreamType.COLOR,
                format=StreamFormat.RGBA8
            )
        }
    ),

]