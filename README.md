virtualenv venv -p python3.7
source venv/bin/activate

sudo apt-get install python-pyaudio libgirepository1.0-dev libjack-jackd2-dev portaudio19-dev

pip install pyaudio sounddevice pysoundfile SpeechRecognition playwright gtts playsound pynput pygobject
playwright install firefox
