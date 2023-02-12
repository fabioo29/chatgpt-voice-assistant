# ChatGPT Voice Assistant

A script that uses the OpenAI's ChatGPT language model as a voice assistant. This script allows users to interact with ChatGPT through voice commands and receive spoken responses. This can be useful for people who are trying to learn english or just want to have a fun conversation with a chatbot without having to type anything.

## Usage
```bash
# create a virtual environment
virtualenv venv -p python3.7
source venv/bin/activate

# install dependencies (tested on Ubuntu 18.04)
sudo apt-get install python-pyaudio libgirepository1.0-dev libjack-jackd2-dev portaudio19-dev libpython3.9-dev

# install python dependencies
pip install -r requirements.txt

# install firefox for playwright
playwright install firefox
```

In the `config.toml` file, you can see the base prompt that ChatGPT will use to begin the conversation. This prompt uses some *trigger words* (default: *'fix me'*) to change the way ChatGPT responds to the user. You can change these trigger words to whatever you want. You can also change the base prompt to whatever you want. The way the default prompt works is that if the user says something that starts with the **trigger words**, ChatGPT will act as a **English sentence correction tool**. If the user says something that does not contain the trigger words, ChatGPT will act as a **normal instance of ChatGPT**.

```logs
Setting up ChatGPT, Speech Recognition and Text-To-Speech...

Welcome to ChatGPT!  Press ALT to start talking, and release to stop.
Press CTRL+C to exit and wait for the program to finish.

You: where's Portugal
Bot: Portugal is a country located in southwestern Europe on the Iberian Peninsula.

You: fix me alright choose the best time for you
Bot: "Alright, choose the most convenient time for you."
```

### Add your own configuration

```md
config.json
{
    "__comment": "Supported Prompts. Can add/remove prompt here...",
    "new-language": [
        "begin prompt",
        "trigger words",
        "location LCID string (https://www.science.co.il/language/Locale-codes.php)",
        "coqui TTS model"
    ], ...
}

config.toml
[settings]
language = 'new-language'
```

## Requirements

Python 3.7 (tested)  
Playwright (tested with Firefox)

## Contributing

Feel free to open an issue or pull request if you have any suggestions or find any bugs.

- [X] Add support for multiple languages
- [ ] Add support for other TTS engines
- [ ] Add support for other STT engines
- [X] Add support for ChatGPT to begin with a base pre-defined prompt
- [ ] Add support for configurable key combinations to start/stop recording

## Credits

This project uses [chatgpt-wrapper](github.com/mmabrouk/chatgpt-wrapper)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
