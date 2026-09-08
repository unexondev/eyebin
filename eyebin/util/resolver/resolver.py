from dataclasses import dataclass

from eyebin.stream.profile import StreamProfile
from eyebin.core.sensor import Sensor

from .descs import DESCS, PVID

import usb.core # for enumerating devices


class SPResolver: # StreamProfileResolver
    """
    Abstraction class for dependency resolution
    from stream profiles to all types of sensors.
    """

    def __init__(self):
        pass

    def resolve(self,
                stream_profile : StreamProfile,
                pvid : PVID | None = None
                ) -> Sensor | None:
        """
        Resolve the stream profile to a sensor that is capable of streaming on given profile.

        Args:
            stream_profile: A `StreamProfile` object to check that is streamable while discovering sensors.
            pvid (optional): A `PVID` object describes which device should be considered while discovering sensors.
        
        Returns:
            A `Sensor` object wraps the sensor that capable of streaming on given profile, `None` otherwise.
        """

        devs_iter = usb.core.find(find_all=True)
        for device in devs_iter:

            pvid_dev = PVID(
                product_id=device.idProduct,
                vendor_id=device.idVendor
                )

            if (pvid is not None and
                pvid != pvid_dev):
                continue
            
            if pvid_dev not in DESCS:
                continue
            
            sensor = DESCS[pvid_dev](
                stream_profile=stream_profile,
                pvid=pvid # pass pvid
            ) # try to resolve sensor

            if sensor is not None:
                return sensor

        return None # no sensor found capable to stream on given profile