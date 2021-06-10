from skyfield.api import load, wgs84, utc
from scipy.constants import c
import numpy as np
import datetime

time_scale = load.timescale()

def doppler_calculator(original_freq, station, satellite, time):
    """
    function to calculated Doppler shift frequency from skyfield objects, ideas from https://en.wikipedia.org/wiki/Relativistic_Doppler_effect#Motion_in_an_arbitrary_direction
    """
    relative = station - satellite
    r = relative.at(time).position.m
    v = relative.at(time).velocity.m_per_s
    beta = np.linalg.norm(v) / c
    gamma = 1 / np.sqrt(1 - beta**2)
    cos_theta = np.dot(r, v) / (np.linalg.norm(r) * np.linalg.norm(v))
    return original_freq / (gamma * (1 + beta * cos_theta))
    
class TLEprediction:
    def __init__(self, data_path, time_of_record, total_step, step_timelength):
        with open(data_path+"/station.txt", "r") as f:
            for _ in range(4):
                input_string = f.readline().replace(" ","").strip("\n").split("=")
                if input_string[0] == 'name':
                    self.station_name = input_string[1]
                elif input_string[0] == 'long':
                    station_long = float(input_string[1])
                elif input_string[0] == 'lat':
                    station_lat = float(input_string[1])
                elif input_string[0] == 'alt':
                    station_alt = float(input_string[1])
        self.station = wgs84.latlon(station_long, station_lat, station_alt)
        self.satellite = load.tle_file(data_path+"/satellite.tle")[0]
        self.time_of_record = time_of_record.replace(tzinfo=utc)
        self.signal_time = [time_scale.utc(self.time_of_record + datetime.timedelta(seconds=step*step_timelength)) for step in range(total_step)]

    def Doppler_prediction(self, center_freq):
        return np.array([doppler_calculator(center_freq, self.station, self.satellite, self.signal_time[step]) for step in range(len(self.signal_time))])
