from tracker import Signal
from signal_io import Metadata
from datetime import datetime
import warnings

def main():
    print("Initializing... ")   
    metadata = Metadata()
    metadata.read_cli_arguments()
    if metadata.dev_mode:
        warnings.filterwarnings("error")   #If dev_mode is on, warnings will be treated as errors
    metadata.read_info_file()
    signal = Signal(metadata=metadata)

    start_time = datetime.now()
    signal.process(default=True)
    print(f"Finished in {datetime.now() - start_time}")        
    return 0

if __name__ == '__main__':
    main()



