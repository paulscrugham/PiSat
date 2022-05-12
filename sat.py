from datetime import timedelta
from skyfield.api import load, wgs84

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