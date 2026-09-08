from eyebin.stream import Stream
from eyebin.stream.profile import VideoStreamProfile, StreamType, StreamFormat
from eyebin.util.resolver import SPResolver

import numpy
import cv2


# create stream profiles
sp_depth = VideoStreamProfile(StreamType.depth, StreamFormat.z16, 1280, 720, 30)
sp_color = VideoStreamProfile(StreamType.color, StreamFormat.rgba8, 1280, 720, 30)

# collect sensors
# initialize a sensor resolver
resolver = SPResolver()

sensor_depth = resolver.resolve(sp_depth)
sensor_color = resolver.resolve(sp_color)

stream_depth = Stream()
stream_color = Stream()

sensor_depth.configure(stream=stream_depth, stream_profiles={sp_depth})
sensor_color.configure(stream=stream_color, stream_profiles={sp_color})

sensor_depth.start()
sensor_color.start()

stream_depth.wait_oldest(...)
stream_color.wait_oldest(...)

img = None

# stream is consumable while it's active
while stream.active():

    frameset = stream.get_data()

    if frameset is None:
        continue

    fcolor = frameset.get_color_frame() 

    img = numpy.asanyarray(fcolor.get_data())
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    

    cv2.imshow("COLOR", img)

    if cv2.waitKey(1) == 27:   # ESC
        break

# stop stream
stream.stop()

# close all windows
cv2.destroyAllWindows()