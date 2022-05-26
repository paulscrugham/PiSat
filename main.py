from turtle import color
from pkg_resources import EntryPoint
from gps import GPS
from sat import SAT
from skyfield.api import load
import PySimpleGUI as sg
import math

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
	'27844': 	{'up': '', 					'down': '437.470 '}, # CUTE-1
	'23439': 	{'up': '', 					'down': ''},
	'26931': 	{'up': '', 					'down': ''},
	'20442': 	{'up': '', 					'down': ''},
	'25397': 	{'up': '', 					'down': ''},
	'36122': 	{'up': '', 					'down': ''},
	'37839': 	{'up': '', 					'down': ''},
	'37841': 	{'up': '', 					'down': ''},
	'37855': 	{'up': '', 					'down': ''},
	'39090': 	{'up': '', 					'down': ''},
	'39134': 	{'up': '', 					'down': ''},
	'39135': 	{'up': '', 					'down': ''},
	'39136': 	{'up': '', 					'down': ''},
	'39417': 	{'up': '', 					'down': ''},
	'39430': 	{'up': '', 					'down': ''},
	'39440': 	{'up': '', 					'down': ''},
	'39444': 	{'up': '', 					'down': ''},
	'39446': 	{'up': '', 					'down': ''},
	'39770': 	{'up': '', 					'down': ''},
	'40012': 	{'up': '', 					'down': ''},
	'40021': 	{'up': '', 					'down': ''},
	'40025': 	{'up': '', 					'down': ''},
	'40900': 	{'up': '', 					'down': ''},
	'40901': 	{'up': '', 					'down': ''},
	'40902': 	{'up': '', 					'down': ''},
	'40903': 	{'up': '', 					'down': ''}
	
}

# initialize satellites object
satellites = SAT(USER_SATS)
satellites.load_tles()
if DEBUG: print(satellites)

# initialize GPS object for observer
# TODO: add while loop to handle sat lock - took awhile to start streaming GPS data on 5/12
observer = GPS()
pos = observer.update_pos()
if DEBUG: print("Observer position:", observer.get_pos())

events = satellites.calc_events(pos)
print(events[25544][0])
print(events[25544][1])

for ti, event in zip(events[25544][0], events[25544][1]):
	name = ('rise above 0°', 'culminate', 'set below 0°')[event]
	print(ti.utc_strftime('%Y %b %d %H:%M:%S'), name)

sg.theme('Dark')

sat_data = []
headings = ['ID', 'NAME', 'ALTITUDE', 'AZIMUTH', 'DISTANCE', 'UPLINK', 'DOWNLINK']

# initialize table data list of lists
# TODO: change list of headings to look up table
for row, entry in enumerate(USER_SATS):
	sat_data.append([])
	sat = satellites.get_tle(entry)
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

# Graph constants
C_LEN = 400  # must be divisible by 2
C_CENTER = (C_LEN / 2, C_LEN / 2)
C_OFFSET = 10
C_LEN_OFF = C_LEN - C_OFFSET

# Skyplot Graphic constants
ALT_MINOR = 1
ALT_MAJOR = 2

def plot_polar(az, alt):
	# don't plot point if altitude is below 0 degrees
	# if alt < 0:
	# 	return None
	
	# calculate radius in pixels
	magnitude = (90 - alt) / 90
	radius = C_LEN_OFF / 2 * magnitude

	# calculate azimuth x, y
	az_rads = math.radians(az)
	x = math.sin(az_rads) * radius + C_CENTER[0]
	y = math.cos(az_rads) * radius + C_CENTER[1]
	return x, y

def draw_azimuth_lines(graph, divs=12):
	# draw azimuth lines
	divs = 12
	radius = C_LEN_OFF / 2
	for i in range(divs):
		az_rads = math.radians(i * 360 / divs)
		x_to = math.sin(az_rads) * radius + C_CENTER[0]
		y_to = math.cos(az_rads) * radius + C_CENTER[1]
		line_to = (x_to, y_to)
		graph.draw_line(C_CENTER, line_to, color='gray')
		graph.draw_text(int(i * 360 / divs), line_to, color='gray')

def draw_altitude_circles(graph, divs=6):
	# draw altitude circles
	circle_offset = C_LEN_OFF / 2 / divs
	angle_offset = 90 / divs
	radius = circle_offset
	angle_label = 90 - angle_offset
	line_width = ALT_MINOR
	for i in range(divs):	
		if i == divs - 1:
			line_width = ALT_MAJOR
		graph.draw_circle(C_CENTER, radius, line_color='gray', line_width=line_width)
		graph.draw_text(int(angle_label), (C_CENTER[0], C_CENTER[1] + radius), color='gray')
		radius += circle_offset
		angle_label -= angle_offset

tab1_layout = [[sg.Table(values=sat_data, 
				headings=headings, 
				key='SAT_TABLE')]]

tab2_layout = [[sg.Graph(canvas_size=(C_LEN, C_LEN), 
			graph_bottom_left=(0, 0), 
			graph_top_right=(C_LEN, C_LEN),
			key='skyplot')]]

tab_group_layout = [[
	sg.Tab('Table', tab1_layout, font='Courier 15', key='-TAB1-'),
	sg.Tab('Skyplot', tab2_layout, font='Courier 15', key='-TAB2-')

]]

layout = [[sg.TabGroup(tab_group_layout,
                       enable_events=True,
                       key='-TABGROUP-')],
          [sg.Button('Exit')]]

WINDOW_X = 720
WINDOW_Y = 480

window = sg.Window('PiSat', layout, size=(WINDOW_X, WINDOW_Y), finalize=True, no_titlebar=False, element_justification='c')

skyplot = window['skyplot']
skyplot.draw_point(C_CENTER, size=6, color='white')
draw_altitude_circles(skyplot)
draw_azimuth_lines(skyplot)

# initialize list of sat points
sat_points = []
sat_labels = []
sat_paths = []
for entry in USER_SATS:
	sat = satellites.get_tle(entry)
	sat_points.append(skyplot.draw_point(C_CENTER, size=6, color='red'))
	sat_labels.append(skyplot.draw_text(sat.name, (C_CENTER[0], C_CENTER[1]), color='white'))
	sat_paths.append(None)

while True:
	event, values = window.read(REFRESH_RATE)
	if DEBUG: print(event, values)

	for row, entry in enumerate(USER_SATS):
		sat = satellites.get_tle(entry)  # look up sat TLE in dictionary of all sats
		alt, az, distance = observer.calc_diff(sat)
		sat_data[row][2] = round(alt.degrees, 2)
		sat_data[row][3] = round(az.degrees, 2)
		sat_data[row][4] = round(distance.km, 2)
		new_x, new_y = plot_polar(az.degrees, alt.degrees)
		skyplot.RelocateFigure(sat_points[row], new_x, new_y)
		skyplot.RelocateFigure(sat_labels[row], new_x, new_y + 10)

		# draw flight path if satellite is above 0 degrees
		if alt.degrees >= 0 and sat_paths[row] is None:
			# reset ephemeris for satellite to None
			sat_paths[row] = []
			# generate ephemeris (alt, az) for satellite
			path = observer.calc_path(sat)
			# convert az and alt values to screen coordinates
			for i in range(len(path)- 1):
				point_from = plot_polar(path[i][0], path[i][1])
				point_to = plot_polar(path[i+1][0], path[i+1][1])
				# add line segment to skyplot
				sat_paths[row].append(skyplot.draw_line(point_from, point_to, color='black'))

		elif alt.degrees < 0 and sat_paths[row] is not None:
			# delete polyline from skyplot
			for i in range(len(sat_paths[row])):
				skyplot.delete_figure(sat_paths[row][i])

			sat_paths[row] = None

	if event in (None, 'Exit'):
		break

	# Update the "output" text element
	# to be the value of "input" element
	window['SAT_TABLE'].update(sat_data)




window.close()

	