from __future__ import annotations
from dataclasses import dataclass

from pyrealsense2 import stream as StreamType
from pyrealsense2 import format as StreamFormat
from pyrealsense2 import stream_profile, video_stream_profile


@dataclass
class StreamProfile:

    stream_type : StreamType
    format : StreamFormat

    def matches(self, other : stream_profile | StreamProfile):
        raise NotImplementedError()


@dataclass
class VideoStreamProfile(StreamProfile):

    width : int
    height : int
    fps : int


    def matches(self, other : video_stream_profile | VideoStreamProfile) -> bool:

        if isinstance(other, video_stream_profile):
            return self.stream_type == other.stream_type() and \
                self.format == other.format() and \
                self.width == other.width() and \
                self.height == other.height() and \
                self.fps == other.fps()

        if isinstance(other, VideoStreamProfile):
            return self == other

        return False


    def __hash__(self):
        return hash((
            self.width, self.height, self.fps,
            self.stream_type, self.format
            ))