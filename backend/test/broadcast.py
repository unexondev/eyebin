import pytest

from ..util.broadcast import BroadcastManager, BroadcastOptions, Subscriber

from comcam.stream import Stream

import numpy as np
from numpy.typing import NDArray

import asyncio
import threading
import time


@pytest.fixture
def event_loop():

    # create an event loop for tests (simulating FastAPI's event loop)
    loop = asyncio.new_event_loop()

    # create a thread that is terminated automatically after tests are ended
    th_loop = threading.Thread(target=loop.run_forever, daemon=True)

    th_loop.start() # start thread (starts with loop.run_forever() call)

    yield loop # return loop

    # clean up
    
    async def cleanup():
        current = asyncio.current_task()

        tasks = [
            task
            for task in asyncio.all_tasks()
            if task is not current
        ]

        for task in tasks:
            task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

    future_cleanup = asyncio.run_coroutine_threadsafe(
        cleanup(),
        loop,
    )

    future_cleanup.result()

    loop.call_soon_threadsafe(loop.stop) # order loop to be stopped
    th_loop.join() # wait for previous stop operation to complete

    loop.close() # close the loop


def test_broadcast_semantically_consistent(
        event_loop : asyncio.AbstractEventLoop
        ):
    
    bc_mgr = BroadcastManager(
        event_loop=event_loop,
        options = BroadcastOptions()
        )

    stream = Stream()

    with pytest.raises(RuntimeError):
        bc_mgr.subscribers(stream)
    
    bc_mgr.mount(stream)

    assert bc_mgr.mounted_streams() == { stream }

    assert not bc_mgr.subscribers(stream)

    sub = bc_mgr.subscribe(stream)

    assert bc_mgr.subscribers(stream) == { sub }

    sub.unsubscribe()

    assert not bc_mgr.subscribers(stream)

    bc_mgr.subscribe(stream)

    bc_mgr.unmount(stream)

    with pytest.raises(RuntimeError):
        bc_mgr.subscribers(stream)

    assert not bc_mgr.mounted_streams()


def test_broadcast_data_arrival(
        event_loop : asyncio.AbstractEventLoop
        ):

    bc_mgr = BroadcastManager(
        event_loop=event_loop,
        options = BroadcastOptions()
        )

    stream_0, stream_1 = Stream(), Stream()

    bc_mgr.mount(stream_0)
    bc_mgr.mount(stream_1)
    # mounted: { stream_0, stream_1 }

    # add subscribers
    sub_0_stream_0 = bc_mgr.subscribe(stream_0)
    sub_1_stream_0 = bc_mgr.subscribe(stream_0)
    sub_0_stream_1 = bc_mgr.subscribe(stream_1)
    sub_1_stream_1 = bc_mgr.subscribe(stream_1)

    in_stream_0 = np.asarray(
        [0xA, 0xB, 0xC],
        dtype=np.ubyte
        )
    in_stream_1 = np.asarray(
        [0xD, 0xE, 0xF], 
        dtype=np.ubyte
        )

    stream_0.put(in_stream_0)
    stream_1.put(in_stream_1)

    async def wait_from_all():

        return (
            await sub_0_stream_0.wait(),
            await sub_1_stream_0.wait(),
            await sub_0_stream_1.wait(),
            await sub_1_stream_1.wait(),
            )

    future = asyncio.run_coroutine_threadsafe(
        wait_from_all(),
        event_loop
        ) # will instanly get their distributed data

    results : tuple[NDArray] = future.result()

    assert (
        np.array_equal(results[0], in_stream_0) and
        np.array_equal(results[1], in_stream_0) and
        np.array_equal(results[2], in_stream_1) and
        np.array_equal(results[3], in_stream_1)
        )

    future = asyncio.run_coroutine_threadsafe(
        wait_from_all(),
        event_loop
        ) # will be waiting for data

    in_stream_0 = np.asarray(
        [0x1A, 0x1B, 0x1C],
        dtype=np.ubyte
        )
    in_stream_1 = np.asarray(
        [0x1D, 0x1E, 0x1F], 
        dtype=np.ubyte
        )

    stream_0.put(in_stream_0)
    stream_1.put(in_stream_1)

    results : tuple[NDArray] = future.result()

    assert (
        np.array_equal(results[0], in_stream_0) and
        np.array_equal(results[1], in_stream_0) and
        np.array_equal(results[2], in_stream_1) and
        np.array_equal(results[3], in_stream_1)
        )


def test_data_arrival_subscriber_leaves(
        event_loop : asyncio.AbstractEventLoop
        ):

    bc_mgr = BroadcastManager(
        event_loop=event_loop,
        options = BroadcastOptions()
        )

    stream = Stream()

    bc_mgr.mount(stream)

    # first, get data from multiple subscribers once

    sub_dead = bc_mgr.subscribe(stream)
    sub_alive = bc_mgr.subscribe(stream)

    async def wait_from(subscriber : Subscriber):
        return await subscriber.wait()

    async def wait_from_all():
        return (
            await wait_from(sub_dead),
            await wait_from(sub_alive)
            )

    future = asyncio.run_coroutine_threadsafe(
        wait_from_all(), 
        event_loop
        )

    in_before_leave = np.asarray([1, 2, 3], dtype=np.ubyte)

    stream.put(in_before_leave)

    results : tuple[NDArray] = future.result()

    assert (
        np.array_equal(results[0], in_before_leave) and
        np.array_equal(results[1], in_before_leave)
        )

    # now get data while one of the subscribers is left

    in_after_leave = np.asarray([4, 5, 6], dtype=np.ubyte)

    sub_dead.unsubscribe()

    assert bc_mgr.subscribers(stream) == { sub_alive }

    bc_mgr.wait_subscribers_synced(stream)

    stream.put(in_after_leave)

    future = asyncio.run_coroutine_threadsafe(
        wait_from(sub_dead), 
        event_loop
        )

    with pytest.raises(TimeoutError):
        future.result(0.5) # wait 500ms

    future.cancel()