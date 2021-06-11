from scipy.io import wavfile
import matplotlib.pyplot as plt
import os
import numpy as np
import datetime
import soundfile as sf
from datetime import datetime, timedelta
PATH=os.path.dirname(__file__)+'/'

#INPUT

def read_info_from_wav(wav_path, step_timelength, time_begin, time_end):
    with sf.SoundFile(wav_path, 'r') as f:
        fs= f.samplerate
        step_framelength = int(step_timelength * fs)
        max_step = int(f.frames / step_framelength) 
        f.subtype
        if time_begin < 0:
            time_begin = 0
        if (time_end == None) or (time_end * fs > f.frames):
            time_end = f.frames/fs
    return fs, step_framelength, max_step, time_begin, time_end

def read_data_from_wav(wav_path, fs, step_timelength, step_framelength, time_begin, time_end, time_data):
    with sf.SoundFile(wav_path, 'r') as f:
        # bitrate_dictionary = {'PCM_U8':255, 'PCM_S8':127, 'PCM_16': 32767}
        # normalize_factor = bitrate_dictionary[f.subtype]
        frame_begin = int(time_begin*fs)
        frame_end = frame_begin + int( int((time_end - time_begin) / step_timelength) * step_timelength * fs)
        f.seek(frame_begin)
        step = -1
        while f.tell() < frame_end:
            step += 1
            raw_time_data = f.read(frames=step_framelength)
            time_data.put((step, raw_time_data[:,0] + 1j * raw_time_data[:,1]))
        time_data.put(None)

#OUTPUT
def waterfall(signal, outputType='png'):
    """our main method of visualization"""
    plt.figure(figsize=(10,5))
    scale = 1e-3                                    #Transform Hz to kHz
    centroids = np.empty(signal.total_step)
    mags = np.empty((signal.total_step, signal.resolution))
    times = [(signal.time_of_record + timedelta(seconds=step*signal.step_timelength)).strftime('%H:%M:%S') for step in range(0, signal.total_step+1, int(signal.total_step/10))]

    for i in range(signal.total_step):
        print(f"Analyzing input... {i/signal.total_step*100:.2f}%", end='\r')
        step, centroid, mag = signal.freq_data.get()
        mags[step] = mag
        if centroid == None:
            centroids[step] = None
        else:
            centroids[step] = (centroid + signal.center_frequency) * scale
    print("Analyzing input... Done    ")
    print("Plotting waterfall... ", end='\r')

    f = (signal.simplifiedFreq + signal.center_frequency) * scale
    X, Y = np.meshgrid(f, range(signal.total_step))
    plt.pcolormesh(X, Y, mags, cmap='Blues', shading='auto', zorder=0)
    plt.yticks(range(0,signal.total_step, int(signal.total_step/10)), times)
    satellite_name, station_name, prediction_from_TLE = signal.Doppler_freqs_from_TLE()
    prediction_from_TLE *= scale
    plt.plot(prediction_from_TLE, range(signal.total_step), '.', color='green', label=f'Prediction from TLE of {satellite_name}', markersize=5, zorder=1)
    plt.plot(centroids, range(signal.total_step), '.', color='red', label='Calculation from wave file', markersize=5, zorder=1 )
    plt.grid()
    plt.ticklabel_format(axis='x', useOffset=False)
    plot_area = int(signal.bandWidth / 2)
    plot_tick = int(plot_area / 4)
    plt.xlim([(signal.expected_frequency-plot_area)*scale, (signal.expected_frequency+plot_area)*scale])
    plt.xticks(np.around(np.arange(signal.expected_frequency-plot_area, signal.expected_frequency+plot_area+plot_tick, plot_tick)*scale,decimals=1))
    plt.xlabel("Frequency [kHz]")
    plt.ylabel("Time in UTC") 
    plt.legend()
    plt.title(f"Waterfall with Centroid positions\n{signal.name} signal recorded at {station_name} station on {signal.time_of_record.strftime('%Y-%m-%d')}")
    plt.savefig(f'{PATH}/data/Waterfall_{signal.name}.{outputType}', dpi=300)
    print("Plotting waterfall... Done")

def calculated_vs_predicted(signal, outputType='png'):
    """a more simple version of waterfall"""
    plt.figure(figsize=(10,5))
    scale = 1e-3                        #Transform Hz to kHz
    prediction_from_TLE = signal.Doppler_freqs_from_TLE()*scale
    plt.plot(prediction_from_TLE, range(signal.total_step), '.', color='blue', markersize=1)
    centroids = np.empty(signal.total_step)
    times = [(signal.time_of_record + timedelta(seconds=step*signal.step_timelength)).strftime('%H:%M:%S') for step in range(0, signal.total_step+1, int(signal.total_step/10))]

    for i in range(signal.total_step):
        print(f"{int(i/signal.total_step*100)}%", end='\r')
        step, centroid, _ = signal.freq_data.get()
        if centroid == None:
            centroids[step] = None
        else:
            centroids[step] = (centroid + signal.center_frequency) * scale
    
    print("Plotting waterfall")
    plt.plot(centroids, range(signal.total_step), 'r.', markersize=1 )
    plt.yticks(range(0,signal.total_step+1, int(signal.total_step/10)), times)

    plt.grid()
    plt.ticklabel_format(axis='x', useOffset=False)
    plot_area = int(signal.bandWidth / 6)
    plot_tick = int(plot_area / 4)
    plt.xlim([(signal.expected_frequency-plot_area-plot_tick)*scale, (signal.expected_frequency+plot_area+plot_tick)*scale])
    plt.xticks(np.around(np.arange(signal.expected_frequency-plot_area-plot_tick, signal.expected_frequency+plot_area+2*plot_tick, plot_tick)*scale,decimals=1))
    plt.xlabel("Centroid position [kHz]")
    plt.ylabel("Time")
    plt.title(f"{signal.name}: The shift of centroid by time")
    plt.savefig(f'{PATH}/data/Center_position_{signal.name}.{outputType}', dpi=300)

def plot(signal, outputType = None):
    """plot the spectral density by time, not important"""
    plt.figure(figsize=(10,5))
    scale = 1e-3 #convert Hz to kHz
    f = signal.simplifiedFreq * scale
    centroids = np.empty(signal.total_step)

    while True:
        queue_output = signal.freq_data.get()
        if queue_output == 'END':
            signal.freq_data.put('END')
            break
        
        step, centroid, mag = queue_output
        print(f"\t{step/signal.total_step*100:.2f} %", end="\r")
        plt.plot(f+signal.center_frequency*scale, mag, '.', markersize=1.)
        
        if centroid != None:
            centroid = (centroid + signal.center_frequency)*scale
            plt.axvline(x=centroid, color='red', markersize=0.1, label=f'Centroid={centroid:.1f}kHz')

        centroids[step] = centroid
        plt.ticklabel_format(useOffset=False)
        plt.ylim([-20,40])
        plt.yticks(np.arange(40,-30,-10))
        plt.xticks(np.arange(signal.expected_frequency-signal.bandWidth/2, signal.expected_frequency+signal.bandWidth/2+signal.bandWidth/10, signal.bandWidth/10)*scale)

        plt.title(f'{signal.name}: Frequency domain at step {step:03d} ({datetime.timedelta(seconds=int(step*signal.step_timelength))}) with each step = {signal.step_timelength}s')
        plt.xlabel(f'Frequency (kHz)')
        plt.ylabel('Amplitude (dB)')
        plt.grid()
        plt.savefig(f'{PATH}/outputs/timeseries/{step:04d}.png', dpi=100)
        plt.clf()

def double_plot(signal, outputType = None):
    """plot spectral power density with centroid positions, not important"""
    fig, (ax1, ax2) = plt.subplots(2, figsize=(8,8))
    fig.tight_layout(pad=2.)
    scale = 1e-3 #convert Hz to kHz
    f = signal.simplifiedFreq * scale
    
    centroids = np.empty(signal.total_step)

    ax2.ticklabel_format(useOffset=False)
    ax2.grid()
    ax2.set_ylim([0,signal.total_step+1])
    # ax2.set_xlim([(signal.expected_frequency-5e3-1e3)*scale, (signal.expected_frequency+5e3+1e3)*scale])
    ax2.set_xlabel("Frequency (kHz)")
    ax2.set_ylabel("Time step")
    ax2.set_title(f"{signal.name}: Centroid position")
    # ax2.set_xticks(np.arange(signal.expected_frequency-5e3, signal.expected_frequency+5e3+1e3, 1e3)*scale)

    plot_area = int(signal.bandWidth / 2)
    plot_tick = int(plot_area / 4)
    ax2.set_xlim([(signal.expected_frequency-plot_area)*scale, (signal.expected_frequency+plot_area)*scale])
    ax2.set_xticks(np.around(np.arange(signal.expected_frequency-plot_area, signal.expected_frequency+plot_area+plot_tick, plot_tick)*scale,decimals=1))

    for i in range(signal.total_step):
        print(f"Analyzing input... {i/signal.total_step*100:.2f}%", end='\r')
        step, centroid, mag = signal.freq_data.get()
        ax1.plot(f+signal.center_frequency*scale, mag, '.', markersize=3.)        
        if centroid != None:
            centroid = (centroid + signal.center_frequency)*scale
            ax1.axvline(x=centroid, color='red', markersize=0.1)
            ax2.plot(centroid, step, 'r.', markersize=3.)
        ax1.ticklabel_format(useOffset=False)
        ax1.grid()
        ax1.set_ylim([-20,40])
        ax1.set_yticks(np.arange(40,-30,-10))
        ax1.set_xlim([(signal.expected_frequency-plot_area)*scale, (signal.expected_frequency+plot_area)*scale])
        ax1.set_xticks(np.around(np.arange(signal.expected_frequency-plot_area, signal.expected_frequency+plot_area+plot_tick, plot_tick)*scale,decimals=1))
        # ax1.set_xticks(np.arange(signal.expected_frequency-signal.bandWidth/2, signal.expected_frequency+signal.bandWidth/2+signal.bandWidth/10, signal.bandWidth/10)*scale)
        ax1.set_title(f'{signal.name}: Power spectral density at step {step:04d}')# ({datetime.timedelta(seconds=int(step*signal.step_timelength))}) with each step = {signal.step_timelength}s')
        ax1.set_ylabel('Amplitude (dB)')
        fig.savefig(f'{signal.data_path}/timeseries/{step:04d}.png', dpi=300)
        ax1.clear()
    print("Finished plotting")
    if outputType == None:
        outputType = 'mp4'
    os.system(f"ffmpeg -y -framerate {int(1/signal.step_timelength)} -i {PATH+signal.data_path}/timeseries/%04d.png -i {PATH}plot_palette.png -lavfi paletteuse {signal.data_path}/{signal.name}.{outputType}")

    # if os.name == 'nt':
        # os.system(f"del {os.path.normpath(signal.data_path)}\timeseries\\*.png)")
    # else:
        # os.system(f"rm {signal.data_path}/timeseries/*.png")
