from dataclasses import dataclass, replace
from enum import Enum
from threading import Lock # for thread-safe

from eyebin.stream import Stream, StreamProfile


@dataclass
class SensorOptions:
    pass


@dataclass(frozen=True)
class SensorConfig:
    stream : Stream | None = None
    stream_profiles : frozenset[StreamProfile] = frozenset()


class SensorState(Enum):
    CLOSED = 0,
    OPENED = 1,
    STREAMING = 2,
    ERRORED = 3


class Sensor:
    """
    Abstraction class for all types of sensors.

    This abstraction is responsible for physical implementation of sensors,
    higher level implementations are expected to depend on context. 

    Assumptions:
        - Sensors can physically have 3 states:
            - `Closed` state,
            - `Opened` state,
            - `Streaming` (or `Started`) state.

    The derived classes must implement the functions properly
    to ensure that all assumptions are satisfied.
    """
    def __init__(self, options : SensorOptions, config : SensorConfig = None):

        # initialize state
        self._state = SensorState.CLOSED

        # save the config
        self.opts = options

        # save the config
        self._conf = config if config is not None else SensorConfig()

        # create mutex
        self._lock = Lock()


    @property
    def config(self):
        with self._lock:
            return replace(self._conf)


    @property
    def state(self):
        with self._lock:
            return self._state


    """
    Sensor Management APIs
    """

    def configure(self, config : SensorConfig):
        """
        Configure the sensor so it can then stream on
        given stream configuration after the next time it's opened.
        
        Args:
            config: A `SensorConfig` object.
        """
        with self._lock:

            if self._state != SensorState.CLOSED:
                raise RuntimeError("Sensor must be closed to configure.")

            self._conf = config


    def open(self):
        """
        Open the sensor physically.

        Raises:
            SensorOpenError: If sensor couldn't be opened successfully.
        """
        with self._lock:
            self._state = SensorState.OPENED


    def close(self):
        """
        Close the sensor physically.

        Raises:
            SensorCloseError: If sensor couldn't be closed successfully.
        """
        with self._lock:
            self._state = SensorState.CLOSED


    def start(self):
        """
        Start the sensor (start streaming) physically.

        Raises:
            SensorStartError: If sensor couldn't be started successfully.
        """
        with self._lock:
            self._state = SensorState.STREAMING


    def stop(self):
        """
        Stop the sensor (end streaming) physically.

        Raises:
            SensorStopError: If sensor couldn't be stopped successfully.
        """
        with self._lock:
            self._state = SensorState.OPENED


    """
    Sensor Information Query APIs
    """

    def is_healthy(self):
        """
        Check if sensor is healthy under constraints passed in `options`.

        Raises:
            SensorInfoError: If an error occurs while gathering the sensor information.
        """
        raise NotImplementedError()


    """
    Private Functions
    """

    def _fail(self):
        self._state = SensorState.ERRORED
        