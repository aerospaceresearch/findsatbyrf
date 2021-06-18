import numpy as np
import tools
import signal_io as io
import tle_processing as tle
import multiprocessing
import glob
from datetime import datetime

class signal:
    def __init__(self, name='Unknown',
            data_path='data',
            center_frequency = None,
            expected_frequency = None,
            bandWidth = None,
            step_timelength = None,
            resolution = None,
            pass_bandwidth = None,
            time_of_record = None):

        self.name = name
        self.safety = 0.5
        self.channel_frequencies = []
        self.bandwidth_indices = []
        self.full_freq_domain = []
        self.avg_freq_domain = []
        self.channel_bandwidths = []
        self.data_path = data_path
        self.time_data = multiprocessing.Queue()
        self.freq_data = multiprocessing.Queue()
        self.channel_count = 0

        if expected_frequency == None:
            self.expected_frequency = 0
        else:
            self.expected_frequency = expected_frequency

        if resolution  == None:
            self.resolution = 512
        else:
            self.resolution = resolution

        if bandWidth == None:
            self.bandWidth = 30e3
        else:
            self.bandWidth = bandWidth

        self.sensitivity = int(self.bandWidth/self.resolution)

        if center_frequency == None:
            self.center_frequency = 0
        else:
            self.center_frequency = center_frequency

        if step_timelength == None:
            self.step_timelength = 1.
        else:
            self.step_timelength = step_timelength

        if pass_bandwidth == None:
            self.pass_bandwidth = 1000
        else:
            self.pass_bandwidth = pass_bandwidth

        if time_of_record == None:
            self.time_of_record = 0
        else:
            self.time_of_record = datetime.strptime(time_of_record, "%Y-%m-%d %H:%M:%S")

    def read_info_from_wav(self, time_begin=0, time_end=None):
        self.wav_path = glob.glob(io.PATH+self.data_path+'/*.wav')[0]
        self.fs, self.step_framelength, self.max_step, self.time_begin, self.time_end = io.read_info_from_wav(self.wav_path, self.step_timelength, time_begin, time_end)
        self.full_freq = np.fft.fftfreq(int(self.fs * self.step_timelength), 1/(self.fs))
        self.total_step = int((self.time_end-self.time_begin)/self.step_timelength)


    def read_data_from_wav(self):
        io.read_data_from_wav(self.wav_path, self.fs, self.step_timelength, self.step_framelength, self.time_begin, self.time_end, self.time_data)

    def add_channel(self, channel_frequency, channel_bandwidth):
        self.channel_frequencies.append(channel_frequency)
        self.channel_count += 1
        self.channel_bandwidths.append(channel_bandwidth)
        bandwidth_index = np.where(np.logical_and(self.full_freq > channel_frequency - self.center_frequency - channel_bandwidth/2, self.full_freq < channel_frequency - self.center_frequency + channel_bandwidth/2))
        self.bandwidth_indices.append(bandwidth_index)
        self.full_freq_domain.append(self.full_freq[bandwidth_index])
        self.avg_freq_domain.append(tools.avg_binning(self.full_freq[bandwidth_index], self.resolution))

    def find_centroids(self):
        while True:
            centroids = []
            channel_kernels = []
            queue_output = self.time_data.get()
            if queue_output == None:
                self.time_data.put(None)
                break
            step, local_signal = queue_output
            local_signal *= np.hanning(self.step_framelength)
            raw_kernel = np.abs(np.fft.fft(local_signal))
            for channel in range(self.channel_count):
                channel_kernel = 20 * np.log10(raw_kernel[self.bandwidth_indices[channel]])
                safety_factor = 0
                avg_mag = tools.avg_binning(channel_kernel, self.resolution)   
                # if int(step * self.step_timelength) % 10 == 0:
                noise_offset = tools.calculate_offset(avg_mag)   
                avg_mag += noise_offset + safety_factor
                filtered_mag = np.clip(avg_mag, a_min=0., a_max=None)
                tools.channel_filter(filtered_mag, self.resolution, pass_step_width = int(self.pass_bandwidth / self.bandWidth * self.resolution))
                centroid = tools.centroid(self.avg_freq_domain[channel], filtered_mag)
                centroids.append(centroid)
                # channel_kernels.append(channel_kernel)
                channel_kernels.append(filtered_mag)
            self.freq_data.put((step, centroids, channel_kernels))
            # print(channel_kernels)
        
        self.freq_data.put('END')

    def Doppler_freqs_from_TLE(self, channel):
        freqs_from_TLE = tle.TLEprediction(self.data_path, self.time_of_record, self.total_step, self.step_timelength)
        return freqs_from_TLE.satellite.name, freqs_from_TLE.station_name, freqs_from_TLE.Doppler_prediction(self.channel_frequencies[channel])

    def plot(self):
        io.waterfall(self)




