import numpy as np
from skyfield.api import load, wgs84, utc
from scipy.constants import c
import datetime
import os

def centroid(freq, mag):
    """Finding the center, or spectral centroid, of the signal.
    """   
    mag_sum = np.sum(mag)
    if mag_sum == 0:
        return None
    else:
        return  np.sum(freq * mag) / mag_sum

def avg_binning(inputArray, resolution):
    avg_mag = np.empty(resolution)
    for i, value in enumerate(np.array_split(inputArray, resolution)):
        avg_mag[i] = np.mean(value)
    return avg_mag

def channel_filter(mag, resolution, pass_step_width):
    in_channel = False
    mag[-pass_step_width:-1] = 0
    for i in range(resolution):
        if (in_channel == False) and (mag[i] > 0):
            in_channel = True
            channel_begin = i
        if (in_channel == True) and (mag[i] == 0) and (np.all(mag[i+1:i+pass_step_width]==0)):
            in_channel = False
            if (i - channel_begin < pass_step_width):
                mag[channel_begin:i] = 0

def calculate_offset(input_mag):
    #resolution = int(full_bandwidth/pass_bandwidth)
    resolution = 10
    mag = np.empty(resolution)
    std = np.empty(resolution)
    for i, value in enumerate(np.array_split(input_mag, resolution)):
        mag[i] = np.mean(value)
        std[i] = np.std(value)
    return - (np.min(mag) + 4*np.min(std))

class TLE:
    def __init__(self, signal_object):#data_path, time_of_record, total_step, step_timelength
        time_scale = load.timescale()
        with open(os.path.normpath(signal_object.data_path+"/station.txt"), "r") as f:
            for _ in range(4):
                input_string = f.readline().replace(" ","").strip("\n").split("=")
                if 'name' in input_string[0]:
                    self.station_name = input_string[1]
                elif 'long' in input_string[0]:
                    station_long = float(input_string[1])
                elif 'lat' in input_string[0]:
                    station_lat = float(input_string[1])
                elif 'alt' in input_string[0]:
                    station_alt = float(input_string[1])
        self.station = wgs84.latlon(station_lat, station_long, station_alt)
        self.satellite = load.tle_file(os.path.normpath(signal_object.data_path+"/satellite.tle"))[0]
        self.time_of_record = signal_object.time_of_record.replace(tzinfo=utc)
        self.signal_time = [time_scale.utc(self.time_of_record + datetime.timedelta(seconds=step*signal_object.step_timelength)) for step in range(signal_object.total_step)]
        self.channel_frequencies = signal_object.channel_frequencies

    def Doppler_prediction(self, channel, step):
        """
        function to calculated Doppler shift frequency from skyfield objects, ideas from https://en.wikipedia.org/wiki/Relativistic_Doppler_effect#Motion_in_an_arbitrary_direction
        """
        relative = self.station - self.satellite
        r = relative.at(self.signal_time[step]).position.m
        v = relative.at(self.signal_time[step]).velocity.m_per_s
        beta = np.linalg.norm(v) / c
        gamma = 1 / np.sqrt(1 - beta**2)
        cos_theta = np.dot(r, v) / (np.linalg.norm(r) * np.linalg.norm(v))
        return self.channel_frequencies[channel] / (gamma * (1 + beta * cos_theta))



