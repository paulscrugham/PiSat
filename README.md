# PiSat

See the PiSat in action in this video! 

[![PiSat Video](https://github.com/paulscrugham/PiSat/blob/master/README/pisat.jpg)](https://youtu.be/-QSAdjNMguM?t=193)

## What is PiSat?

PiSat is a Python GUI application running on a Raspberry Pi to help HAM radio operators aim an antenna at a satellite they want to communicate with and track it as it moves across the sky. All prediction calculations are performed on the device with occasional satellite TLE data updates from CelesTrak.

## What does PiSat do?

PiSat allows a user to select amateur radio satellites they want to track and displays their current position in table and skyplot views. Users can also enter up/downlink frequencies for each satellite to make it easier to tune a radio while tracking the satellite.

![alt text](https://github.com/paulscrugham/PiSat/blob/master/README/table.png)

The **Table** view shows current information about each tracked satellite. It also colors each satellite table row based on how far they are above an altitude of 0 degrees to make it easy to identify which satellites are highest in the sky. This view also shows the user-provided up/downlink for each satellite.

![alt text](https://github.com/paulscrugham/PiSat/blob/master/README/skyplot.png)

The **Skyplot** view shows the current location of satellites above an altitude of 0 degrees on a polar graph. The polar graph plots a satellite by its altitude and azimuth with 90 degrees being the center. Also shown is a trajectory path for each visible satellite showing how they will pass over the observer.

![alt text](https://github.com/paulscrugham/PiSat/blob/master/README/config.png)

The **Configure Satellites** view allows the user to select which satellites they would like shown in the Table and Skyplot views as well as manually enter up/downlink frequencies to be shown in the Table view.
