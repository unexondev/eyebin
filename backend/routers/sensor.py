from ..models.sensor import SensorModel
from ..util.cache import CacheManager

# import FastAPI
from fastapi import APIRouter

# import Comcam
from comcam.util.resolver import SensorResolver
from comcam.stream import VideoStreamProfile


# For testing & debugging
import os

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

if MOCK_MODE:
    from ..mock.sensor import *

import logging
from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)


# FastAPI definitions

router = APIRouter(prefix="/sensor")

@router.get("/fetch-all", response_model=list[SensorModel])
def fetch_sensors():

    logger.debug("Fetch all sensors request received.")

    sensor_responses = []

    for sensor in (SensorResolver.resolve_all() if not MOCK_MODE else MOCK_SENSORS):

        id_cached = CacheManager.cache(sensor)

        sensor_responses.append(
            SensorModel.build(
                sensor=sensor,
                id=id_cached
                )
            )

    return sensor_responses