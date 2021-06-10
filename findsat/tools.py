import numpy as np

def centroid(freq, mag):
    """Finding the center, or spectral centroid, of the signal.
    """   
    mag_sum = np.sum(mag)
    if mag_sum == 0:
        return None
    else:
        return  np.sum(freq * mag) / mag_sum

def avg_binning(inputArray, resolution):
    avg_mag = np.empty(resolution)
    for i, value in enumerate(np.array_split(inputArray, resolution)):
        avg_mag[i] = np.mean(value)
    return avg_mag

def channel_filter(mag, resolution, pass_step_width):
    in_channel = False
    mag[-pass_step_width:-1] = 0
    for i in range(resolution):
        if (in_channel == False) and (mag[i] > 0):
            in_channel = True
            channel_begin = i
        if (in_channel == True) and (mag[i] == 0) and (np.all(mag[i+1:i+pass_step_width]==0)):
            in_channel = False
            if (i - channel_begin < pass_step_width):
                mag[channel_begin:i] = 0

def calculate_offset(input_mag):
    #resolution = int(full_bandwidth/pass_bandwidth)
    resolution = 10
    mag = np.empty(resolution)
    std = np.empty(resolution)
    for i, value in enumerate(np.array_split(input_mag, resolution)):
        mag[i] = np.mean(value)
        std[i] = np.std(value)
    return - (np.min(mag) + 4*np.min(std))



