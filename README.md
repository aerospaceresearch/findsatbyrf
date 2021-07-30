# Description:
This program finds the center in the frequency domain of a signal by time.

# Usage:

## Step 1: Make a folder that containing the data of your signal inside the 'findsat' folder.
It should include:

* **(your_wave_file).wav**: The recorded wavefile that is needed to analyze

* **signal_info.txt**: Information about your wavefile, for example:
```
name = UnknownNOAA            
type = NOAA                                
center_frequency = 137.5e6                          
time_of_record = 2021-06-04T20:17:05Z
```
Note that the time of record must be written in ISO 8601 format in UTC (as in the example). More timezones and date formats will be supported later.
* **satellite.tle**: TLE (two-line elements) of the satellite whose signal belongs to, for example:
```
NOAA 18
1 28654U 05018A   21156.90071532  .00000084  00000-0  69961-4 0  9998
2 28654  98.9942 221.7189 0013368 317.9158  42.0985 14.12611611826810
```

* **station.txt**: Information about the station that recorded the signal, for example:
```
name = Stuttgart
long = 9.2356
lat = 48.777
alt = 200.0
```

Example of a 'data' folder: https://drive.google.com/drive/folders/1uGzdi6BOhARco0Xc8hvp6Qh80E-X6SoF

## Step 2: Run the program from the Command-Line Interface (CLI)
Simply use Python to run the file main.py with the following arguments:
```
[-h] [-i folder] [-ch1 frequency_in_Hz] [-ch2 frequency_in_Hz]
               [-ch3 frequency_in_Hz] [-ch4 frequency_in_Hz]
               [-bw1 frequency_in_Hz] [-bw2 frequency_in_Hz]
               [-bw3 frequency_in_Hz] [-bw4 frequency_in_Hz]
               [-step time_in_second] [-sen frequency_in_Hz] [-tle]
               [-begin time_in_second] [-end time_in_second]
```
with:
* -h: to show help.
* -i: to input the name of the the data folder.
* -ch1, -ch2, -ch3, -ch4: to input the frequencies of up to 4 channels to be analyzed.
* -bw1, -bw2, -bw3, -bw4: to input the bandwidth of up to 4 channels to be analyzed.
* -step: to input the length in time (in second) of each time interval, defaults to 1.
* -sen: to input the sensitivity, which is the width of each bin in the frequency kernel (in Hz) after FFT, defaults to 1.
* -begin: to input the time of begin of the segment to be analyzed, defaults to 1.
* -end: to input the time of end of the segment to be analyzed, defaults to the end of the file.
* -tle: used to turn on prediction based on Two-line elements (TLE) file, otherwise this function is off.

## Output:
1. A time vs. frequency graph, showing the center of the signal in the frequency domain by time, for example:
![image](https://drive.google.com/uc?export=view&id=1RjDIYBCl5piBFpMhxTO615D-8-g_1ZFK)

2. A .csv file storing the center position in the frequency domain by time.

Both files are stored in the same data folder.
