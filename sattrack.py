import io
import time
from datetime import datetime, timedelta

from skyfield.api import load, wgs84
from serial import Serial, SerialException
import pynmea2


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

	# main program loop to update device orientation
	while True:
		# ^^^^^^^^^^^^^RAW NMEA MESSAGE DEMO^^^^^^^^^^^^^
		# print(observer._read_line())

		# ^^^^^^^^^^^^^SAT LOCATION DEMO^^^^^^^^^^^^^
		# ts = observer.time_scale
		# geocentric = satellite.at(ts.now())
		# lat, lon = wgs84.latlon_of(geocentric)
		# height = wgs84.height_of(geocentric)
		# coord = [lat.degrees, lon.degrees, height.m]
		# print('')
		# print('-------------Current lat, lon, and elevation (km) of ISS now----------------')
		# print('Lat: {0:.3f}; Lon: {1:.3f}; Elev: {2:.1f}'.format(coord[0], coord[1], coord[2] / 1000))


		# ^^^^^^^^^^^^^LOOK ANGLE DEMO^^^^^^^^^^^^^
		# Use Skyfield to get difference between satellite and observer position at this moment
		alt, az, distance = observer.calc_diff(satellite)
		if alt.degrees > 0:
			print('The ISS is above the horizon')
		print('-------------Look Angles and Distance to ISS----------------')
		print('Altitude: {0} ; Azimuth: {1} ; Distance {2:.1f}km'.format(round(alt.degrees, 2), round(az.degrees, 2), round(distance.km, 2)))
		print('')
		

		# ^^^^^^^^^^^^^DO NOT COMMENT^^^^^^^^^^^^^
		time.sleep(0.5)