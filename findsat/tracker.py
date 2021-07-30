import numpy as np
import tools
import signal_io as io
import glob
from datetime import datetime

class Signal:
    def __init__(self, data_path = 'data', sensitivity = 1.0, step_timelength = 1.0):
        self.data_path = io.PATH + data_path + "/"
        self.name, type, self.center_frequency, time_of_record =  io.read_input_folder(self.data_path)
        if type.lower() == 'noaa':
            self.type = 'NOAA'
        else:
            self.type = 'general'
        self.time_of_record = datetime.strptime(time_of_record, "%Y-%m-%dT%H:%M:%SZ")

        self.channel_frequencies = []
        self.bandwidth_indices = []
        self.full_freq_domain = []
        self.avg_freq_domain = []
        self.channel_bandwidths = []
        self.channel_freq_domain_len = []
        self.resolutions = []
        self.channel_count = 0
        self.sensitivity = sensitivity
        self.step_timelength = step_timelength
        # if time_of_record == None:
        #     self.time_of_record = datetime.strptime("2021-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        # else:
        if type.lower() == 'noaa':
            self.type = 'NOAA'
        else:
            self.type = 'general'

    def read_info_from_wav(self, time_begin=0, time_end=None):
        self.wav_path = glob.glob(self.data_path+'*.wav')[0]
        self.fs, self.step_framelength, self.max_step, self.time_begin, self.time_end = io.read_info_from_wav(self.wav_path, self.step_timelength, time_begin, time_end)
        self.full_freq = np.fft.fftfreq(int(self.fs * self.step_timelength), 1/(self.fs))
        self.total_step = int((self.time_end-self.time_begin)/self.step_timelength)

    def add_channel(self, channel_frequency, channel_bandwidth):
        self.channel_frequencies.append(channel_frequency)
        self.channel_count += 1
        self.channel_bandwidths.append(channel_bandwidth)
        self.resolutions.append(int(channel_bandwidth/self.sensitivity))
        bandwidth_index = np.where(np.logical_and(self.full_freq > channel_frequency - self.center_frequency - channel_bandwidth/2, self.full_freq < channel_frequency - self.center_frequency + channel_bandwidth/2))
        self.bandwidth_indices.append(bandwidth_index)
        self.full_freq_domain.append(self.full_freq[bandwidth_index])
        self.avg_freq_domain.append(tools.avg_binning(self.full_freq[bandwidth_index], int(channel_bandwidth/self.sensitivity)))
        self.channel_freq_domain_len.append(len(bandwidth_index))

    def find_centroids(self, peak_finding_range=None, safety_factor = 0.):
        self.centroids = np.empty((self.channel_count, self.total_step))
        reader = io.WavReader(self)
        for step in range(self.total_step):
            print(f"Processing data... {step/self.total_step*100:.2f}%", end='\r')
            time_data = reader.read_current_step()              # * np.hanning(self.step_framelength)
            raw_freq_kernel = np.abs(np.fft.fft(time_data))
            for channel in range(self.channel_count):
                channel_kernel = 20 * np.log10(raw_freq_kernel[self.bandwidth_indices[channel]])
                avg_mag = tools.avg_binning(channel_kernel, self.resolutions[channel])   
                noise_offset = tools.calculate_offset(avg_mag)   
                avg_mag += noise_offset
                if safety_factor != 0.:
                    avg_mag -= np.max(avg_mag) * safety_factor
                filtered_mag = np.clip(avg_mag, a_min=0., a_max=None)
                centroid = tools.centroid(self.avg_freq_domain[channel], filtered_mag)
                if peak_finding_range != None:
                    centroid = tools.peak_finding(self.avg_freq_domain[channel], filtered_mag, centroid, peak_finding_range)
                self.centroids[channel, step] = centroid
        reader.close()

    def export(self, filter=False, TLE_prediction=False):
        waterfall = io.Waterfall(self, TLE_prediction=TLE_prediction)
        csv = io.Csv(self)
        if filter:   
            for channel in range(self.channel_count):
                self.centroids[channel] = tools.lowpass_filter(self.centroids[channel], self.step_timelength)
        waterfall.save_all(self.centroids)
        csv.save_all(self.centroids)
        waterfall.export()
        csv.export()
        print(f"Processing data... 100.00%", end='\r\n')

    def process(self, default=True, TLE_prediction=False, filter=False, peak_finding_range=None, safety_factor = 0.):
        if default:
            if self.type == 'NOAA':
                self.find_centroids(peak_finding_range = 1000)
                self.export(filter=filter, TLE_prediction=TLE_prediction)
            elif self.type == 'general':
                self.find_centroids()
                self.export(filter=filter, TLE_prediction=TLE_prediction)
        else:
            self.find_centroids(peak_finding_range=peak_finding_range, safety_factor=safety_factor)
            self.export(filter=filter, TLE_prediction=TLE_prediction)







