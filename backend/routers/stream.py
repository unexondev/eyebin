from ..models.response import StatusResponse
from ..models.stream import StartStreamRequest, StopStreamRequest, StreamModel

from ..util.cache import CacheManager
from ..util.broadcast import BroadcastManager
from ..util.state import broadcast_manager_from_request, broadcast_manager_from_websocket


# import Comcam
from comcam.core.sensor import Sensor, SensorState
from comcam.core.sensor.exceptions import *
from comcam.stream import Stream, StreamFormat


# import FastAPI
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends

# For testing & debugging
import os
import logging
from rich.pretty import pretty_repr

logger = logging.getLogger(__name__)

# MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# if MOCK_MODE:
#    from ..mock.stream import *


# FastAPI definitions
router = APIRouter(prefix="/stream")

@router.post("/start", response_model=StatusResponse)
def start_stream(params : StartStreamRequest, 
                 bc_manager : BroadcastManager = Depends(broadcast_manager_from_request)
                 ):

    logger.debug("Start stream request received:\n%s", pretty_repr(params))
    
    if not params.profiles:
        return HTTPException(
            status_code=409,
            detail="No profiles are provided. Please select stream profiles first."
            )

    sensor : Sensor | None = CacheManager.get(params.sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Couldn't find sensor, please restart the session."
            )

    if sensor.state != SensorState.CLOSED:
        raise HTTPException(
            status_code=409,
            detail="Sensor is not closed."
            )

    # Now we know that sensor is closed, try to open and start it.

    # check all formats are encodable
    if params.encode:
        encoder = bc_manager.encoder
        if encoder is None:
            raise HTTPException(
                status_code=409,
                detail="Couldn't find any encoder, encoding feature might be disabled."
                )
        for profile in params.profiles:
            if not encoder.encodable(profile.format):
                raise HTTPException(
                    status_code=409,
                    detail="Format is not encodable: %s" % profile.format.name
                    )

    # clear last configuration
    sensor.config.clear()

    # add requested configuration
    for profile in params.profiles:

        profile = profile.transform()
        stream = Stream()

        sensor.config.use(
            stream_profile=profile,
            stream=stream
            )

        bc_manager.mount(
            stream=stream,
            format=profile.format if params.encode else None
            ) # mount to broadcast manager
        

    try:
        sensor.start()
    except SensorOpenError:
        logger.exception("Failed to open sensor.")
        raise HTTPException(
            status_code=500, 
            detail="Couldn't open sensor. Traceback is logged to the server."
            )
    except SensorStartError:
        logger.exception("Failed to start sensor.")
        raise HTTPException(
            status_code=500, 
            detail="Couldn't start sensor. Traceback is logged to the server."
            )

    logger.debug("Stream has been started.")

    return StatusResponse(
        message="Sensor has been started successfully."
        ) # OK


@router.post("/stop", response_model=StatusResponse)
def stop_stream(params : StopStreamRequest,
                bc_manager : BroadcastManager = Depends(broadcast_manager_from_request)
                ):

    logger.debug("Stop stream request received:\n%s", pretty_repr(params))

    if not params.profiles:
        return HTTPException(
            status_code=409,
            detail="No profiles are provided. Please select stream profiles first."
            )

    sensor : Sensor | None = CacheManager.get(params.sensor_id)

    if sensor is None:
        raise HTTPException(
            status_code=404,
            detail="Couldn't find sensor, please restart the session."
            )

    if sensor.state != SensorState.STREAMING:
        raise HTTPException(
            status_code=409,
            detail="Sensor is not streaming."
            )

    # Now we know that sensor is streaming

    # unmount streams from broadcast
    for profile, stream in sensor.config:
        bc_manager.unmount(stream)

    # try to close sensor
    try:
        sensor.close()
    except SensorStopError:
        logger.exception("Failed to stop sensor.")
        raise HTTPException(
            status_code=500, 
            detail="Couldn't stop sensor. Traceback is logged to the server."
            )
    except SensorCloseError:
        logger.exception("Failed to close sensor.")
        raise HTTPException(
            status_code=500, 
            detail="Couldn't close sensor. Traceback is logged to the server."
            )

    logger.debug("Stream has been stopped.")

    return StatusResponse(
        message="Stream has been ended successfully."
        ) # OK


@router.get("/encodable-formats", response_model=set[StreamFormat])
def get_encodable_formats(bc_manager : BroadcastManager = Depends(broadcast_manager_from_request)):
    return bc_manager.encoder.encodable_formats()


# Websocket definitions

@router.websocket("/consume")
async def ws_stream(socket : WebSocket, 
                    stream : StreamModel = Depends(StreamModel),
                    bc_manager : BroadcastManager = Depends(broadcast_manager_from_websocket)
                    ):

    # accept connection
    await socket.accept()

    logger.debug(
        "Consumer websocket connection established from %s:%s",
        socket.client.host,
        socket.client.port
        )

    # get stream
    stream : Stream = CacheManager.get(stream.id)
    
    if stream is None:
        try:
            await socket.close(
                reason="Couldn't find stream, please restart the session."
                )
        except (RuntimeError, WebSocketDisconnect):
            pass
        return

    subscriber = bc_manager.subscribe(stream)
            
    while True:
    
        bs = await subscriber.wait(1000) # wait for a second for data arrival

        if bs is None:
            # producer (sensor) is either
            # unstable, closed or errored
            bc_manager.unmount(stream) # unmount it
            try:
                await socket.close(
                    reason="Stream seems to be unmounted, please restart the stream."
                    )
            except (RuntimeError, WebSocketDisconnect):
                pass
            return

        try:
            await socket.send_bytes(bs) # send bytes to the socket

        except (RuntimeError, WebSocketDisconnect):
            # socket is probably disconnected
            subscriber.unsubscribe()
            return