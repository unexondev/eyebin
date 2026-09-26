from __future__ import annotations

from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from comcam.stream import StreamProfile, VideoStreamProfile, StreamType, StreamFormat


class StreamProfileModel(BaseModel):
    type: str
    stream_type : StreamType
    format : StreamFormat
    fps : int

    @classmethod
    def build(cls, stream_profile : StreamProfile) -> StreamProfileModel:

        if isinstance(stream_profile, VideoStreamProfile):
            return VideoStreamProfileModel.build(stream_profile)

        raise NotImplementedError()


class VideoStreamProfileModel(StreamProfileModel):
    type: Literal["video"] = "video"
    width: int
    height: int

    @classmethod
    def build(cls, video_stream_profile : VideoStreamProfile) -> VideoStreamProfileModel:

        return cls(
            stream_type = video_stream_profile.stream_type,
            format = video_stream_profile.format,
            fps = video_stream_profile.fps,
            width = video_stream_profile.width,
            height = video_stream_profile.height
            )

    def transform(self) -> VideoStreamProfile:
        return VideoStreamProfile(
            stream_type=self.stream_type,
            format=self.format,
            fps=self.fps,
            width=self.width,
            height=self.height
        )


StreamProfileModelType = Annotated[
    Union[
        VideoStreamProfileModel,
        # MotionStreamProfileResponse,
        # ...
    ],
    Field(discriminator="type"),
]


class StreamModel(BaseModel):
    id : UUID = Field(default_factory=uuid4)


class StreamConfigEntryModel(BaseModel):
    profile : StreamProfileModelType
    stream : StreamModel


class StreamConfigModel(BaseModel):
    entries: list[StreamConfigEntryModel]


class StartStreamRequest(BaseModel):
    sensor_id : UUID
    profiles: list[StreamProfileModelType]