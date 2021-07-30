from tracker import Signal
import signal_io
from datetime import datetime

def findsat(signal, channels, time_begin=0, time_end=None, tle_prediction = False, debug_mode=False):
    if debug_mode:
        import warnings
        warnings.filterwarnings('error')
        print("Debug mode: ON")
    print("Initializing... ", end="")   

    signal.read_info_from_wav(time_begin = time_begin, time_end=time_end)          
    for channel in channels:
        signal.add_channel(channel_frequency=channel[0], channel_bandwidth=channel[1])
    print("Done")

    start_time = datetime.now()
    signal.process(default=True, TLE_prediction = tle_prediction)
    print(f"Finished in {datetime.now() - start_time}")        

if __name__ == '__main__':
    input_folder, time_step, sensitivity, tle_prediction, time_begin, time_end, channels = signal_io.read_cli_arguments()
    signal = Signal(data_path = input_folder, sensitivity = sensitivity, step_timelength = time_step)
    findsat(signal, channels, time_begin = time_begin, time_end=time_end, tle_prediction=tle_prediction, debug_mode=False)



