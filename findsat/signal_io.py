from scipy import signal
from scipy.io import wavfile
import matplotlib.pyplot as plt
import os
import csv
import numpy as np
import datetime
import soundfile
import tools
from datetime import datetime, timedelta
PATH=os.path.dirname(__file__)+'/'

def read_info_from_wav(wav_path, step_timelength, time_begin, time_end):
    with soundfile.SoundFile(wav_path, 'r') as f:
        fs= f.samplerate
        step_framelength = int(step_timelength * fs)
        max_step = int(f.frames / step_framelength) 
        f.subtype
        if time_begin < 0:
            time_begin = 0
        if (time_end == None) or (time_end * fs > f.frames):
            time_end = f.frames/fs
    return fs, step_framelength, max_step, time_begin, time_end

class WavReader:
    def __init__(self, signal_object):
        frame_begin = int(signal_object.time_begin * signal_object.fs)
        self.step_framelength = signal_object.step_framelength
        self.reader = soundfile.SoundFile(signal_object.wav_path, 'r')
        self.reader.seek(frame_begin)
    def read_current_step(self):
        raw_time_data = self.reader.read(frames=self.step_framelength)
        return raw_time_data[:,0] + 1j * raw_time_data[:,1]
    def close(self):
        self.reader.close()

class CsvWriter:
    def __init__(self, signal_object, frequency_unit='kHz'):
        if frequency_unit.lower() == 'hz':
            self.scale = 1
        elif frequency_unit.lower() == 'mhz':
            self.scale = 1e-6
        else:
            self.scale = 1e-3                                    #Transform Hz to kHz
            frequency_unit = 'kHz'
        self.file = open(os.path.normpath(signal_object.data_path+f"{signal_object.name}_{signal_object.time_of_record.strftime('%Y-%m-%d')}.csv"), 'w', newline='')
        self.reader = csv.writer(self.file)
        header = [f"date={signal_object.time_of_record.strftime('%Y-%m-%d')}"]
        for channel in range(signal_object.channel_count):
            header.append(f"CH_{channel}[Hz]={signal_object.channel_frequencies[channel]}")
        self.reader.writerow(header) 
        self.center_frequency = signal_object.center_frequency
        self.total_step = signal_object.total_step
        self.channel_count = signal_object.channel_count
        self.time_labels = [(signal_object.time_of_record + timedelta(seconds=step*signal_object.step_timelength)).strftime('%H:%M:%S') for step in range(0, signal_object.total_step)]

    def save_step(self, step, centroids):
        data = [self.time_labels[step]]
        for channel in range(self.channel_count):
            data.append(centroids[channel])
        self.reader.writerow(data)

    def save_all(self, centroids):
        for step in range(self.total_step):
            data = [self.time_labels[step]]
            for channel in range(self.channel_count):
                data.append(self.scale * (centroids[channel, step] + self.center_frequency))
            self.reader.writerow(data)            
    
    def export(self):
        self.file.close()

class Waterfall:
    def __init__(self, signal_object, frequency_unit='kHz'):
        if frequency_unit.lower() == 'hz':
            self.scale = 1
        elif frequency_unit.lower() == 'mhz':
            self.scale = 1e-6
        else:
            self.scale = 1e-3                                    #Transform Hz to kHz
            frequency_unit = 'kHz'

        self.total_step = signal_object.total_step
        self.fig, self.axs = plt.subplots(nrows = signal_object.channel_count, figsize=(10,2+1.8*signal_object.channel_count))
        if signal_object.channel_count == 1:
            self.axs = [self.axs]
        time_labels = [(signal_object.time_of_record + timedelta(seconds=step*signal_object.step_timelength)).strftime('%H:%M:%S') for step in range(0, signal_object.total_step+1, int(signal_object.total_step/10))]
        for channel in range(signal_object.channel_count):
            self.axs[channel].set_yticks(range(0,self.total_step, int(self.total_step/10)))
            self.axs[channel].set_yticklabels(time_labels)
            self.axs[channel].grid()
            self.axs[channel].ticklabel_format(axis='x', useOffset=False)
            plot_area = int(signal_object.channel_bandwidths[channel] / 6)
            plot_tick = int(plot_area / 4)
            self.axs[channel].set_xlim([(signal_object.channel_frequencies[channel]-plot_area)*self.scale, (signal_object.channel_frequencies[channel]+plot_area)*self.scale])
            self.axs[channel].set_xticks(np.around(np.arange(signal_object.channel_frequencies[channel]-plot_area, signal_object.channel_frequencies[channel]+plot_area+plot_tick, plot_tick)*self.scale,decimals=1))
            self.axs[channel].set_ylabel("Time in UTC")

        #self.fig.tight_layout()
        self.channel_count = signal_object.channel_count
        self.center_frequency = signal_object.center_frequency
        self.channel_frequencies = signal_object.channel_frequencies
        self.TLE = tools.TLE(signal_object) #.data_path, signal_object.time_of_record, signal_object.total_step, signal_object.step_timelength)
        self.fig.suptitle(f"Centroid positions: RED = calculated from wav, BLUE = predicted from TLE\n{signal_object.name} signal recorded at {self.TLE.station_name} station on {signal_object.time_of_record.strftime('%Y-%m-%d')}")
        self.axs[-1].set_xlabel(f"Frequency [{frequency_unit}]")
        self.save_path = os.path.normpath(signal_object.data_path+f"{signal_object.name}_{signal_object.time_of_record.strftime('%Y-%m-%d')}")

    def save_step(self, step, centroids, show_prediction=True):
        for channel in range(self.channel_count):
            if show_prediction:
                prediction_from_TLE = self.scale * self.TLE.Doppler_prediction(channel, step)
                self.axs[channel].plot(prediction_from_TLE, step, '.', color='blue', markersize = 0.5)
            centroid = self.scale * (centroids[channel] + self.center_frequency)
            self.axs[channel].plot(centroid, step, '.', color='red', markersize = 0.5)

    def save_all(self, centroids, show_prediction=True):
        for channel in range(self.channel_count):
            if show_prediction:
                prediction_from_TLE = self.scale * self.TLE.Doppler_prediction(channel, range(self.total_step))
                self.axs[channel].plot(prediction_from_TLE, range(self.total_step), '.', color='blue', markersize = 0.5)
            self.axs[channel].plot(self.scale * (centroids[channel] + self.center_frequency), range(self.total_step), '.', color='red', markersize = 0.5)

    def export(self, format='png'):
        self.fig.savefig(f"{self.save_path}.{format}", dpi=300)
        plt.close(self.fig)

