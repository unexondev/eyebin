from __future__ import annotations

from dataclasses import dataclass, field
from threading import Thread, Condition, Event

from typing import Callable
from asyncio import Queue, AbstractEventLoop, QueueFull, wait_for

from comcam.stream import Stream


@dataclass(frozen=True)
class BroadcastOptions:
    wait_stream_duration_ms : int = 100 # 100 milliseconds by default


@dataclass(frozen=True)
class WorkerEvents:
    subs_synced : Event = field(default_factory=Event)


@dataclass(frozen=True)
class WorkerContext:
    thread : Thread
    events : WorkerEvents = field(default_factory=WorkerEvents)


class Subscriber:

    def __init__(self, on_unsubscribe : Callable[[], None] | None = None):
        self.queue = Queue()    
        self._unsub_cb = on_unsubscribe

    async def wait(self, timeout_ms : float | None = None):

        if timeout_ms is None:
            return await self.queue.get()

        try:
            return await wait_for(self.queue.get(), timeout_ms / 1000)
        
        except TimeoutError:
            return None

    def unsubscribe(self):
        unsub_cb = self._unsub_cb
        if unsub_cb:
            unsub_cb()

    def set_on_unsubscribe(self, on_unsubscribe : Callable[[], None]):
        self._unsub_cb = on_unsubscribe

    def __enter__(self) -> Subscriber:
        return self

    def __exit__(self, exc_type, exc, tb):
        self.unsubscribe()       


class BroadcastManager:
    """
    A multithread data distribution utility for
    broadcasting data to multiple receivers from streams.
    """

    def __init__(self,
                 options : BroadcastOptions, 
                 event_loop : AbstractEventLoop | None = None
                 ):

        self._opts : BroadcastOptions = options

        self._loop : AbstractEventLoop | None = event_loop

        self._mntd : set[Stream] = set()

        self._subs : dict[Stream, set[Subscriber]] = {}

        self._worker_ctxs : dict[Stream, WorkerContext] = {}

        self._cond_sub = Condition()


    def init_event_loop(self, event_loop : AbstractEventLoop):

        loop_cur = self._loop

        if loop_cur is not None and event_loop != loop_cur:
            raise RuntimeError("Event loop changed after initialized.")

        self._loop = event_loop


    def mounted_streams(self) -> set[Stream]:
        
        with self._cond_sub:
            return self._mntd.copy()


    def subscribers(self, stream : Stream) -> set[Subscriber]:

        with self._cond_sub:
            return self._subscribers(stream)


    def mount(self, stream : Stream) -> None:

        th_worker = Thread(
            target=self._worker, 
            args=(stream,), 
            daemon=True
            )

        ctx_worker = WorkerContext(th_worker)

        with self._cond_sub:

            self._mntd.add(stream)

            self._subs[stream] = set()

            self._worker_ctxs[stream] = ctx_worker

        th_worker.start()


    def unmount(self, stream : Stream) -> None:

        with self._cond_sub:
            self._unmount(stream)


    def unmount_all(self) -> None:

        with self._cond_sub:
            for stream in self._mntd:
                self._unmount(stream)


    def subscribe(self, stream : Stream) -> Subscriber:

        with self._cond_sub:

            subs = self._subscribers(stream)

            sub = Subscriber()

            def _on_unsubscribe(subs : set[Subscriber] = subs,
                               sub : Subscriber = sub
                               ):
                with self._cond_sub:
                    subs.discard(sub)

            sub.set_on_unsubscribe(_on_unsubscribe)

            subs.add(sub)

            self._cond_sub.notify()

            return sub


    def wait_subscribers_synced(self, stream : Stream):

        with self._cond_sub:

            self._sanity_check_mounted(stream)

            ctx_worker = self._worker_ctxs[stream]

            event = ctx_worker.events.subs_synced

        event.clear()

        event.wait()
    

    def _sanity_check_mounted(self, stream : Stream):
        """
        Must be called inside `with self._cond_sub:` block.
        """

        if stream not in self._mntd:
            raise RuntimeError("Stream is not mounted: %r" % stream)


    def _subscribers(self, stream : Stream):
        """
        Must be called inside `with self._cond_sub:` block.
        """
        
        self._sanity_check_mounted(stream)

        return self._subs[stream]


    def _unmount(self, stream : Stream):
        """
        Must be called inside `with self._cond_sub:` block.
        """

        # delete from subscriber map if exists
        self._subs.pop(stream, None)

        # delete from mounted streams list if exists
        self._mntd.discard(stream)

        # delete from worker map if exists
        self._worker_ctxs.pop(stream, None)

        # worker will stop automatically since we
        # removed the stream from mounted stream list
        
        return
    

    def _worker(self, stream : Stream):

        opts = self._opts

        with self._cond_sub:
            events = self._worker_ctxs[stream].events

        while True:

            with self._cond_sub:

                while True:

                    if stream not in self._mntd: # unmounted
                        return self._unmount(stream)

                    if self._subs[stream]: # got a subscriber
                        break

                    # wait while there is no subscribers
                    self._cond_sub.wait()

                events.subs_synced.set() # signal subscribers are about to synced

                subs = self._subs[stream].copy()

            # now we safely had subs, let's send them data 

            data = stream.wait(opts.wait_stream_duration_ms)

            if data is None:
                continue

            for sub in subs:

                self._loop.call_soon_threadsafe(
                    self._try_put_nowait, 
                    sub.queue, 
                    data
                    )


    @staticmethod
    def _try_put_nowait(_queue : Queue, _item):
        try:
            _queue.put_nowait(_item)
        except QueueFull:
            pass


def _now_as_milliseconds() -> int:
    from time import monotonic_ns
    return monotonic_ns() // 1_000_000