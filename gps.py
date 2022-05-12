import io
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