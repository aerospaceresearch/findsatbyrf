import numpy as np
from numpy.core.numeric import NaN
from skyfield.api import load, EarthSatellite, wgs84, utc
from scipy.constants import c
import datetime
import os
from scipy import signal 

def centroid(freq, mag):
    """Finding the center, or spectral centroid, of the signal.
    """   
    mag_sum = np.sum(mag)
    if mag_sum == 0:
        return NaN
    else:
        return  np.sum(freq * mag) / mag_sum

def avg_binning(inputArray, resolution):
    if len(inputArray) <= resolution:
        return inputArray
    avg_mag = np.empty(resolution)
    for i, value in enumerate(np.array_split(inputArray, resolution)):
        avg_mag[i] = np.mean(value)
    return avg_mag

def channel_filter(mag, resolution, pass_step_width):
    """filter our every peaks that narrower than pass_step_width, deprecated""" 
    #tools.channel_filter(filtered_mag, self.resolutions[channel], pass_step_width = int(self.pass_bandwidth / self.channel_bandwidths[channel] * self.resolutions[channel]))
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

def calculate_offset(input_mag, filter_strength):
    #resolution = int(full_bandwidth/pass_bandwidth)
    resolution = 16            #Divide the kernel to 16 parts
    mag = np.empty(resolution)
    std = np.empty(resolution)
    for i, value in enumerate(np.array_split(input_mag, resolution)):
        if np.any((value != 0)):
            mag[i] = np.mean(value)
            std[i] = np.std(value)
    return - (np.min(mag) + 3 * filter_strength * np.min(std))

def lowpass_filter(centroids, step_timelength):
    sos = signal.butter(8, 0.02*step_timelength, output='sos')
    return signal.sosfiltfilt(sos, centroids, padlen=int(len(centroids)/10))

def peak_finding(freq_domain, mag_domain, centroid, range = 1e3):
    if np.isnan(centroid):
        return NaN
    local_region_indices = np.where(np.logical_and(freq_domain> centroid - range/2, freq_domain < centroid + range/2))          #Search for peaks in +- 1kHz around the centroid
    local_mag = mag_domain[local_region_indices]
    if np.all((local_mag == 0)):
        return NaN
    local_freq = freq_domain[local_region_indices]
    local_peak = np.argmax(local_mag)
    return local_freq[local_peak]

def remove_outliers(centroids):
    """Removing ourliers for centroids"""
    cutoff = np.std(centroids)
    mean = np.mean(centroids)
    return np.clip(centroids, a_min=mean-cutoff*2, a_max=mean+cutoff*2)

class TLE:
    def __init__(self, signal_object):#data_path, time_of_record, total_step, step_timelength
        time_scale = load.timescale()
        self.station_name = signal_object.station_data["name"]
        station_long = signal_object.station_data["longitude"]
        station_lat = signal_object.station_data["latitude"]
        station_alt = signal_object.station_data["altitude"]
        self.station = wgs84.latlon(station_lat, station_long, station_alt)
        self.satellite = EarthSatellite(signal_object.tle_data["line_1"], signal_object.tle_data["line_2"], signal_object.name, time_scale)
        self.time_of_record = signal_object.time_of_record.replace(tzinfo=utc)
        self.signal_time = [time_scale.utc(self.time_of_record + datetime.timedelta(seconds=step*signal_object.step_timelength)) for step in range(signal_object.total_step)]
        self.channel_frequencies = signal_object.channel_frequencies

    def Doppler_prediction(self, channel, steps):
        """
        function to calculated Doppler shift frequency from skyfield objects, ideas from https://en.wikipedia.org/wiki/Relativistic_Doppler_effect#Motion_in_an_arbitrary_direction
        """
        Doppler_freqs = np.empty_like(steps)
        relative = self.station - self.satellite
        for step in steps:
            r = relative.at(self.signal_time[step]).position.m
            v = relative.at(self.signal_time[step]).velocity.m_per_s
            beta = np.linalg.norm(v) / c
            gamma = 1 / np.sqrt(1 - beta**2)
            cos_theta = np.dot(r, v) / (np.linalg.norm(r) * np.linalg.norm(v))
            Doppler_freqs[step] = self.channel_frequencies[channel] / (gamma * (1 + beta * cos_theta))
        return Doppler_freqs



