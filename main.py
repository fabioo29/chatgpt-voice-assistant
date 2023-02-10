import os
import sys
import queue
import soundfile as sf
import sounddevice as sd

import speech_recognition as sr
from pynput import keyboard as pk


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


q = queue.Queue()
r = sr.Recognizer()


if __name__ == "__main__":
    listener = pk.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    device_info = sd.query_devices(None, 'input')
    samplerate = int(device_info['default_samplerate'])
    filename = 'output.wav'

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

            with sr.AudioFile(filename) as source:
                audio = r.record(source)
                try:
                    text = r.recognize_google(audio, show_all=True)
                    final_pred = text['alternative'][0]['transcript']
                    print(f"You: {final_pred}")

                except:
                    print("Sorry, I didn't catch that.")