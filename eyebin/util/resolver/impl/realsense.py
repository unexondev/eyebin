from eyebin.core.sensor.impl.realsense import RSSensor
from eyebin.stream.profile import StreamProfile

from ..descs import PVID

from pyrealsense2 import context as rs_context
from pyrealsense2 import camera_info as rs_camera_info


def resolve(stream_profile : StreamProfile,
            pvid : PVID | None = None
            ) -> RSSensor | None:

    ctx = rs_context() # context is required

    devices = ctx.query_devices()
    for device in devices:

        if pvid is not None:

            pid_str = device.get_info(rs_camera_info.product_id)
            pid = int(pid_str, base=16)

            if pid != pvid.product_id:
                continue

        for sensor in device.sensors:

            rs_prfs_stream = sensor.get_stream_profiles()
            for rs_prf_stream in rs_prfs_stream:

                if stream_profile.matches(rs_prf_stream):
                    # create Sensor (RSSensor) instance
                    return RSSensor(
                        sensor=sensor
                        )
                
    return None