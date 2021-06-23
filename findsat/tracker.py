import numpy as np
import tools
import signal_io as io
import tle_processing as tle
import multiprocessing
import glob
import matplotlib.pyplot as plt
import soundfile as sf
from datetime import datetime, timedelta

class signal:
    def __init__(self, name='Unknown',
            data_path='data',
            center_frequency = None,
            expected_frequency = None,
            bandWidth = None,
            step_timelength = None,
            resolution = None,
            sensitivity = None,
            pass_bandwidth = None,
            time_of_record = None):

        self.name = name
        self.safety = 0.5
        self.channel_frequencies = []
        self.bandwidth_indices = []
        self.full_freq_domain = []
        self.avg_freq_domain = []
        self.channel_bandwidths = []
        self.channel_freq_domain_len = []
        self.resolutions = []
        self.data_path = io.PATH + data_path
        self.channel_count = 0

        if expected_frequency == None:
            self.expected_frequency = 0
        else:
            self.expected_frequency = expected_frequency

        if resolution  == None:
            self.resolution = 2400
        else:
            self.resolution = resolution

        # if bandWidth == None:
            # self.bandWidth = 60e3
        # else:
            # self.bandWidth = bandWidth

        # self.sensitivity = int(self.bandWidth/self.resolution)

        if sensitivity != None:
            self.sensitivity = sensitivity

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
        self.wav_path = glob.glob(self.data_path+'/*.wav')[0]
        self.fs, self.step_framelength, self.max_step, self.time_begin, self.time_end = io.read_info_from_wav(self.wav_path, self.step_timelength, time_begin, time_end)
        self.full_freq = np.fft.fftfreq(int(self.fs * self.step_timelength), 1/(self.fs))
        self.total_step = int((self.time_end-self.time_begin)/self.step_timelength)


    def read_data_from_wav(self):
        io.read_data_from_wav(self.wav_path, self.fs, self.step_timelength, self.step_framelength, self.time_begin, self.time_end, self.time_data)

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

    def initializing(self):
        self.time_data = np.zeros((self.step_framelength))                                                #time domain at each step
        self.freq_data = np.empty((channel_count, len(max(self.bandwidth_indices, key=len))))            #frequency domain at each step for channel_count channels.
        self.centroids = np.empty((channel_count))

    def draw_output(self):
        time_data = np.zeros((self.step_framelength))                                                #time domain at each step
        # freq_data = np.empty((channel_count, len(max(self.bandwidth_indices, key=len))))            #frequency domain at each step for channel_count channels.
        raw_freq_kernel = np.zeros((self.step_framelength))
        centroids = np.empty((self.channel_count))
        frame_begin = int(self.time_begin*self.fs)
        frame_end = frame_begin + int( int((self.time_end - self.time_begin) / self.step_timelength) * self.step_timelength * self.fs)

        scale = 1e-3                                    #Transform Hz to kHz
        fig, axs = plt.subplots(nrows = self.channel_count, figsize=(10,2+1.8*self.channel_count))
        if self.channel_count == 1:
            axs = [axs]
        times = [(self.time_of_record + timedelta(seconds=step*self.step_timelength)).strftime('%H:%M:%S') for step in range(0, self.total_step+1, int(self.total_step/10))]
        TLE = tle.TLEprediction(self.data_path, self.time_of_record, self.total_step, self.step_timelength)
        

        for channel in range(self.channel_count):
            axs[channel].set_yticks(range(0,self.total_step, int(self.total_step/10)))
            axs[channel].set_yticklabels(times)
            axs[channel].grid()
            axs[channel].ticklabel_format(axis='x', useOffset=False)
            plot_area = int(self.channel_bandwidths[channel] / 6)
            plot_tick = int(plot_area / 4)
            axs[channel].set_xlim([(self.channel_frequencies[channel]-plot_area)*scale, (self.channel_frequencies[channel]+plot_area)*scale])
            axs[channel].set_xticks(np.around(np.arange(self.channel_frequencies[channel]-plot_area, self.channel_frequencies[channel]+plot_area+plot_tick, plot_tick)*scale,decimals=1))
            axs[channel].set_ylabel("Time in UTC")
        plt.suptitle(f"Centroid positions: Red = calculated from wav, Green = predicted from TLE\n{self.name} signal recorded at {TLE.station_name} station on {self.time_of_record.strftime('%Y-%m-%d')}")
        axs[-1].set_xlabel("Frequency [kHz]")

        with sf.SoundFile(self.wav_path, 'r') as f:
            f.seek(frame_begin)
            step = -1
            while f.tell() < frame_end:
                step += 1
                print(f"Processing data... {step/self.total_step*100:.2f}%", end='\r')
                raw_time_data = f.read(frames=self.step_framelength)
                time_data = raw_time_data[:,0] + 1j * raw_time_data[:,1]
                #local_signal *= np.hanning(self.step_framelength)
                raw_freq_kernel = np.abs(np.fft.fft(time_data))
                for channel in range(self.channel_count):
                    channel_kernel = 20 * np.log10(raw_freq_kernel[self.bandwidth_indices[channel]])
                    safety_factor = 0
                    avg_mag = tools.avg_binning(channel_kernel, self.resolutions[channel])   
                    noise_offset = tools.calculate_offset(avg_mag)   
                    avg_mag += noise_offset + safety_factor
                    filtered_mag = np.clip(avg_mag, a_min=0., a_max=None)
                    tools.channel_filter(filtered_mag, self.resolutions[channel], pass_step_width = int(self.pass_bandwidth / self.channel_bandwidths[channel] * self.resolutions[channel]))
                    centroid = tools.centroid(self.avg_freq_domain[channel], filtered_mag)
                    if centroid != None:
                        centroid = scale * (centroid + self.center_frequency)

                    prediction_from_TLE = scale * TLE.Doppler_prediction(self.channel_frequencies[channel], step)
                    axs[channel].plot(prediction_from_TLE, step, '.', color='green', markersize = 0.2)
                    if centroid != None:
                        axs[channel].plot(centroid, step, '.', color='red', markersize = 0.2)
            plt.savefig(f"{io.PATH}/data/Waterfall_{self.name}_{self.time_of_record.strftime('%Y-%m-%d')}.png", dpi=300)
            print(f"Processing data... 100.00%", end='\r\n')

    def plot(self):
        io.waterfall(self)




