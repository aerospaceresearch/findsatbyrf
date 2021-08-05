# Description:
This program finds the center in the frequency domain of a signal by time.

# Usage:

## Step 1: Prepare your wave file (.wav/.dat) and a json file containing the information about your signal
Example of a json file:
```
{
    "signal": {
        "name": "CUBESAT",
        "type": null,
        "center_frequency": 401e6,
        "time_of_record": "2021-03-26T20:41:24.00Z"
    },
    "tle": {
        "line_1": "1 47448U 21006AM  21085.91927129  .00000916  00000-0  55862-4 0  9998",
        "line_2": "2 47448  97.5067 148.6617 0013215  32.4216 327.7824 15.12754713  9576"
    },
    "station": {
        "name": "Jena",
        "longitude": 11.56886,
        "latitude": 50.91847,
        "altitude": 150.0
    }
}
```

Where:
* "signal" object contains information about the signal file, such as name, center frequency and time of record. For now, there is only "type": "NOAA" is supported, if the signal is not NOAA then you should put "type": null or simply remove that key.
* "tle" object contains the two lines of the "two-line element" file of the satellite that the signal comes from.
* "station" object contains the information of the station, such as name, longitude (degree), latitude (degree) and altitude (meter).

> **_NOTE:_** "tle" and "station" objects are only needed if you intend to use signal center frequency prediction based on TLE, otherwise you can remove them.

## Step 2: Run the program from the Command-Line Interface (CLI)
Simply use Python to run the file main.py with the following arguments:
```
[-h] 
-f wav/dat_file 
-i json_file 
[-o name_of_output_file] 
-ch1 frequency_in_Hz    -bw1 frequency_in_Hz
[-ch2 frequency_in_Hz] [-bw2 frequency_in_Hz]
[-bw3 frequency_in_Hz] [-ch3 frequency_in_Hz]
[-ch4 frequency_in_Hz] [-bw4 frequency_in_Hz] 
[-step time_in_second]
[-sen frequency_in_Hz] 
[-tle] 
[-begin time_in_second]
[-end time_in_second]
```

With:
* -h: to show help.
* -f (required): to input the directory of the wave file.
* -i (required): to input the json signal information file.
* -o: directory and name without extension of the wanted output file, defaults to "./output".
* -ch0 (required), -ch1, -ch2, -ch3: to input the frequencies (in Hz) of up to 4 channels to be analyzed.
* -bw0 (required), -bw1, -bw2, -bw3: to input the bandwidth (in Hz) of up to 4 channels to be analyzed.
* -step: to input the length in time (in second) of each time interval, defaults to 1.
* -sen: to input the sensitivity, which is the width of each bin in the frequency kernel (in Hz) after FFT, defaults to 1.
* -begin: to input the time of begin of the segment to be analyzed, defaults to 1.
* -end: to input the time of end of the segment to be analyzed, defaults to the end of the file.
* -tle: used to turn on prediction based on Two-line elements (TLE) file, otherwise this function is off.

> **EXAMPLES:** 
```
python3 .\main.py -i .\MySignal.json -f .\MySatellite\MySignal.wav -ch0 400.575e6 -bw0 20e3 -o D:\\CubeSat -begin 10. -end 60. -tle

python3 ./main.py -i /home/MyUser/MySignal.json -f ./MySatellite/MySignal.wav -ch0 400.575e6 -bw0 20e3 -o ./CubeSat
```
 
## Output:
1. A time vs. frequency graph, showing the center of the signal in the frequency domain by time, for example:
![image](https://drive.google.com/uc?export=view&id=1RjDIYBCl5piBFpMhxTO615D-8-g_1ZFK)

2. A .csv file storing the center position in the frequency domain by time.

Both files are exported with name and directory as selected with the [-o] argument.
