from tracker import Signal
import signal_io
from datetime import datetime

def main(debug_mode = False):
    if debug_mode:
        import warnings
        warnings.filterwarnings('error')
        print("Debug mode: ON")
    print("Initializing... ")   
    metadata = signal_io.metadata_input()
    metadata.read_cli_arguments()
    metadata.read_info_file()
    signal = Signal(metadata=metadata)
    start_time = datetime.now()
    signal.process(default=True)
    print(f"Finished in {datetime.now() - start_time}")        

if __name__ == '__main__':
    main()



