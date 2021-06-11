# Usage:
Make a folder that containing the data of your signal inside the 'findsat' folder. It should include:

**satellite.tle**: TLE (two-line elements) of the satellite whose signal belongs to, for example:
```
NOAA 18
1 28654U 05018A   21156.90071532  .00000084  00000-0  69961-4 0  9998
2 28654  98.9942 221.7189 0013368 317.9158  42.0985 14.12611611826810
```
**station.txt**: Information about the station that recorded the signal, for example:
```
name = Stuttgart
long = 9.2356
lat = 48.777
alt = 200.0
```
**(your_wave_file).wav**: The recorded wavefile that is needed to analyze

Then change the information in the **main.py** and run it with python3. The result will be put in your data folder.

Example of a 'data' folder: https://drive.google.com/drive/folders/1uGzdi6BOhARco0Xc8hvp6Qh80E-X6SoF
