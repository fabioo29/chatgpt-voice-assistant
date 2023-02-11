# ChatGPT Voice Assistant

A script that uses the OpenAI's ChatGPT language model as a voice assistant. This script allows users to interact with ChatGPT through voice commands and receive spoken responses.

## Usage
```bash
# create a virtual environment
virtualenv venv -p python3.7
source venv/bin/activate

# install dependencies (tested on Ubuntu 18.04)
sudo apt-get install python-pyaudio libgirepository1.0-dev libjack-jackd2-dev portaudio19-dev

# install python dependencies
pip install -r requirements.txt

# install firefox for playwright
playwright install firefox
```

## Requirements

Python 3.7 (tested)  
Playwright (tested with Firefox)

## Contributing

Feel free to open an issue or pull request if you have any suggestions or find any bugs.

## Credits

This project uses [chatgpt-wrapper](github.com/mmabrouk/chatgpt-wrapper)

## License

MIT
