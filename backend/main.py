from contextlib import asynccontextmanager
import asyncio

# for debugging
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler()]
)


# FastAPI
from fastapi import FastAPI
from .routers import (
    sensor,
    stream
    )


# Broadcast Manager
from .util.broadcast import BroadcastManager, BroadcastOptions
@asynccontextmanager
async def lifespan(app : FastAPI):
    
    # initialization
    app.state.broadcast_manager = BroadcastManager(
        options=BroadcastOptions(),
        event_loop=asyncio.get_running_loop()
        )
    
    yield
    
    # cleanup
    pass


app = FastAPI(lifespan=lifespan)


# Router definitions
app.include_router(sensor.router, prefix="/api")
app.include_router(stream.router, prefix="/api")