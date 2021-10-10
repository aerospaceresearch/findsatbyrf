import matplotlib.pyplot as plt
import os
import csv, json
import numpy as np
import datetime
import soundfile
import tools
from datetime import datetime, timedelta
from argparse import ArgumentParser
# PATH=os.path.dirname(__file__)+'/'

class Metadata:
    """
        This class reads from CLI and stores metadata of the signal
    """
    def __init__(self):
        self.input_file = None
        self.info_file = None
        self.output_file = None
        self.channels = []
        self.tle_prediction = False
        self.time_step = 1.
        self.sensitivity = 1.
        self.time_begin = 0.
        self.filter_strength = 1.
        self.time_end = None
        self.samplerate = None
        self.raw_input = False

    def read_cli_arguments(self):
        parser = ArgumentParser()
        parser.add_argument("-f", "--input_file", type=str, action='store', metavar='wav/dat_file', help="The wav/dat wave signal file that needs to be analyzed", required= True)
        parser.add_argument("-i", "--input_signal_info", type=str, action='store', metavar='json_file', help="The json file containing the signal information", required=True)
        parser.add_argument("-o", "--output_file", type=str, action='store', metavar='name_of_output_file', help="Name of the output files without extension part", default="./output")
        parser.add_argument("-ch0", "--channel_0", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 0 (Hz)", default=None)
        parser.add_argument("-ch1", "--channel_1", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 1 (Hz)", default=None)
        parser.add_argument("-ch2", "--channel_2", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 2 (Hz)", default=None)
        parser.add_argument("-ch3", "--channel_3", type=float, action='store', metavar='frequency_in_Hz', help="Center frequency of channel 3 (Hz)", default=None)
        parser.add_argument("-bw0", "--bandwidth_0", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 0 (Hz)", default=None)
        parser.add_argument("-bw1", "--bandwidth_1", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 1 (Hz)", default=None)
        parser.add_argument("-bw2", "--bandwidth_2", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 2 (Hz)", default=None)
        parser.add_argument("-bw3", "--bandwidth_3", type=float, action='store', metavar='frequency_in_Hz', help="Bandwidth of channel 3 (Hz)", default=None)
        parser.add_argument("-step", "--time_step", type=float, action='store', metavar='time_in_second', help="Length of each time step in second", default=1.0)
        parser.add_argument("-sen", "--sensitivity", type=float, action='store', metavar='frequency_in_Hz', help="Length of bin step in second", default=1.0)
        parser.add_argument("-filter", "--filter_strength", type=float, action='store', metavar='ratio_to_1', help="Strength of the noise filter as ratio to 1.", default=1.0)
        parser.add_argument("-fs", "--samplerate", type=int, action='store', metavar='samples_per_second', help="Sampling rate of the file, will overwrite default samplerate, needed for RAW files.", default=None)
        parser.add_argument("-tle", "--tle_prediction", action='store_true', help="Use prediction from TLE", default=False)
        parser.add_argument("-begin", "--time_begin", type=float, action='store', metavar='time_in_second', help="Time of begin of the segment to be analyzed", default=0.)
        parser.add_argument("-end", "--time_end", type=float, action='store', metavar='time_in_second', help="Time of end of the segment to be analyzed", default=None)
        args = vars(parser.parse_args())
        self.input_file = os.path.abspath(args["input_file"])
        self.info_file = os.path.abspath(args["input_signal_info"])
        self.output_file = os.path.abspath(args["output_file"])
        self.time_step = args["time_step"]
        self.sensitivity = args["sensitivity"]
        self.tle_prediction = args["tle_prediction"]
        self.time_begin = args["time_begin"]
        self.time_end = args["time_end"]
        self.filter_strength = args["filter_strength"]
        self.samplerate = args["samplerate"]

        if type(args["channel_0"]) is float and type(args["bandwidth_0"]) is float:
            self.channels.append((args["channel_0"], args["bandwidth_0"]))
        if type(args["channel_1"]) is float and type(args["bandwidth_1"]) is float:
            self.channels.append((args["channel_1"], args["bandwidth_1"]))
        if type(args["channel_2"]) is float and type(args["bandwidth_2"]) is float:
            self.channels.append((args["channel_2"], args["bandwidth_2"]))
        if type(args["channel_3"]) is float and type(args["bandwidth_3"]) is float:
            self.channels.append((args["channel_3"], args["bandwidth_3"]))

        print(f"Reading signal information from {self.info_file}")
        if float(self.time_begin) == 0.:
            time_begin = "the beginning"
        elif float(self.time_begin) == 1.:
            time_begin = "1. second"
        else:
            time_begin = f"{self.time_begin} seconds"
        
        if float(self.time_step) == 1.:
            time_step = "1. second"
        else:
            time_step = f"{self.time_begin} seconds"

        if self.time_end == None:
            time_end = "the end"
        elif float(self.time_end) == 1.:
            time_end = "1. second"
        else:
            time_end = f"{self.time_step} seconds"

        print(f"Reading signal file from {self.input_file} from {time_begin} to {time_end} with time step of {time_step} and frequency bin of {self.sensitivity} Hertz.")

        if self.tle_prediction:
            print("Turned on signal center prediction based on TLE.")

    def read_info_file(self):
        with open(self.info_file) as f:
            json_data = json.load(f)
        self.signal_name = json_data["signal"]["name"]
        if "type" in json_data["signal"]:
            self.signal_type = json_data["signal"]["type"]
        else:
            self.signal_type = None
        self.signal_center_frequency = json_data["signal"]["center_frequency"]

        if "time_of_record" in json_data["signal"] or "timestamp_of_record" in json_data["signal"]:
            if "time_of_record" in json_data["signal"]:
                self.time_of_record = datetime.strptime(json_data["signal"]["time_of_record"], "%Y-%m-%dT%H:%M:%S.%fZ")

            if "timestamp_of_record" in json_data["signal"]:
                # preferred, even more prefeered in astropy format
                utc_time = datetime.utcfromtimestamp(json_data["signal"]["timestamp_of_record"])
                #utc_time = datetime.strftime("%Y-%m-%d %H:%M:%S.%f")
                self.time_of_record = utc_time
        else:
            self.time_of_record = datetime.now()

        if (self.samplerate is None) and ("samplerate" in json_data["signal"]):
            self.samplerate = json_data["signal"]["samplerate"]
        if self.samplerate is not None:
            print(f"You have provided samplerate = {self.samplerate}, make sure your input file is raw (.dat/.bin/.raw).")
            self.raw_input = True

        self.tle_data = None
        self.station_data = None
        try:
            if len(self.channels) == 0 and ("default_channel" in json_data):
                if len(json_data["default_channel"]) > 0:
                    for channel in json_data["default_channel"]:
                        self.channels.append((channel["frequency"], channel["bandwidth"]))
            else:
                raise Exception("Channel information must be provided in the CLI or in the json input file.")
        except Exception as error_message:
            print(error_message)
            raise

        try: 
            if "tle" in json_data:
                self.tle_data = json_data["tle"]
            elif self.tle_prediction:
                raise Exception("Tle information is not found in the json file")
        except Exception as error_message:
            print(error_message)
            raise

        try:
            if "station" in json_data:
                self.station_data = json_data["station"]
            elif self.tle_prediction:
                raise Exception("Station information is not found in the json file")
        except Exception as error_message:
            print(error_message)
            raise

def read_info_from_wav(wav_path, step_timelength, time_begin, time_end):
    """
        Reading info from wav files
    """
    with soundfile.SoundFile(wav_path, 'r') as f:
        fs= f.samplerate
        step_framelength = int(step_timelength * fs)
        max_step = int(f.frames / step_framelength) 
        if time_begin < 0:
            time_begin = 0
        if (time_end is None) or (time_end * fs > f.frames):
            time_end = f.frames/fs
    return fs, step_framelength, max_step, time_begin, time_end

def read_info_from_bin(bin_path, step_timelength, time_begin, time_end, samplerate):
    f = np.memmap(bin_path, offset=0)
    fs = samplerate
    step_framelength = int(step_timelength * fs)
    frames = len(f)
    max_step = int(frames / step_framelength / 2)
    if time_begin < 0:
        time_begin = 0
    if (time_end is None) or (time_end * fs > frames):
        time_end = frames/fs/2
    del f
    return fs, step_framelength, max_step, time_begin, time_end
  
def read_info_from_data_file(file_path, step_timelength, time_begin, time_end, raw_input, samplerate):
    """ 
        Detect if input is binary or wav then use the appropriate method
    """
    if raw_input:
        return read_info_from_bin(file_path, step_timelength, time_begin, time_end, samplerate)
    else:
        return read_info_from_wav(file_path, step_timelength, time_begin, time_end)
      
class WavReader:
    """
        Reading details of the wav file
    """
    def __init__(self, signal_object):
        frame_begin = int(signal_object.time_begin * signal_object.fs)
        self.step_framelength = signal_object.step_framelength
        self.reader = soundfile.SoundFile(signal_object.signal_path, 'r')
        self.reader.seek(frame_begin)
        self.step = 0

    def read_current_step(self):
        raw_time_data = self.reader.read(frames=self.step_framelength)
        return raw_time_data[:,0] + 1j * raw_time_data[:,1]

    def close(self):
        self.reader.close()

class BinReader:
    """
        Reading details of the binary file
    """
    def __init__(self, signal_object):
        self.frame_begin = int(signal_object.time_begin * signal_object.fs)
        self.step_framelength = signal_object.step_framelength
        self.reader = np.memmap(signal_object.signal_path, offset=0)
        self.step = 0

    def read_current_step(self):
        raw_time_data = self.reader[self.frame_begin + self.step_framelength * 2 * (self.step+0):
                                    self.frame_begin + self.step_framelength * 2 * (self.step+1)]
        return (-127.5 + raw_time_data[0::2]) + 1j * (-127.5 + raw_time_data[1::2]) ## only for 8bit rtlsdr

    def close(self):
        pass

class Csv:
    """
        Handling csv output
    """
    def __init__(self, signal_object):
        self.output_file = signal_object.output_file+".csv"
        self.file = open(self.output_file, 'w', newline='')
        self.reader = csv.writer(self.file)
        header = [f"date={signal_object.time_of_record.strftime('%Y-%m-%d')}"]
        for channel in range(signal_object.channel_count):
            header.append(f"CH_{channel}[Hz]={signal_object.channel_frequencies[channel]}")
        self.reader.writerow(header) 
        self.center_frequency = signal_object.center_frequency
        self.total_step = signal_object.total_step
        self.channel_count = signal_object.channel_count
        self.time_labels = [(signal_object.time_of_record + timedelta(seconds=step*signal_object.step_timelength)).strftime('%H:%M:%S.%f') for step in range(0, signal_object.total_step)]

    def save_all(self, centroids):
        for step in range(self.total_step):
            data = [self.time_labels[step]]
            for channel in range(self.channel_count):
                centroid = None if np.isnan(centroids[channel, step]) else centroids[channel, step] + self.center_frequency
                data.append(centroid)
            self.reader.writerow(data)            
    
    def export(self):
        self.file.close()
        print(f"Exported to {self.output_file} successfully.")

class Json:
    """
        Handling json output
    """
    def __init__(self, signal_object):
        self.output_file = signal_object.output_file+".json"
        self.file = open(self.output_file, 'w')
        self.data_to_dump = {}
        self.data_to_dump['header'] = {}
        self.data_to_dump['header']['name'] = signal_object.name
        self.data_to_dump['header']['date'] = signal_object.time_of_record.strftime('%Y-%m-%d')
        self.data_to_dump['header']['time_step[second]'] = signal_object.step_timelength
        for channel in range(signal_object.channel_count):
            self.data_to_dump['header'][f"ch_{channel}[Hz]"] = signal_object.channel_frequencies[channel]
        self.center_frequency = signal_object.center_frequency
        self.total_step = signal_object.total_step
        self.channel_count = signal_object.channel_count
        self.time_labels = [(signal_object.time_of_record + timedelta(seconds=step*signal_object.step_timelength)).strftime('%H:%M:%S.%f') for step in range(0, signal_object.total_step)]
        self.data_to_dump['signal_center'] = {}
        self.data_to_dump['signal_center']['label'] = "time[hh:mm:ss]: signal_center[Hz]"

    def save_all(self, centroids):
        for channel in range(self.channel_count):
            self.data_to_dump['signal_center'][f"ch_{channel}"] = {}
            for step in range(self.total_step):
                self.data_to_dump['signal_center'][f"ch_{channel}"][self.time_labels[step]] = None if np.isnan(centroids[channel, step]) else centroids[channel, step] + self.center_frequency
        json.dump(self.data_to_dump, self.file, indent=4)
    
    def export(self):
        self.file.close()
        print(f"Exported to {self.output_file} successfully.")

class Waterfall:
    """
        Handling png output
    """
    def __init__(self, signal_object, frequency_unit='kHz', tle_prediction=False):
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
            self.axs[channel].set_yticks(range(0, self.total_step+1, int(self.total_step/10)))
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
        self.save_path = signal_object.output_file

        self.tle_prediction = tle_prediction
        if self.tle_prediction:
            self.TLE = tools.TLE(signal_object) #.data_path, signal_object.time_of_record, signal_object.total_step, signal_object.step_timelength)
            self.fig.suptitle(f"Centroid positions: RED = calculated from wav, BLUE = predicted from TLE\n{signal_object.name} signal recorded at {self.TLE.station_name} station on {signal_object.time_of_record.strftime('%Y-%m-%d')}")
        else:
            self.fig.suptitle(f"Centroid positions calculated from wav\n{signal_object.name} signal recorded on {signal_object.time_of_record.strftime('%Y-%m-%d')}")

    def save_all(self, centroids):
        for channel in range(self.channel_count):   
            actual_calculation = centroids[channel] + self.center_frequency
            self.axs[channel].plot(actual_calculation * self.scale, range(self.total_step), '.', color='red', markersize = 1)
            if self.tle_prediction:
                prediction_from_TLE = self.TLE.Doppler_prediction(channel, range(self.total_step))
                self.axs[channel].plot(prediction_from_TLE * self.scale, range(self.total_step), '.', color='blue', markersize = 1)
                raw_error = (actual_calculation - prediction_from_TLE)
                actual_signal = ~np.isnan(raw_error)
                raw_error = raw_error[actual_signal]
                if len(raw_error)==0:
                    print("No signal is found for this channel")
                else:
                    standard_error = np.std(raw_error, ddof=1) / np.sqrt(np.size(raw_error))        
                    offset = np.mean(raw_error)            
                    print(f"Finished calculation for channel {channel}, Offset to prediction = {offset} Hz, Estimated true frequency = {self.channel_frequencies[channel] + offset} Hz, Standard error = {standard_error} Hz.")                  
            
            
    def export(self, format='png'):
        self.fig.savefig(f"{self.save_path}.{format}", dpi=300)
        plt.close(self.fig)
        print(f"Exported to {self.save_path}.{format} successfully.")
