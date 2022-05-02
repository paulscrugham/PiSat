import io
import time
from datetime import datetime, timedelta

from smbus2 import SMBus
from imusensor.MPU9250 import MPU9250
# from imusensor.filters import kalman
from skyfield.api import load, wgs84
from serial import Serial, SerialException
import pynmea2


class IMU:
	"""
	Wrapper for the MPU9250. Uses the imusensor and smbus2 libraries to
	interface with the hardware. 
	Receives data over I2C.
	"""
	def __init__(self, address=0x68, bus=1):
		self.bus = SMBus(bus)
		self.address = address
		self.imu = MPU9250.MPU9250(self.bus, self.address)
		print("Starting up MPU9250")
		self.imu.begin()

	def calibrate(self, gyro=True, accel=True, file_path=None):
		"""Calibrates the gyro and/or accelerometer."""
		if gyro:
			print("Calibrating MPU9250 gyroscope")
			self.imu.caliberateGyro()
		if accel:
			print("Calibrating MPU9250 accelerometer")
			self.imu.caliberateAccelerometer()
		if file_path:
			print("Calibrating MPU9250 from file")
			self.imu.loadCalibDataFromFile(file_path)

	def read_no_filter(self):
		"""Reads estimated roll, pitch, and yaw from the IMU. No filter applied."""
		self.imu.readSensor()
		self.imu.computeOrientation()
		return (self.imu.roll, self.imu.pitch, self.imu.yaw)

	def get_address(self):
		return self.address


class GPS:
	"""
	Wrapper for the ublox CO99-F9P board.
	Uses the serial library to read device data.
	Uses the pynmea2 library to parse nmea sentences.
	Receives data over UART.
	"""
	def __init__(self, address="/dev/ttyACM0", baud=9600):
		self.address = address
		self.baud = baud
		self.ser = Serial(self.address, self.baud, timeout=5.0)  # Get raw byte data from serial port
		self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser))  # convert to string type
		self.position = {}
		self.time_scale = load.timescale()

	def _read_line(self):
		"""
		Reads a line from the GPS at serial port ttyACM0 and attempts to parse it using pynmea2.
		Based on the pySerial example from the pynmea2 source code: 
		https://github.com/Knio/pynmea2#pyserial-device-example.
		Returns a pynmea2 object.
		"""
		try:
			line = self.sio.readline()
			msg = pynmea2.parse(line)
			return msg
		except SerialException as e:
			print('Device error: {}'.format(e))
		except pynmea2.ParseError as e:
			print('Parse error: {}'.format(e))
	
	def update_pos(self):
		"""
		Returns a Skyfield object representing the position of the observer.
		"""
		# get first GGA message to use as current location
		self.position = {}
		while not self.position:
			nmea = self._read_line()
			# check for GGA type (Global positioning system fix data)
			if nmea.identifier()[2:5] == 'GGA':
				lat = float(nmea.lat) / 100
				if nmea.lat_dir == 'S':
					lat = -lat
				lon = float(nmea.lon) / 100
				if nmea.lon_dir == 'W':
					lon = -lon
				alt = nmea.altitude
				# create wgs84 object
				self.position = wgs84.latlon(lat, lon, alt)

	def get_pos(self):
		"""Returns the last received position. Use update_pos() to update the coordinates."""
		return self.position

	def calc_diff(self, satellite):
		"""
		Uses the Skyfield library to perform vector subtraction of the satellite and observer positions.
		"""
		difference = satellite - self.position
		t = self.time_scale.now()
		topocentric = difference.at(t)
		return topocentric.altaz()


class SAT:
	"""
	Wrapper for the Skyfield library to get satellite ephemeris.
	Requests TLEs from Celestrak via the Skyfield library.
	"""
	# TODO: add timestamp for when TLE was retrieved as class member
	def __init__(self, catnr):
		self.catnr = catnr
		self.celestrak_url = 'https://celestrak.com/satcat/tle.php?CATNR={}'.format(catnr)
		self.filename = 'tle-CATNR-{}.txt'.format(catnr)
		self.satellite = None
		self.ephemeris = None
	
	def get_tle(self):
		"""
		Uses the Skyfield library to make an API call to Celestrak for the most
		recent TLE for the specific satellite.
		"""
		self.satellite = load.tle_file(self.celestrak_url, filename=self.filename)[0]
		return self.satellite

	def gen_ephem_now(self, duration=3600, interval=60):
		"""
		Generates ephemeris starting now for the specified duration and interval.
		Duration and interval are in seconds.
		Returns ephemeris as a list of positions in either the WSG84 (1) or GCRS (2) 
		coordinate systems.
		"""
		self.ephemeris = []  # reset ephemeris data
		ts = load.timescale()
		t = ts.now()
		iterations = duration // interval
		for _ in range(iterations):
			# get GCRS coordinates
			geocentric = self.satellite.at(t)
			# Convert to lat, lon, alt
			lat, lon = wgs84.latlon_of(geocentric)
			height = wgs84.height_of(geocentric)
			coord = [lat.degrees, lon.degrees, height.m]
			self.ephemeris.append(coord)

			self.ephemeris.append(geocentric)

			# increment time
			t += timedelta(seconds=interval)

		return self.ephemeris
			
	def get_ephem(self):
		"""
		Returns the ephemeris data and None if create_ephem_now() has not be run.
		"""
		return self.ephemeris


# Driver code
if __name__ == "__main__":
	# Generate satellite ephemeris
	iss = SAT(25544)
	satellite = iss.get_tle()

	# Get observer position
	observer = GPS()
	observer.update_pos()
	print("Observer position:", observer.get_pos())
	time.sleep(1)

	# Start up and calibrate IMU
	imu = IMU(0x68)
	imu.calibrate(False, False)  # not calibrating to speed testing

	# main program loop to update device orientation
	while True:
		# Use Skyfield to get difference between satellite and observer position at this moment
		alt, az, distance = observer.calc_diff(satellite)

		if alt.degrees > 0:
			print('The ISS is above the horizon')

		print('-------------Look Angles and Distance to ISS----------------')
		print('Altitude: {0} ; Azimuth: {1} ; Distance {2:.1f}km'.format(round(alt.degrees, 2), round(az.degrees, 2), round(distance.km, 2)))
		print('')
		
		# read IMU for posture
		# TODO: add try/except clause to handle OSERROR where IMU device address changes
		rpy = imu.read_no_filter()


		# print ("Accel x: {0} ; Accel y : {1} ; Accel z : {2}".format(imu.AccelVals[0], imu.AccelVals[1], imu.AccelVals[2]))
		# print ("Gyro x: {0} ; Gyro y : {1} ; Gyro z : {2}".format(imu.GyroVals[0], imu.GyroVals[1], imu.GyroVals[2]))
		# print ("Mag x: {0} ; Mag y : {1} ; Mag z : {2}".format(imu.MagVals[0], imu.MagVals[1], imu.MagVals[2]))
		print('----------------------Device Posture------------------------')
		print("Roll: {0} ; Pitch : {1} ; Yaw : {2}".format(round(rpy[0], 2), round(rpy[1], 2), round(rpy[2], 2)))
		print('')
		print('============================================================')
		print('')

		time.sleep(0.5)