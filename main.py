import time
from gps import GPS
from sat import SAT
import PySimpleGUI as sg

# Generate satellite ephemeris
iss = SAT(25544)
satellite = iss.get_tle()

# Get observer position
observer = GPS()
observer.update_pos()
print("Observer position:", observer.get_pos())

sg.theme('BluePurple')

layout = [
			[sg.Text('Look Angles and Distance to ISS')],
			[sg.Text('Altitude: '), sg.Text(size=(15,1), key='-ALT-')],
			[sg.Text('Azimuth: '), sg.Text(size=(15,1), key='-AZ-')],
			[sg.Text('Distance (km): '), sg.Text(size=(15,1), key='-DIST-')],
			[sg.Button('Exit')]
		]

window = sg.Window('SatTrack', layout)

while True:
	event, values = window.read(1)
	print(event, values)

	alt, az, distance = observer.calc_diff(satellite)
	if alt.degrees > 0:
		print('The ISS is above the horizon')
	print('-------------Look Angles and Distance to ISS----------------')
	print('Altitude: {0} ; Azimuth: {1} ; Distance {2:.1f}km'.format(round(alt.degrees, 2), round(az.degrees, 2), round(distance.km, 2)))
	print('')
	
	if event in (None, 'Exit'):
		break

	# Update the "output" text element
	# to be the value of "input" element
	window['-ALT-'].update(round(alt.degrees, 2))
	window['-AZ-'].update(round(az.degrees, 2))
	window['-DIST-'].update(round(distance.km, 2))

	time.sleep(0.5)

window.close()

	