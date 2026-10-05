from contextlib import asynccontextmanager
import asyncio

# for debugging
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s\n",
    handlers=[RichHandler()]
)


# FastAPI
from fastapi import FastAPI
from .routers import (
    sensor,
    stream,
    metrics
    )


# utils
from .util.broadcast import BroadcastManager, BroadcastOptions
from .util.encoder import JPEGEncoder

# lifespan definition
@asynccontextmanager
async def lifespan(app : FastAPI):
    
    # initialization
    app.state.broadcast_manager = BroadcastManager(
        options=BroadcastOptions(),
        event_loop=asyncio.get_running_loop(),
        encoder=JPEGEncoder(quality=100) # TODO make quality env variable
        )
    
    yield
    
    # cleanup
    pass


# define app
app = FastAPI(
    lifespan=lifespan
    )


# Router definitions
app.include_router(sensor.router, prefix="/api")
app.include_router(stream.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")