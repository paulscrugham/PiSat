from turtle import update
from skyfield.api import load
import PySimpleGUI as sg
import math
import json

from pisat import PiSat

DEBUG = True

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

def delete_polyline(graph, poly):
	pass

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
		graph.draw_line(C_CENTER, line_to, color='lightblue')
		graph.draw_text(int(i * 360 / divs), line_to, color='blue')

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
		graph.draw_circle(C_CENTER, radius, line_color='lightblue', line_width=line_width)
		graph.draw_text(int(angle_label), (C_CENTER[0], C_CENTER[1] + radius), color='blue')
		radius += circle_offset
		angle_label -= angle_offset

def update_user_sats(filepath, user_sats, sat_config):
	"""
	Updates the specified file with data from the PySimpleGUI elements
	in the sat_config list. Returns an updated user_sat dict.
	"""
	# update USER_SATS
	for config in sat_config:
		sat_num = config[0].metadata
		if config[0].get():
			user_sats[sat_num] = {}
			user_sats[sat_num]['up'] = config[2].get()
			user_sats[sat_num]['down'] = config[4].get()
		else:
			if sat_num in user_sats: user_sats.pop(config[0].metadata)

	# save new user sat info to file
	with open(filepath, 'w') as sat_file:
		json.dump(user_sats, sat_file)

	return user_sats

def update_table_data(user_sats, headings, ps):
	sat_data = []

	# initialize table data list of lists
	# TODO: change list of headings to look up table
	for row, entry in enumerate(user_sats):
		sat_data.append([])
		sat = ps.get_tle(entry)
		for col in headings:
			if col == 'ID':
				sat_data[row].append(sat.model.satnum)
			elif col == 'NAME':
				sat_data[row].append(sat.name)
			elif col == 'UPLINK':
				sat_data[row].append(user_sats[entry]['up'])
			elif col == 'DOWNLINK':
				sat_data[row].append(user_sats[entry]['down'])
			else:
				sat_data[row].append(0)
	return sat_data

def update_skyplot(user_sats, ps, skyplot, sat_points=[], sat_labels=[], sat_paths=[]):
	for i in range(len(sat_points)):
		skyplot.delete_figure(sat_points[i])
		skyplot.delete_figure(sat_labels[i])
		if sat_paths[i]:
			for j in range(len(sat_paths[i])):
				skyplot.delete_figure(sat_paths[i][j])
	
	sat_points = []
	sat_labels = []
	sat_paths = []
	for entry in user_sats:
		sat = ps.get_tle(entry)
		sat_points.append(skyplot.draw_point(C_CENTER, size=6, color='red'))
		sat_labels.append(skyplot.draw_text(sat.name, (C_CENTER[0], C_CENTER[1]), color='white'))
		sat_paths.append(None)

	return sat_points, sat_labels, sat_paths

def map_colors(sat_data):
	colors = []
	for i, sat in enumerate(sat_data):
		if sat[2] <= 0:
			color = (i, 'grey')
		elif sat[2] <= 15:
			color = (i, '#dffbed')
		elif sat[2] <= 30:
			color = (i, '#9ef2c8')
		elif sat[2] < 45:
			color = (i, '#5eeaa3')
		elif sat[2] < 60:
			color = (i, '#1ee17f')
		elif sat[2] < 75:
			color = (i, '#15a15a')
		elif sat[2] < 90:
			color = (i, '#0d6136')
		colors.append(color)

	return colors

# Application code
if __name__ == '__main__':
	# load user defined list of satellites to track
	with open('user_sats.json', 'r+') as sat_file:
		USER_SATS = json.load(sat_file)  # format: {ID:[UP, DOWN]}

	# initialize PiSat
	ps = PiSat(USER_SATS, expiry=5)
	ps.load_tles('https://celestrak.com/NORAD/elements/gp.php?GROUP=amateur&FORMAT=tle') # downloads TLEs from CelesTrak from the amsat group

	# get current location of observer
	ps.update_pos()
	# if DEBUG: print("Observer position:", ps.get_pos())


	headings = ['ID', 'NAME', 'ALT (deg)', 'AZ (deg)', 'DIST (km)', 'UPLINK', 'DOWNLINK']
	col_vis = [True, True, True, True, False, True, True]

	sat_data = update_table_data(USER_SATS, headings, ps)


	tab1_layout = [[sg.Table(values=sat_data, 
					headings=headings, 
					key='SAT_TABLE', 
					expand_y=True,
					visible_column_map=col_vis,
					text_color='black',
					row_height=20)]]

	tab2_layout = [[sg.Graph(canvas_size=(C_LEN, C_LEN), 
				graph_bottom_left=(0, 0), 
				graph_top_right=(C_LEN, C_LEN),
				key='skyplot')]]

	sat_config = []

	sats = ps.get_tles()
	for sat in sats:
		checked = False
		up = ''
		down = ''
		if str(sat) in USER_SATS:
			checked = True
			up = USER_SATS[str(sat)]['up']
			down = USER_SATS[str(sat)]['down']
		sat_config.append([
			sg.Checkbox(sats[sat].name, size=(25, None), default=checked, metadata=str(sat)), 
			sg.Text('Up (Mhz)'), 
			sg.Input(up, size=(20, None), metadata=str(sat)),
			sg.Text('Down (Mhz)'), 
			sg.Input(down, size=(20, None), metadata=str(sat))])

	tab3_layout = [[sg.Column(sat_config, 
					scrollable=True, 
					vertical_scroll_only=True,
					expand_x=True,
					expand_y=True,
					size=(None, 300))],
					[sg.Button('Update Satellites'), sg.Button('Check All'), sg.Button('Check None')]]

	tab_group_layout = [[
		sg.Tab('Table', tab1_layout, font='Courier 15', key='-TAB1-'),
		sg.Tab('Skyplot', tab2_layout, font='Courier 15', key='-TAB2-'),
		sg.Tab('Configure Satellites', tab3_layout, font='Courier 15', key='-TAB3-', expand_y=True)
	]]

	layout = [	[sg.TabGroup(tab_group_layout,
						enable_events=True,
						key='-TABGROUP-',
						size=(None,400),
						expand_y=True)],
				[sg.Button('Exit'), sg.Text('Observer Location: '), sg.Text(ps.get_pos())]]

	window = sg.Window('PiSat', layout, size=(WINDOW_X, WINDOW_Y), finalize=True, no_titlebar=False)
	sg.theme(THEME)

	# initialize skyplot view
	skyplot = window['skyplot']
	draw_altitude_circles(skyplot)
	draw_azimuth_lines(skyplot)

	# initialize list of sat points, labels, and paths
	sat_points, sat_labels, sat_paths = update_skyplot(USER_SATS, ps, skyplot)

	# main application loop
	while True:
		event, values = window.read(REFRESH_RATE)
		# if DEBUG: print(event, values)
		print(event)

		# loop to update satellite date
		for row, entry in enumerate(USER_SATS):
			sat = ps.get_tle(entry)  # look up sat TLE in dictionary of all sats
			alt, az, distance = ps.calc_diff(sat)
			
			# TABLE: save instantaneous satellite position data for table
			sat_data[row][2] = round(alt.degrees, 2)
			sat_data[row][3] = round(az.degrees, 2)
			sat_data[row][4] = round(distance.km, 2)

			# sat_data.sort(key=lambda x: x[2])

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

		if event == 'Update Satellites':
			# update user_sats.json
			USER_SATS = update_user_sats('user_sats.json', USER_SATS, sat_config)
			sat_data = update_table_data(USER_SATS, headings, ps)
			sat_points, sat_labels, sat_paths = update_skyplot(USER_SATS, ps, skyplot, sat_points, sat_labels, sat_paths)

		if event == 'Check All':
			for config in sat_config:
				config[0].update(value=True)

		if event == 'Check None':
			for config in sat_config:
				config[0].update(value=False)


		# Update the "output" text element
		# to be the value of "input" element
		window['SAT_TABLE'].update(sat_data, row_colors=map_colors(sat_data))

	window.close()
