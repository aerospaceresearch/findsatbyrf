import tracker
#import rtlsdr
import multiprocessing
from datetime import datetime

if __name__ == '__main__':
    print("Initializing... ", end="")
    signal = tracker.signal(
            name = 'UnknownNOAA',                   #name of the signal
            data_path = 'data',                     #path to the data-containing folder from the findsat folder
            center_frequency = 137.5e6,             #center frequency of the wave file
            # expected_frequency = 137.9125e6,        #the original frequency of the satellite that you expect to get
            bandWidth = 60e3,                       #bandwidth of the part of the signal needed to analyze
            step_timelength = 1.,                   #length of each time step in second
            pass_bandwidth=5e3,                     #minimum width of a peak in waterfall to not be considered a noise
            time_of_record = '2021-06-04 20:17:04') #time in UTC


    print("Done")

    signal.read_info_from_wav(time_end=None)  #unit of second, set time_end to None to analyze the entire wave file
    signal.add_channel(channel_frequency=137.9125e6, channel_bandwidth=60e3)
    signal.add_channel(channel_frequency=138.035e6, channel_bandwidth=60e3)
    start_time = datetime.now()

    reading_process = multiprocessing.Process(target=signal.read_data_from_wav)
    calculating_process = multiprocessing.Process(target=signal.find_centroids)
    plotting_process = multiprocessing.Process(target=signal.plot)

    reading_process.start()
    calculating_process.start()
    plotting_process.start()

    reading_process.join()
    calculating_process.join()
    plotting_process.join()

    print(f"Finished in {datetime.now() - start_time}")


