import numpy as np
import tools
import signal_io as io
from datetime import datetime

class Signal:
    def __init__(self, metadata=None):
        try:
            if metadata is None:
                raise Exception("Loading initial input data from command-line and/or json failed")
        except Exception as error_message:
            print(error_message)
            raise      
        if metadata.signal_type is None:
            self.type = 'general'
        elif metadata.signal_type.lower() == 'noaa':
            self.type = 'NOAA'
        else:
            self.type = 'general'
        self.name = metadata.signal_name
        self.signal_path = metadata.input_file
        self.output_file = metadata.output_file
        self.center_frequency = metadata.signal_center_frequency
        self.time_of_record = metadata.time_of_record

        self.channels = metadata.channels
        self.channel_frequencies = []
        self.bandwidth_indices = []
        self.full_freq_domain = []
        self.avg_freq_domain = []
        self.channel_bandwidths = []
        self.channel_freq_domain_len = []
        self.resolutions = []
        self.channel_count = 0
        self.sensitivity = metadata.sensitivity
        self.step_timelength = metadata.time_step
        self.filter_strength = metadata.filter_strength
        self.raw_input = metadata.raw_input
        self.unit = metadata.unit

        (self.fs,
        self.step_framelength, 
        self.max_step, 
        self.time_begin, 
        self.time_end) = io.read_info_from_data_file(
                            self.signal_path, 
                            self.step_timelength, 
                            metadata.time_begin, 
                            metadata.time_end,
                            self.raw_input,
                            metadata.samplerate)

        self.full_freq = np.fft.fftfreq(int(self.fs * self.step_timelength), 1/(self.fs))
        self.total_step = int((self.time_end-self.time_begin)/self.step_timelength)
        
        self.tle_prediction = metadata.tle_prediction
        self.tle_data = metadata.tle_data
        self.station_data = metadata.station_data

    def add_channel(self, channel_frequency, channel_bandwidth):
        self.channel_frequencies.append(channel_frequency)
        self.channel_bandwidths.append(channel_bandwidth)
        self.resolutions.append(int(channel_bandwidth/self.sensitivity))
        bandwidth_index = np.where(np.logical_and(self.full_freq > channel_frequency - self.center_frequency - channel_bandwidth/2, self.full_freq < channel_frequency - self.center_frequency + channel_bandwidth/2))
        self.bandwidth_indices.append(bandwidth_index)
        self.full_freq_domain.append(self.full_freq[bandwidth_index])
        self.avg_freq_domain.append(tools.avg_binning(self.full_freq[bandwidth_index], int(channel_bandwidth/self.sensitivity)))
        self.channel_freq_domain_len.append(len(bandwidth_index))
        print(f"Added channel {self.channel_count}: frequency = {channel_frequency} Hz, bandwidth = {channel_bandwidth} Hz")
        self.channel_count += 1

    def find_centroids(self, peak_finding_range=None):
        self.centroids = np.empty((self.channel_count, self.total_step))

        if self.raw_input:
            reader = io.BinReader(self)
        else:
            reader = io.WavReader(self)

        for step in range(self.total_step):
            print(f"Processing data... {step/self.total_step*100:.2f}%", end='\r')
            reader.step = step
            time_data = reader.read_current_step()

            raw_freq_kernel = np.abs(np.fft.fft(time_data))
            for channel in range(self.channel_count):
                channel_kernel = 20 * np.log10(raw_freq_kernel[self.bandwidth_indices[channel]])
                avg_mag = tools.avg_binning(channel_kernel, self.resolutions[channel])   
                noise_offset = tools.calculate_offset(avg_mag, self.filter_strength)   
                avg_mag += noise_offset
                filtered_mag = np.clip(avg_mag, a_min=0., a_max=None)
                centroid = tools.centroid(self.avg_freq_domain[channel], filtered_mag)
                if peak_finding_range is not None:
                    centroid = tools.peak_finding(self.avg_freq_domain[channel], filtered_mag, centroid, peak_finding_range)
                self.centroids[channel, step] = centroid
        reader.close()

    def export(self, filter=False):
        if filter:   
            for channel in range(self.channel_count):
                self.centroids[channel] = tools.lowpass_filter(self.centroids[channel], self.step_timelength)
        try:
            waterfall = io.Waterfall(self, frequency_unit=self.unit, tle_prediction = self.tle_prediction)
            waterfall.save_all(self.centroids)
            waterfall.export()
        except Exception as error:
            print("Failed to create center vs time graph output")
            print(error)
        try:
            csv = io.Csv(self)
            csv.save_all(self.centroids)
            csv.export()
        except Exception as error:
            print("Failed to create csv output")
            print(error)
        try:
            json = io.Json(self)
            json.save_all(self.centroids)
            json.export()
        except Exception as error:
            print("Failed to create json output")
            print(error)
        print(f"Processing data... 100.00%", end='\r\n')

    def process(self, default=True, filter=False, peak_finding_range=None):
        """
            set filter to True to smoothen the output centroid curve, however the result is not good (for now) therefore it is not recommended to use.
        """
        for channel in self.channels:
            self.add_channel(channel[0], channel[1])
        if default:
            if self.type == 'NOAA':
                self.find_centroids(peak_finding_range = 1000)
                self.export(filter=filter)
            elif self.type == 'general':
                self.find_centroids()
                self.export(filter=filter)
        else:
            self.find_centroids(peak_finding_range=peak_finding_range)
            self.export(filter=filter)







