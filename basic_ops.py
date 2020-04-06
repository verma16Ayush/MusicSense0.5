import numpy as np
import hashlib
from scipy.ndimage import generate_binary_structure, iterate_structure, binary_erosion, maximum_filter


def spectrogram(samples, sample_rate, stride_ms=10.0, window_ms=20.0, max_freq=20000.0, eps=1e-14):
    """
    spectrogram implementation. takes in samples and sample rate and returns a 2d array.
    :param samples: 1d array of samples
    :param sample_rate: 44100 for most accurate calculations. use the original sample rate of audio (recommended)
    :param stride_ms: stride size. default value 10 milli seconds
    :param window_ms: Hanning window size. default value 20 milli seconds
    :param max_freq: maximum observable frequency. default value 20KHz
    :param eps:
    :return: 2d array or a savable image. looks pretty AF
    """
    stride_size = int(0.001 * sample_rate * stride_ms)
    window_size = int(0.001 * sample_rate * window_ms)

    # Extract strided windows
    truncate_size = (len(samples) - window_size) % stride_size
    samples = samples[:len(samples) - truncate_size]
    nshape = (window_size, (len(samples) - window_size) // stride_size + 1)
    nstrides = (samples.strides[0], samples.strides[0] * stride_size)
    windows = np.lib.stride_tricks.as_strided(samples, shape=nshape, strides=nstrides)

    assert np.all(windows[:, 1] == samples[stride_size:(stride_size + window_size)])

    # Window weighting, squared Fast Fourier Transform (fft), scaling
    weighting = np.hanning(window_size)[:, None]

    fft = np.fft.rfft(windows * weighting, axis=0)
    fft = np.absolute(fft)
    fft = fft ** 2

    scale = np.sum(weighting ** 2) * sample_rate
    fft[1:-1, :] *= (2.0 / scale)
    fft[(0, -1), :] /= scale

    # Prepare fft frequency list
    freqs = float(sample_rate) / window_size * np.arange(fft.shape[0])

    # Compute spectrogram feature
    ind = np.where(freqs <= max_freq)[0][-1] + 1
    specgram = np.log(fft[:ind, :] + eps)
    return specgram


def get_peaks(img):
    """
    create a binary structure to specify shape. use this shape to filter peaks
    from the spectrogram image passed as param. erode the background and apply
    xor operation to get final image(a 2d array) containing only peaks.
    find the amplitude at the found peaks.
    extract time and frequency location from the original spectrogram using these found peak.
    filter through the peaks. i used only the peaks whose amps are more than the avg amp.
    zip all these into a list and return for hashing
    :param img:
    :return: list of tuples containing time and frequency location in the structure [(time,freq)...]
    """
    struct = generate_binary_structure(2, 2)
    neighbor = iterate_structure(structure=struct, iterations=20)
    avg_peak = np.mean(img)
    maximas = maximum_filter(input=img, footprint=neighbor) == img
    background = img == 0
    eroded_back = binary_erosion(input=background, structure=neighbor, border_value=1)
    peaks = maximas ^ eroded_back  # this will return a numpy array containing boolean values that are true at the peaks
    amps = img[peaks]
    t, f = np.where(peaks)
    zipped_peaks = list(zip(t, f, amps))
    # filtering through our peaks
    time_loc = [zips[0] for zips in zipped_peaks if zips[2] >= avg_peak]
    freq_loc = [zips[1] for zips in zipped_peaks if zips[2] >= avg_peak]
    return list(zip(time_loc, freq_loc))


def gen_hash(peak_loc, song_id=None):
    """
    implements hashing for accurate matching of songs. returns half the size of original hash so as to be more
    space efficient
    :param peak_loc: peaks as returned by get_peaks method
    :param song_id:
    :return: a list of hashes along with song id and time offset in structure
    [(hash,(song_id, time_offset)).......]
    """
    hash_list = list()

    for i in range(len(peak_loc)):
        for j in range(0, 20):
            if i + j < len(peak_loc):

                f1 = peak_loc[i][1]
                f2 = peak_loc[i + j][1]
                t1 = peak_loc[i][0]
                t2 = peak_loc[i + j][0]
                del_t = t2 - t1

                if del_t > 0:
                    # encoding and hashing in the defined structure
                    st = ('{}{}{}'.format(f1, f2, del_t)).encode('utf-8')
                    h = hashlib.sha1(st)
                    # t1 is the offset time
                    hash_list.append((h.hexdigest()[:20], (song_id, t1)))

    return hash_list


def align_match():
    pass
