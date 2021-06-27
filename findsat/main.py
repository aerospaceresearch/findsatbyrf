import tracker
#import rtlsdr
from datetime import datetime

def main():
    print("Initializing... ", end="")
    signal = tracker.Signal(name = 'UnknownNOAA',                   #name of the signal
                            data_path = 'data',                     #path to the data-containing folder from the findsat folder
                            center_frequency = 137.5e6,             #center frequency of the wave file
                            sensitivity= 100,                       #width of each bin in Hz            
                            step_timelength = 1.,                   #length of each time step in second
                            pass_bandwidth=5e3,                     #minimum width of a peak in waterfall to not be considered a noise
                            time_of_record = '2021-06-04 20:17:05') #time in UTC
    
    signal.read_info_from_wav(time_end=60)          #unit of second, set time_end to None to analyze the entire wave file
    signal.add_channel(channel_frequency=137.9125e6, channel_bandwidth=60e3)
    print("Done")

    start_time = datetime.now()
    signal.process()
    print(f"Finished in {datetime.now() - start_time}")        

if __name__ == '__main__':
    main()


