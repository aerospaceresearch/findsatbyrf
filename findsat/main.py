from tracker import Signal
from signal_io import Metadata
from datetime import datetime

def main():
    print("Initializing... ")   
    metadata = Metadata()
    metadata.read_cli_arguments()
    metadata.read_info_file()
    signal = Signal(metadata=metadata)

    start_time = datetime.now()
    signal.process(default=True)
    print(f"Finished in {datetime.now() - start_time}")        
    return 0

if __name__ == '__main__':
    main()



