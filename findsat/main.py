import tracker
from datetime import datetime

def main(debug_mode=False):
    if debug_mode:
        import warnings
        warnings.filterwarnings('error')
        print("Debug mode: ON")
    print("Initializing... ", end="")
    signal = tracker.Signal(
        name = 'UnknownNOAA',                   #name of the signal
        type = 'NOAA',                          #type of the signal, for example: 'NOAA', 'general'
        data_path = 'data',                     #path to the data-containing folder from the findsat folder, defaults to 'data'
        center_frequency = 137.5e6,             #center frequency of the wave file in Hz, defaults to 0
        sensitivity = 1.,                       #the sensitive-ness of the program in Hz, defaults to 10.
        step_timelength = 1.,                   #length of each time step in second, defaults to 1
        time_of_record = '2021-06-04 20:17:05'  #time in UTC, if set to None, datetime.now() will be used
        ) 
    
    signal.read_info_from_wav(time_end=None)          #unit of second, set time_end to None to analyze the entire wave file
    signal.add_channel(channel_frequency=137.9125e6, channel_bandwidth=60e3)
    print("Done")

    start_time = datetime.now()
    signal.process(default=True)
    print(f"Finished in {datetime.now() - start_time}")        

if __name__ == '__main__':
    main(debug_mode=False)


