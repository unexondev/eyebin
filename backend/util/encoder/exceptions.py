class EncoderError(Exception):
    "Generic class for encoder-related exceptions."

class UnsupportedFormatError(EncoderError):
    """
    Raised when the given format is not encodable by encoder.
    """