import basic_ops as bo
from data import Database
import glob
import librosa as lb
import pyaudio
import scipy.io.wavfile as sw
import random
import numpy as np

db_client = Database('fingerprints.db')


def upload():
    """
    uploads fingerprints to database
    :return:
    """
    path = 'data/'
    total_hashes = 0
    for files in glob.glob(path + '*.wav'):
        samples, sample_rate = lb.load(path=files, sr=None)
        spec = bo.spectrogram(samples=samples, sample_rate=sample_rate)
        peaks = bo.get_peaks(spec)
        song_id = files.replace('-', ' ').replace('_', ' ').strip()[5:-4]
        hash_list = bo.gen_hash(peaks, song_id=song_id)
        for hash_item in hash_list:
            db_client.insert_fingerprint(hash_item)
            print(hash_item)

        total_hashes += len(hash_list)
    print('TOTAL FINGERPRINTS INSERTED: {}'.format(total_hashes))


def listen_query(seconds=10):
    """
    records audio and prints if a match is found from the database
    :param seconds:
    :return:
    """

    # open stream
    au = pyaudio.PyAudio()
    stream = au.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=44100,
                     input=True,
                     frames_per_buffer=8192)

    print("* recording")
    query = []
    for i in range(0, int(44100 / 8192 * seconds)):
        data = stream.read(8192)
        nums = np.fromstring(data, np.int16)
        query.extend(nums[0::2])
    print("* done recording")

    # close and stop the stream
    stream.stop_stream()
    stream.close()

    spec = bo.spectrogram(query, sample_rate=44100)
    peaks = bo.get_peaks(spec)
    hash_list = bo.gen_hash(peaks)
    db_client = Database('fingerprints.db')
    matches = db_client.fetch_result(hash_list)
    print(matches)


def from_file(sec=6):
    files = [file for file in glob.glob('**/*.wav', recursive=True)]
    fi = random.randint(0, len(files) - 1)
    samples, sample_rate = lb.load(files[fi], sr=None)
    len_sample_start = random.randint(0, len(samples) - 1 - sample_rate * sec)
    len_sample_stop = len_sample_start + sample_rate * sec
    print(len_sample_start)
    print(len_sample_stop)
    sample_query = samples[len_sample_start:len_sample_stop]
    spec = bo.spectrogram(samples=sample_query, sample_rate=sample_rate)
    peaks = bo.get_peaks(spec)
    hash_list = bo.gen_hash(peaks)
    db_client = Database('fingerprints.db')
    match = db_client.fetch_result(hash_list)
    print(match)


upload()