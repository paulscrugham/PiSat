from pisat import PiSat
from skyfield.api import load
import PySimpleGUI as sg
import math
import json

DEBUG = False

REFRESH_RATE = 1000  # used with window.read() to set the data refresh rate

# Application window dimensions
WINDOW_X = 720
WINDOW_Y = 480

THEME = 'Dark'

# Skyplot graph settings
C_LEN = 400  # canvas x and y dimension
C_CENTER = (C_LEN / 2, C_LEN / 2)  # a tuple representing the center of the canvas
C_OFFSET = 10  # margin in pixels
C_LEN_OFF = C_LEN - C_OFFSET

# Skyplot altitude line thickness
ALT_MINOR = 1
ALT_MAJOR = 2

# Skyplot functions
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


# load user defined list of satellites to track
sat_file = open('user_sats.json')
USER_SATS = json.load(sat_file)  # format: {ID:[UP, DOWN]}

# initialize PiSat
ps = PiSat(USER_SATS, expiry=5)
ps.load_tles('https://celestrak.com/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle') # downloads TLEs from CelesTrak from the amsat group

# get current location of observer
ps.update_pos()
if DEBUG: print("Observer position:", ps.get_pos())


sat_data = []
headings = ['ID', 'NAME', 'ALT (deg)', 'AZ (deg)', 'DIST (km)', 'UPLINK', 'DOWNLINK']
col_vis = [True, True, True, True, False, True, True]

# initialize table data list of lists
# TODO: change list of headings to look up table
for row, entry in enumerate(USER_SATS):
	sat_data.append([])
	sat = ps.get_tle(entry)
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


tab1_layout = [[sg.Table(values=sat_data, 
				headings=headings, 
				key='SAT_TABLE', 
				expand_y=True,
				visible_column_map=col_vis)]]

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

window = sg.Window('PiSat', layout, size=(WINDOW_X, WINDOW_Y), finalize=True, no_titlebar=False, element_justification='c')
sg.theme(THEME)

# initialize skyplot view
skyplot = window['skyplot']
skyplot.draw_point(C_CENTER, size=6, color='white')
draw_altitude_circles(skyplot)
draw_azimuth_lines(skyplot)

# initialize list of sat points
sat_points = []
sat_labels = []
sat_paths = []
for entry in USER_SATS:
	sat = ps.get_tle(entry)
	sat_points.append(skyplot.draw_point(C_CENTER, size=6, color='red'))
	sat_labels.append(skyplot.draw_text(sat.name, (C_CENTER[0], C_CENTER[1]), color='white'))
	sat_paths.append(None)


# main application loop
while True:
	event, values = window.read(REFRESH_RATE)
	if DEBUG: print(event, values)

	# loop to update satellite date
	for row, entry in enumerate(USER_SATS):
		sat = ps.get_tle(entry)  # look up sat TLE in dictionary of all sats
		alt, az, distance = ps.calc_diff(sat)
		
		# TABLE: save instantaneous satellite position data for table
		sat_data[row][2] = round(alt.degrees, 2)
		sat_data[row][3] = round(az.degrees, 2)
		sat_data[row][4] = round(distance.km, 2)

		# SKYPLOT: move satellite dot for skyplot view
		new_x, new_y = plot_polar(az.degrees, alt.degrees)
		skyplot.RelocateFigure(sat_points[row], new_x, new_y)
		skyplot.RelocateFigure(sat_labels[row], new_x, new_y + 10)

		# SKYPLOT: draw flight path if satellite is above 0 degrees
		if alt.degrees >= 0 and sat_paths[row] is None:
			# reset ephemeris for satellite to None
			sat_paths[row] = []
			# generate ephemeris (alt, az) for satellite
			path = ps.calc_path(sat)
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
sat_file.close()
