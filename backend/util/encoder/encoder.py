from comcam.stream.profile import StreamFormat

from numpy.typing import NDArray

class Encoder:
    """
    Common interface for all encoder implementations.
    """

    def encodable(self, format: StreamFormat):
        raise NotImplementedError()

    def encode(self, data : NDArray, format : StreamFormat):
        raise NotImplementedError()