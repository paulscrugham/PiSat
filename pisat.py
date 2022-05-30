from datetime import timedelta
import io
from skyfield.api import load, wgs84
from serial import Serial, SerialException
import pynmea2

class PiSat:
	"""
	Wrapper for the ublox CO99-F9P board.
	Uses the serial library to read device data.
	Uses the pynmea2 library to parse nmea sentences.
	Receives data over UART.
	"""
	def __init__(self, user_sats, expiry=5, address="/dev/ttyACM0", baud=9600):
		# GPS specific class members
		self.address = address
		self.baud = baud
		self.ser = Serial(self.address, self.baud, timeout=5.0)  # Get raw byte data from serial port
		self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser))  # convert to string type
		# satellite specific class members
		self.TLEs = None
		self.expiry = expiry
		self.events = {}
		self.ephemeris = {}
		self.user_sats = user_sats
		
		
		self.position = {}
		self.ts = load.timescale()

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

	def load_tles(self, url='https://celestrak.com/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle'):
		"""
		Uses the Skyfield library to make an API call to Celestrak for the most
		recent TLE for the specific satellite.
		"""
		raw_tles = load.tle_file(url)
		# build look up dictionary of satellite TLE Skyfield objects
		# based on: https://rhodesmill.org/skyfield/earth-satellites.html#loading-a-tle-file
		self.TLEs = {sat.model.satnum: sat for sat in raw_tles}
		return self.TLEs

	def get_tle(self, id):
		"""
		Returns a single TLE from the look up dictionary.
		"""
		return self.TLEs[int(id)]
	
	def update_pos(self):
		"""
		Returns a Skyfield object representing the position of the observer.
		"""
		# TODO: add while loop to handle sat lock - took awhile to start streaming GPS data on 5/12
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
		
		return self.position

	def get_pos(self):
		"""Returns the last received position. Use update_pos() to update the coordinates."""
		return self.position

	def calc_diff(self, satellite):
		"""
		Uses the Skyfield library to perform vector subtraction of the satellite and observer positions.
		"""
		difference = satellite - self.position
		t = self.ts.now()
		topocentric = difference.at(t)
		return topocentric.altaz()

	def calc_path(self, satellite):
		"""
		Calculates ephemeris of the specified satellite while it is visible.
		"""
		t = self.ts.now()
		sat_ephemeris = []
		alt, az, distance = self.calc_diff(satellite)
		while alt.degrees >= 0:
			difference = satellite - self.position
			topocentric = difference.at(t)
			alt, az, distance = topocentric.altaz()
			sat_ephemeris.append((az.degrees, alt.degrees))
			t += timedelta(seconds=2)

		return sat_ephemeris

	def calc_events(self):
		"""
		Generates rise, culminate, and set events for satellites in the user_sats list 
		for a period of 5 days from the satellite's epoch.
		"""
		self.events = {}
		for entry in self.user_sats:
			sat = self.get_tle(entry)
			t0 = sat.epoch
			t1 = t0 + timedelta(days=self.expiry)
			t, events = sat.find_events(self.position, t0, t1)
			self.events[sat.model.satnum] = (t, events)

		return self.events

	def calc_ephem(self):
		"""
		Calculates ephemeris for all events.
		"""
		# TODO: complete function to precompute ephemeris
		self.calc_events()  # calculate events
		for sat in self.user_sats:
			# create temporary list of rise and set times for this satellite's events.
			temp = []
			# if satellite is already visible, set the start of the first event window to now
			if self.events[sat][1][0] == 1 or self.events[sat][1][0] == 2:
				temp.append(self.ts.now())

			for ti, event in zip(self.events[sat][0], self.events[sat][1]):
				if event == 0 or event == 2:
					temp.append(ti)

			# if the last rise/set event is cut short, set the final set time to epoch plus expiry
			if self.events[sat][1][-1] != 2:
				temp.append()

	
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
