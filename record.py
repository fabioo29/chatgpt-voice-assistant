import tempfile
import queue
import sys
import os

import sounddevice as sd
import soundfile as sf

from pynput import keyboard as pk


q = queue.Queue()


def on_press(key):
    if key == pk.Key.alt_l:
        global recording
        recording = True

def on_release(key):
    if key == pk.Key.alt_l:
        global recording
        recording = False

        
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())

if __name__ == "__main__":
    listener = pk.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    device_info = sd.query_devices(None, 'input')
    samplerate = int(device_info['default_samplerate'])
    filename = tempfile.mktemp(prefix='delme_rec_unlimited_', suffix='.wav', dir='')

    recording = False
    while True:
        if recording:
            if os.path.exists(filename):
                os.remove(filename)
                
            with sf.SoundFile(filename, mode='x', samplerate=samplerate, channels=1, subtype=None) as file:
                with sd.InputStream(samplerate=samplerate, device=None, channels=1, callback=callback):
                    print("Recording started. Press Ctrl+C to stop.")
                    while True:
                        file.write(q.get())
                        if not recording:
                            print("Recording stopped and file saved.")
                            break