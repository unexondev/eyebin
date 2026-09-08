from dataclasses import dataclass
from collections import defaultdict

from eyebin.stream import Stream, StreamProfile
from eyebin.core.sensor import Sensor, SensorConfig, SensorState
from eyebin.core.sensor.exceptions import *
from eyebin.util.resolver import SPResolver
from eyebin.util.resolver import PVID

import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineOptions:

    max_len_captured_data_buffer : int
    """
    For scalibility we keep the captured RGB/depth data inside a buffer, then process them.
    Since this buffer may cause a memory overhead, we allow you to set its maximum size.
    If maximum length is exceeded, capturing process will be suspended until any of older data is dequeued.
    """

        
class Pipeline:
    """
    The main pipeline for EyeBin project that organizes tasks.
    """

    def __init__(self,
                 options : PipelineOptions
                 ):
        
        self.opts = options
        self.prf_to_sensor : dict[StreamProfile, Sensor] = {}
        self.resolver = SPResolver()


    def add_config(self,
                  profiles : set[StreamProfile],
                  pvid_device : PVID | None = None
                  ):

        prf_to_ss = self.prf_to_sensor

        prf_to_ss_new : dict[StreamProfile, Sensor] = {}

        for profile in profiles:

            if profile in prf_to_ss:
                # remove configuration if exists
                self.remove_config(profile)

            sensor = self.resolver.resolve(
                stream_profile=profile,
                pvid=pvid_device
                )

            if sensor is None:
                raise RuntimeError(
                    "Could not resolve a sensor for stream profile=%r and PVID=%r." % (profile, pvid_device)
                    )

            prf_to_ss_new[profile] = sensor # do the mapping

        sensor_profiles : defaultdict[Sensor, set[StreamProfile]] = defaultdict(set)
        for profile, sensor in prf_to_ss_new.items():

            sensor_profiles[sensor].add(profile)

        for sensor, _profiles in sensor_profiles.items():

            sensor.configure(SensorConfig(
                stream=Stream(),
                stream_profiles=frozenset(_profiles)
            ))

        prf_to_ss.update(prf_to_ss_new) # update the mapping


    def remove_config(self, profile : StreamProfile):
        sensor = self.prf_to_sensor.pop(profile)


    def start(self):

        if not self.prf_to_sensor:
            raise RuntimeError(
                "Sensor not found, please configure pipeline before starting it."
                )

        # get sensors only 'once'
        sensors = sensors = list(dict.fromkeys(self.prf_to_sensor.values()))

        for sensor in sensors:

            # if open, close it
            if sensor.state == SensorState.OPENED:
                sensor.close()

            if sensor.state != SensorState.CLOSED:
                raise RuntimeError("Sensor is already streaming.")

            # open the sensor
            sensor.open()

            # start the sensor
            sensor.start()