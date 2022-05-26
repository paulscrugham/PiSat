from datetime import timedelta
from re import T
from skyfield.api import load, wgs84

class SAT:
	"""
	Wrapper for the Skyfield library to get satellite ephemeris.
	Requests TLEs from Celestrak's web API via the Skyfield library.
	"""
	def __init__(self, user_sats):
		self.celestrak_url = 'https://celestrak.com/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle'
		self.filename = 'amateur.txt'
		self.TLEs = None
		self.events = {}
		self.ephemeris = {}
		self.user_sats = user_sats
	
	def load_tles(self):
		"""
		Uses the Skyfield library to make an API call to Celestrak for the most
		recent TLE for the specific satellite.
		"""
		raw_tles = load.tle_file(self.celestrak_url, filename=self.filename)
		# build look up dictionary of satellite TLE Skyfield objects
		# based on: https://rhodesmill.org/skyfield/earth-satellites.html#loading-a-tle-file
		self.TLEs = {sat.model.satnum: sat for sat in raw_tles}
		return self.TLEs

	def get_tle(self, id):
		"""
		Returns a single TLE from the look up dictionary.
		"""
		return self.TLEs[int(id)]

	def calc_events(self, observer_pos):
		"""
		Generates rise, culminate, and set events for satellites in the user_sats list 
		for a period of 5 days from the satellite's epoch.
		"""
		self.events = {}
		for entry in self.user_sats:
			sat = self.get_tle(entry)
			t0 = sat.epoch
			t1 = t0 + timedelta(days=5)
			t, events = sat.find_events(observer_pos, t0, t1)
			self.events[sat.model.satnum] = (t, events)

		return self.events



	def calc_ephemeris(self, start, stop, interval=1):
		"""
		Generates ephemeris between the start and stop times with the specified interval (seconds)
		for the specified satellite.
		Duration and interval are in seconds.
		Returns ephemeris as a list of positions in either the WSG84 (1) or GCRS (2) 
		coordinate systems.
		"""
		self.ephemeris = {}  # reset ephemeris data
		ts = load.timescale()
		t = ts.now()
		# TODO: find 
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
			
	def get_ephemeris(self, satellite):
		"""
		Returns the ephemeris data for the specified satellite.
		"""
		return self.ephemeris[satellite]