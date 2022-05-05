import io
import time
from datetime import datetime, timedelta

from smbus2 import SMBus
from imusensor.MPU9250 import MPU9250
# from imusensor.filters import kalman
from skyfield.api import load, wgs84
from serial import Serial, SerialException
import pynmea2

from sattrack import SAT, GPS

# Generate satellite ephemeris
iss = SAT(51085)
satellite = iss.get_tle()

# Get observer position
observer = GPS()
observer.update_pos()
print("Observer position:", observer.get_pos())
time.sleep(1)

# main program loop to update device orientation
while True:
    # Use Skyfield to get difference between satellite and observer position at this moment
    alt, az, distance = observer.calc_diff(satellite)

    if alt.degrees > 0:
        print('The ISS is above the horizon')

    print('-------------Look Angles and Distance to ISS----------------')
    print('Altitude: {0} ; Azimuth: {1} ; Distance {2:.1f}km'.format(round(alt.degrees, 2), round(az.degrees, 2), round(distance.km, 2)))
    print('')