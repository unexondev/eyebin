from comcam.core.sensor import Sensor, DeviceDesc, SensorOptions, SensorState
from comcam.stream import StreamProfile, VideoStreamProfile, StreamType, StreamFormat

from uuid import uuid1
from threading import Thread # for producers
import time

import numpy as np
from numpy.typing import NDArray

from typing import Callable


class MockSensor(Sensor):

    idx_next : int = 0

    def __init__(self, 
                 name : str, 
                 sensor_type : str, 
                 profile_to_producer : dict[StreamProfile, Callable[[StreamProfile], None]]
                 ):
        
        super().__init__(
            device_desc = DeviceDesc(
                product_name="[MOCK: %d] %s (%s)" % (self.idx_next, name, sensor_type),
                serial_number=str(uuid1())
                ),
            options=SensorOptions()
            )
        
        MockSensor.idx_next += 1

        self._profile_to_producer : dict[
            StreamProfile, Callable[[StreamProfile], None]
            ] = profile_to_producer.copy()
        
        self._producer_threads : dict[StreamProfile, Thread] = {}


    def __hash__(self):
        return hash((self.device))


    def supported_stream_profiles(self):
        return set(self._profile_to_producer.keys())
    

    def start(self, open_before=True):
        super().start(
            open_before=open_before
            ) # sets state as streaming
        for profile in self.config.profiles_iter():
            prod = self._profile_to_producer.get(profile, None)
            if prod is None:
                raise ValueError("Unsupported profile is given as config: %r" % profile)
            self._producer_threads[profile] = th_prod = Thread(
                target=prod, 
                args=(profile,), 
                daemon=True
                )
            th_prod.start()


    def close(self, stop_before=True):
        super().close(
            stop_before=stop_before
            )
        for th_prod in self._producer_threads.values():
            if th_prod.is_alive():
                th_prod.join()


class MockColorSensor(MockSensor):

    def __init__(self, 
                 name : str, 
                 profile_to_producer : dict[StreamProfile, Callable[[StreamProfile], None]]
                 ):
        super().__init__(
            name=name,
            sensor_type="Color",
            profile_to_producer=profile_to_producer
            )


class MockDepthSensor(MockSensor):

    def __init__(self, 
                 name : str, 
                 profile_to_producer : dict[StreamProfile, Callable[[StreamProfile], None]]
                 ):
        super().__init__(
            name=name,
            sensor_type="Depth",
            profile_to_producer=profile_to_producer
            )
        

class Mock_ColorTransition(MockColorSensor):

    def __init__(self):

        super().__init__(
            name="Color Transition",
            profile_to_producer = {
                profile: self._producer for profile in [
                    VideoStreamProfile(
                        width=1920,
                        height=1080,
                        stream_type=StreamType.COLOR,
                        format=StreamFormat.RGB8,
                        fps=60
                        ),    
                    VideoStreamProfile(
                        width=1920,
                        height=1080,
                        stream_type=StreamType.COLOR,
                        format=StreamFormat.RGB8,
                        fps=30
                        ),
                    VideoStreamProfile(
                        width=1280,
                        height=720,
                        stream_type=StreamType.COLOR,
                        format=StreamFormat.RGB8,
                        fps=30
                        ),
                    VideoStreamProfile(
                        width=1280,
                        height=720,
                        stream_type=StreamType.COLOR,
                        format=StreamFormat.RGB8,
                        fps=6
                        )
                ]  
            }
            )

        # for color transition effect
        self._rgb_states = {
            profile: (255, 0, 0) for profile in self._profile_to_producer.keys()
        }


    def _producer(self, profile : VideoStreamProfile):

        while self.state == SensorState.STREAMING:

            r, g, b = self._rgb_states[profile]

            data = np.full((profile.height, profile.width, 3), [r, g, b], dtype=np.uint8)

            # put data into the corresponding stream
            self.config.get_stream(profile).put(data)

            if r == 255 and g < 255:
                g += 1
            elif g == 255 and r > 0:
                r -= 1
            elif g == 255 and b < 255:
                b += 1

            elif b == 255 and g > 0:
                g -= 1
            elif b == 255 and r < 255:
                r += 1
            elif r == 255 and b > 0:
                b -= 1

            self._rgb_states[profile] = (r, g, b)

            period = (1 / profile.fps) # 1/60 second = 1 frame
            time.sleep(period) # sleep for fps simulation

        self._rgb_states[profile] = (255, 0, 0)


class Mock_LineFlow(MockDepthSensor):

    def __init__(self, step : int = 10, radius : int = 50):

        super().__init__(
            name="Line Flow",
            profile_to_producer = {
                profile: self._producer for profile in [
                    VideoStreamProfile(
                        width=1920,
                        height=1080,
                        stream_type=StreamType.DEPTH,
                        format=StreamFormat.GRAY8,
                        fps=60
                        ),    
                    VideoStreamProfile(
                        width=1920,
                        height=1080,
                        stream_type=StreamType.DEPTH,
                        format=StreamFormat.GRAY8,
                        fps=30
                        ),
                    VideoStreamProfile(
                        width=1280,
                        height=720,
                        stream_type=StreamType.DEPTH,
                        format=StreamFormat.GRAY8,
                        fps=30
                        ),
                    VideoStreamProfile(
                        width=1280,
                        height=720,
                        stream_type=StreamType.DEPTH,
                        format=StreamFormat.GRAY8,
                        fps=6
                        )
                ]  
            }
            )

        self._step = step

        self._radius = radius

        # for color transition effect
        self._point_states = {
            profile: (radius, radius) for profile in self._profile_to_producer.keys()
        }


    def _producer(self, profile : VideoStreamProfile):

        while self.state == SensorState.STREAMING:

            width, height = profile.width, profile.height
            radius = self._radius
            step = self._step
            x, y = self._point_states[profile]
            
            pts : set[tuple[int, int, int]] = set() # (x, y, value)

            for i in range(x - radius, x + radius + 1):
                # x - r -> x + r
                if i < 0 or i >= width:
                    continue
                delta_y = int((radius ** 2 - abs(i - x) ** 2) ** 0.5)
                for j in range(y - delta_y, y + delta_y + 1):
                    if j < 0 or j >= height:
                        continue
                    distance = ((j - y) ** 2 + (i - x) ** 2) ** 0.5
                    density = 1 - distance / radius
                    value = int(255 * density)
                    pts.add((i, j, value))

            data = np.zeros((height, width), dtype=np.uint8)

            for pt_x, pt_y, value in pts:
                data[pt_y, pt_x] = value

            # put data into the corresponding stream
            self.config.get_stream(profile).put(data)

            if x < width - 1 - radius:
                x += step
            elif y < height - 1 - radius:
                x, y = radius, y + radius
            else:
                # x,y = 255,255
                x, y = radius, radius

            self._point_states[profile] = (x, y)

            period = (1 / profile.fps) # 1/60 second = 1 frame
            time.sleep(period) # sleep for fps simulation

        self._point_states[profile] = (radius, radius)



MOCK_SENSORS : list[Sensor] = [
    Mock_ColorTransition(),
    Mock_LineFlow()
]