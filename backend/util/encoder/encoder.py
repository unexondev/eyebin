from comcam.stream.profile import StreamFormat

from numpy.typing import NDArray

class Encoder:
    """
    Common interface for all encoder implementations.
    """

    def encodable_formats(self) -> set[StreamFormat]:
        raise NotImplementedError()

    def encodable(self, format: StreamFormat) -> bool:
        return format in self.encodable_formats()

    def encode(self, data : NDArray, format : StreamFormat) -> bytes:
        raise NotImplementedError()