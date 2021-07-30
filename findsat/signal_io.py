from scipy import signal
from scipy.io import wavfile
import matplotlib.pyplot as plt
import os
import csv
import numpy as np
import datetime
import soundfile
import tools
from datetime import datetime, time, timedelta
from argparse import ArgumentParser
PATH=os.path.dirname(__file__)+'/'

def read_cli_arguments():
    parser = ArgumentParser()
    parser.add_argument("-i", "--input_folder", type=str, action='store', metavar='folder', help="Name of the folder containing all the data", default="data")
    parser.add_argument("-ch1", "--channel_1", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 1 (Hz)", default=None)
    parser.add_argument("-ch2", "--channel_2", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 2 (Hz)", default=None)
    parser.add_argument("-ch3", "--channel_3", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 3 (Hz)", default=None)
    parser.add_argument("-ch4", "--channel_4", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 4 (Hz)", default=None)
    parser.add_argument("-bw1", "--bandwidth_1", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 1 (Hz)", default=None)
    parser.add_argument("-bw2", "--bandwidth_2", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 2 (Hz)", default=None)
    parser.add_argument("-bw3", "--bandwidth_3", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 3 (Hz)", default=None)
    parser.add_argument("-bw4", "--bandwidth_4", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 4 (Hz)", default=None)
    parser.add_argument("-step", "--time_step", type=float, action='store', metavar='time_in_second', help="Length of each time step in second", default=1.0)
    parser.add_argument("-sen", "--sensitivity", type=float, action='store', metavar='frequency_in_Hz', help="Length of each time step in second", default=1.0)
    parser.add_argument("-tle", "--tle_prediction", action='store_true', help="Use prediction from TLE", default=False)
    parser.add_argument("-begin", "--time_begin", type=float, action='store', metavar='time_in_second', help="Time of begin of the segment to be analyzed", default=0)
    parser.add_argument("-end", "--time_end", type=float, action='store', metavar='time_in_second', help="Time of end of the segment to be analyzed", default=None)
    args = vars(parser.parse_args())
    channels = []
    if args["channel_1"] != None and args["bandwidth_1"] != None:
        channels.append((args["channel_1"], args["bandwidth_1"]))
    if args["channel_2"] != None and args["bandwidth_2"] != None:
        channels.append((args["channel_2"], args["bandwidth_2"]))
    if args["channel_3"] != None and args["bandwidth_3"] != None:
        channels.append((args["channel_3"], args["bandwidth_3"]))
    if args["channel_4"] != None and args["bandwidth_4"] != None:
        channels.append((args["channel_4"], args["bandwidth_4"]))
    return args["input_folder"], args["time_step"], args["sensitivity"], args["tle_prediction"], args["time_begin"], args["time_end"], channels

def read_input_folder(folder):
    name = 'Unknown'
    type = 'general'
    center_frequency = 0.
    time_of_record = None
    with open(os.path.normpath(folder+"/signal_info.txt"), "r") as f:
            for _ in range(4):
                input_string = f.readline().replace(" ","").strip("\n").split("=")
                if 'name' in input_string[0].lower():
                    name = input_string[1]
                elif 'type' in input_string[0].lower():
                    type = input_string[1]
                elif 'freq' in input_string[0].lower():
                    center_frequency = float(input_string[1])
                elif 'time' in input_string[0].lower():
                    time_of_record = input_string[1]
    return name, type, center_frequency, time_of_record


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

class Csv:
    def __init__(self, signal_object, frequency_unit='kHz', type='w'):
        if frequency_unit.lower() == 'hz':
            self.scale = 1
        elif frequency_unit.lower() == 'mhz':
            self.scale = 1e-6
        else:
            self.scale = 1e-3                                    #Transform Hz to kHz
            frequency_unit = 'kHz'
        self.file_name = f"{signal_object.name}_{signal_object.time_of_record.strftime('%Y-%m-%d')}.csv"
        os.path.normpath(signal_object.data_path+f"{signal_object.name}_{signal_object.time_of_record.strftime('%Y-%m-%d')}.csv")
        self.file = open(os.path.normpath(signal_object.data_path + self.file_name), type, newline='')
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
    
    def read_file(self):
        pass
    def export(self):
        self.file.close()
        print(f"Exported to {self.file_name}")

class Waterfall:
    def __init__(self, signal_object, frequency_unit='kHz', TLE_prediction=False):
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
        self.axs[-1].set_xlabel(f"Frequency [{frequency_unit}]")
        self.file_name = f"{signal_object.name}"
        self.save_path = os.path.normpath(signal_object.data_path + self.file_name)

        self.TLE_prediction = TLE_prediction
        if self.TLE_prediction:
            self.TLE = tools.TLE(signal_object) #.data_path, signal_object.time_of_record, signal_object.total_step, signal_object.step_timelength)
            self.fig.suptitle(f"Centroid positions: RED = calculated from wav, BLUE = predicted from TLE\n{signal_object.name} signal recorded at {self.TLE.station_name} station on {signal_object.time_of_record.strftime('%Y-%m-%d')}")
        else:
            self.fig.suptitle(f"Centroid positions calculated from wav\n{signal_object.name} signal recorded on {signal_object.time_of_record.strftime('%Y-%m-%d')}")


    def save_all(self, centroids):
        for channel in range(self.channel_count):   
            actual_calculation = self.scale * (centroids[channel] + self.center_frequency)
            if self.TLE_prediction:
                prediction_from_TLE = self.scale * self.TLE.Doppler_prediction(channel, range(self.total_step))
                self.axs[channel].plot(prediction_from_TLE, range(self.total_step), '.', color='blue', markersize = 0.5)
                raw_error = actual_calculation - prediction_from_TLE 
                temporal_noise = np.std(raw_error[~np.isnan(raw_error)])
                for index, error in enumerate(raw_error):
                    if not np.isnan(error) and np.abs(error) > 2*temporal_noise:
                        actual_calculation[index] = np.nan
                raw_error = actual_calculation - prediction_from_TLE 
                raw_error = raw_error[~np.isnan(raw_error)]
                standard_error = np.std(raw_error) / np.sqrt(np.size(raw_error))
                print(f"Finished calculation for channel {channel}, Standard Error = {standard_error/self.scale} Hz")
            self.axs[channel].plot(actual_calculation, range(self.total_step), '.', color='red', markersize = 0.5)
            

    def export(self, format='png'):
        self.fig.savefig(f"{self.save_path}.{format}", dpi=300)
        plt.close(self.fig)
        print(f"Exported to {self.file_name}.{format}")

