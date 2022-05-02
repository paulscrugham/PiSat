import time
from datetime import datetime, timedelta
from smbus2 import SMBus
from imusensor.MPU9250 import MPU9250
# from imusensor.filters import kalman
from skyfield.api import load, wgs84
from serial import Serial
import pynmea2

class IMU:
	"""
	Wrapper for the MPU9250. Uses the imusensor and smbus2 libraries to
	interface with the hardware. 
	Receives data over I2C.
	"""
	def __init__(self, bus=1, address=0x68):
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
		self.ser = Serial(self.address, self.baud)

	def read(self):
		# tty = io.TextIOWrapper(io.FileIO(os.open("/dev/{0}".format(self.address), os.O_NOCTTY),"r+"))
		data = self.ser.readline()
		if data:
			return data

class SAT:
	"""
	Wrapper for the Skyfield library to get satellite ephemeris.
	"""
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

	def gen_ephem_now(self, duration=3600, interval=60, coord_sys=1):
		"""
		Generates ephemeris starting now for the specified duration and interval.
		Duration and interval are in seconds.
		Returns ephemeris as a list of positions in either the WSG84 (1) or GCRS (2) 
		coordinate systems.
		"""
		self.ephemeris = []  # reset ephemeris data
		ts = load.timescale()
		t = ts.now()
		for _ in range(duration / interval):
			# get GCRS coordinates
			geocentric = self.satellite.at(t)
			if coord_sys == 1:
			# case if specified coordinate system is WSG84
				lat, lon = wgs84.latlon_of(geocentric)
				height = wgs84.height_of(geocentric)
				coord = [lat.degrees, lon.degrees, height.km]
				self.ephemeris.append(coord)
			elif coord_sys == 2:
			# case if specific coordinate system is GCRS
				self.ephemeris.append(geocentric.position.km)

			# increment time
			t += timedelta(seconds=interval)
			
	def get_ephem(self):
		"""
		Returns the ephemeris data and None if create_ephem_now() has not be run.
		"""
		return self.ephemeris



		
		


# Driver code
if __name__ == "__main__":
	# Generate satellite ephemeris
	iss = SAT(25544)
	iss.get_tle()
	iss.gen_ephem_now()

	# Receive 10 seconds of GPS data to get location lock
	gps = GPS()
	start = datetime.now()  # system time now
	while datetime.now() - timedelta(start) < 10:
		pass
	
	
	# Start and calibrate IMU
	imu = IMU()
	imu.calibrate(False, False)  # not calibrating to speed testing



	

# main program loop to update device orientation
while True:
	rpy = imu.read_no_filter()
	nmea = pynmea2.parse(gps.read())

	# print ("Accel x: {0} ; Accel y : {1} ; Accel z : {2}".format(imu.AccelVals[0], imu.AccelVals[1], imu.AccelVals[2]))
	# print ("Gyro x: {0} ; Gyro y : {1} ; Gyro z : {2}".format(imu.GyroVals[0], imu.GyroVals[1], imu.GyroVals[2]))
	# print ("Mag x: {0} ; Mag y : {1} ; Mag z : {2}".format(imu.MagVals[0], imu.MagVals[1], imu.MagVals[2]))
	print("IMU: roll: {0} ; pitch : {1} ; yaw : {2}".format(rpy[0], rpy[1], rpy[2]))
	print("GPS:", nmea)
	print(type(nmea))
	time.sleep(0.5)