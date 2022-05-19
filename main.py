from pkg_resources import EntryPoint
from gps import GPS
from sat import SAT
from skyfield.api import load
import PySimpleGUI as sg

DEBUG = False

REFRESH_RATE = 1000  # used with window.read() to set the data refresh rate

# constant variable to store user provided sat data.
# format: {ID:[UP, DOWN]}
USER_SATS = {
	'25544': 	{'up': '437.550', 			'down': '437.550'}, # ISS
	'7530': 	{'up': '145.850-145.950', 	'down':'29.400- 29.500'}, # OSCAR 7
	'14781': 	{'up': '', 					'down': '145.826/435.025'}, # OSCAR 11
	'22825': 	{'up': '145.850', 			'down': '436.795 '}, # EYESAT-1
	'24278': 	{'up': '145.900-146.000', 	'down': '435.900-435.800'}, # JAS 2 (FO-29)
	'27844': 	{'up': '', 					'down': '437.470 '} # CUTE-1
}

def debug_print(element):
	if DEBUG: print(element)

# other CelesTrak URLs/file names
# 'https://celestrak.com/satcat/tle.php?CATNR={}'.format(25544)
# 'tle-CATNR-{}.txt'.format(25544)

# Download TLEs from the CelesTrak amateur radio group
satellites = load.tle_file('https://celestrak.com/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle', 'amateur.txt')
debug_print(satellites)

# build lookup dictionary for satellites
# based on: https://rhodesmill.org/skyfield/earth-satellites.html#loading-a-tle-file
by_number = {sat.model.satnum: sat for sat in satellites}

# Get observer position
# TODO: add while loop to handle sat lock - took awhile to start streaming GPS data on 5/12
observer = GPS()
observer.update_pos()
debug_print("Observer position:{}".format(observer.get_pos()))

sg.theme('Dark')

sat_data = []
headings = ['ID', 'NAME', 'ALTITUDE', 'AZIMUTH', 'DISTANCE', 'UPLINK', 'DOWNLINK']

# initialize table data list of lists
for row, entry in enumerate(USER_SATS):
	sat_data.append([])
	sat = by_number[int(entry)]
	for col in headings:
		if col == 'ID':
			sat_data[row].append(sat.model.satnum)
		elif col == 'NAME':
			sat_data[row].append(sat.name)
		elif col == 'UPLINK':
			sat_data[row].append(USER_SATS[entry]['up'])
		elif col == 'DOWNLINK':
			sat_data[row].append(USER_SATS[entry]['down'])
		else:
			sat_data[row].append(0)

table_layout = [
	[sg.Text('Look Angles and Distance to ISS')],
	[sg.Table(values=sat_data, headings=headings, key='SAT_TABLE')],
	[sg.Button('Exit')]
]

skyplot_layout = [
	[sg.Graph(canvas_size=(400, 400), graph_bottom_left=(0, 0), graph_top_right=(400, 400))]
]

window = sg.Window('SatTrack', table_layout)

while True:
	event, values = window.read(REFRESH_RATE)
	debug_print(event, values)

	for row, entry in enumerate(USER_SATS):
		sat = by_number[int(entry)]  # look up sat in dictionary of all sats
		alt, az, distance = observer.calc_diff(sat)
		sat_data[row][2] = round(alt.degrees, 2)
		sat_data[row][3] = round(az.degrees, 2)
		sat_data[row][4] = round(distance.km, 2)
	
	# sort sat_data by distance to observer

	if event in (None, 'Exit'):
		break

	# Update the "output" text element
	# to be the value of "input" element
	window['SAT_TABLE'].update(sat_data)


window.close()

	