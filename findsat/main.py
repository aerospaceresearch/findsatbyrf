import tracker
from datetime import datetime

NOAA18 = tracker.Signal(
        name = 'UnknownNOAA',                   #name of the signal
        type = 'NOAA',                          #type of the signal, for example: 'NOAA', 'general'
        data_path = 'data_NOAA18',              #path to the data-containing folder from the findsat folder, defaults to 'data'
        center_frequency = 137.5e6,             #center frequency of the wave file in Hz, defaults to 0
        sensitivity = 1.,                       #the sensitive-ness of the program in Hz, defaults to 10.
        step_timelength = 1.,                   #length of each time step in second, defaults to 1
        time_of_record = '2021-06-04 20:17:05'  #time in UTC, if set to None, datetime.now() will be used
        )
channels_NOAA = ((137.913e6, 60e3),)            #the channels will be analyzed, this this case there is only 1 channel

# PIXL1 = tracker.Signal(
        # name = 'PIXL1',                       #name of the signal
        # type = 'PIXL',                        #type of the signal, for example: 'NOAA', 'general'
        # data_path = 'data_pixl',              #path to the data-containing folder from the findsat folder, defaults to 'data'
        # center_frequency = 401e6,             #center frequency of the wave file in Hz, defaults to 0
        # sensitivity = 1.,                     #the sensitive-ness of the program in Hz, defaults to 10.
        # step_timelength = 0.1,                #length of each time step in second, defaults to 1
        # time_of_record = None                 #time in UTC, if set to None, time will be set to 0
        # )
# channels_PIXL = ((400575e3, 40e3),)

def findsat(signal, channels, time_end=None, TLE_prediction = False, filter=False, debug_mode=False):
    if debug_mode:
        import warnings
        warnings.filterwarnings('error')
        print("Debug mode: ON")
    print("Initializing... ", end="")   

    signal.read_info_from_wav(time_end=time_end)          
    for channel in channels:
        signal.add_channel(channel_frequency=channel[0], channel_bandwidth=channel[1])
    print("Done")

    start_time = datetime.now()
    signal.process(default=True, TLE_prediction = TLE_prediction, filter=filter)
    print(f"Finished in {datetime.now() - start_time}")        

if __name__ == '__main__':
    findsat(NOAA18, channels_NOAA, time_end=None, TLE_prediction = True, debug_mode=True)
    #time_end has unit of second, set time_end to None to analyze the entire wave file


