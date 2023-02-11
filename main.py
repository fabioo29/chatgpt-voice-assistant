import os
import sys
import time
import toml
import json
import uuid
import queue
import atexit
import base64
import pygame
import tempfile
import operator
import contextlib
import soundfile as sf
import sounddevice as sd

from time import sleep
from TTS.api import TTS
from functools import reduce
import speech_recognition as sr
from pynput import keyboard as pk
from playwright.sync_api import sync_playwright


config = toml.load("config.toml")
json_config = json.load(open("config.json"))

REC_START_FX = os.path.join('assets', config["paths"]["startfx"])
REC_END_FX = os.path.join('assets', config["paths"]["endfx"])
COOKIES_PATH = config["paths"]["cookies"]

VOICE_VOLUME = config["settings"]["volume"]
KEYS_COMBO = config["settings"]["key_combo"]
LANGUAGE = config["settings"]["language"]

BASE_PROMPT = json_config[LANGUAGE][0]
TRIGGER_WORDS = json_config[LANGUAGE][1]
SPEECH_LANG = json_config[LANGUAGE][2]
TTS_MODEL = json_config[LANGUAGE][3]


class ChatGPT:
    """
    A ChatGPT interface that uses Playwright to run a browser,
    and interacts with that browser to communicate with ChatGPT in
    order to provide an open API to ChatGPT.

    From github.com/mmabrouk/chatgpt-wrapper
    """

    stream_div_id = "chatgpt-wrapper-conversation-stream-data"
    eof_div_id = "chatgpt-wrapper-conversation-stream-data-eof"
    session_div_id = "chatgpt-wrapper-session-data"

    def __init__(self, headless: bool = True, browser="firefox", timeout=60):
        self.play = sync_playwright().start()

        try:
            playbrowser = getattr(self.play, browser)
        except Exception:
            print(f"Browser {browser} is invalid, falling back on firefox")
            playbrowser = self.play.firefox

        self.browser = playbrowser.launch_persistent_context(
            user_data_dir=os.path.join(os.path.dirname(__file__), COOKIES_PATH),
            headless=headless,
        )
        if len(self.browser.pages) > 0:
            self.page = self.browser.pages[0]
        else:
            self.page = self.browser.new_page()
        self._start_browser()
        self.parent_message_id = str(uuid.uuid4())
        self.conversation_id = None
        self.session = None
        self.timeout = timeout
        atexit.register(self._cleanup)

    def _start_browser(self):
        self.page.goto("https://chat.openai.com/")

    def _cleanup(self):
        self.browser.close()
        self.play.stop()

    def refresh_session(self):
        self.page.evaluate(
            """
        const xhr = new XMLHttpRequest();
        xhr.open('GET', 'https://chat.openai.com/api/auth/session');
        xhr.onload = () => {
          if(xhr.status == 200) {
            var mydiv = document.createElement('DIV');
            mydiv.id = "SESSION_DIV_ID"
            mydiv.innerHTML = xhr.responseText;
            document.body.appendChild(mydiv);
          }
        };
        xhr.send();
        """.replace(
                "SESSION_DIV_ID", self.session_div_id
            )
        )

        while True:
            session_datas = self.page.query_selector_all(f"div#{self.session_div_id}")
            if len(session_datas) > 0:
                break
            sleep(0.2)

        session_data = json.loads(session_datas[0].inner_text())
        self.session = session_data

        self.page.evaluate(f"document.getElementById('{self.session_div_id}').remove()")

    def _cleanup_divs(self):
        self.page.evaluate(f"document.getElementById('{self.stream_div_id}').remove()")
        self.page.evaluate(f"document.getElementById('{self.eof_div_id}').remove()")

    def ask_stream(self, prompt: str):
        if self.session is None:
            self.refresh_session()

        new_message_id = str(uuid.uuid4())

        if "accessToken" not in self.session:
            yield (
                "Your ChatGPT session is not usable.\n"
                "* Run this program with the `install` parameter and log in to ChatGPT.\n"
                "* If you think you are already logged in, try running the `session` command."
            )
            return

        request = {
            "messages": [
                {
                    "id": new_message_id,
                    "role": "user",
                    "content": {"content_type": "text", "parts": [prompt]},
                }
            ],
            "model": "text-davinci-002-render",
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_message_id,
            "action": "next",
        }

        code = (
            """
            const stream_div = document.createElement('DIV');
            stream_div.id = "STREAM_DIV_ID";
            document.body.appendChild(stream_div);
            const xhr = new XMLHttpRequest();
            xhr.open('POST', 'https://chat.openai.com/backend-api/conversation');
            xhr.setRequestHeader('Accept', 'text/event-stream');
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('Authorization', 'Bearer BEARER_TOKEN');
            xhr.responseType = 'stream';
            xhr.onreadystatechange = function() {
              var newEvent;
              if(xhr.readyState == 3 || xhr.readyState == 4) {
                const newData = xhr.response.substr(xhr.seenBytes);
                try {
                  const newEvents = newData.split(/\\n\\n/).reverse();
                  newEvents.shift();
                  if(newEvents[0] == "data: [DONE]") {
                    newEvents.shift();
                  }
                  if(newEvents.length > 0) {
                    newEvent = newEvents[0].substring(6);
                    // using XHR for eventstream sucks and occasionally ive seen incomplete
                    // json objects come through  JSON.parse will throw if that happens, and
                    // that should just skip until we get a full response.
                    JSON.parse(newEvent);
                  }
                } catch (err) {
                  console.log(err);
                  newEvent = undefined;
                }
                if(newEvent !== undefined) {
                  stream_div.innerHTML = btoa(newEvent);
                  xhr.seenBytes = xhr.responseText.length;
                }
              }
              if(xhr.readyState == 4) {
                const eof_div = document.createElement('DIV');
                eof_div.id = "EOF_DIV_ID";
                document.body.appendChild(eof_div);
              }
            };
            xhr.send(JSON.stringify(REQUEST_JSON));
            """.replace(
                "BEARER_TOKEN", self.session["accessToken"]
            )
            .replace("REQUEST_JSON", json.dumps(request))
            .replace("STREAM_DIV_ID", self.stream_div_id)
            .replace("EOF_DIV_ID", self.eof_div_id)
        )

        self.page.evaluate(code)

        last_event_msg = ""
        start_time = time.time()
        while True:
            eof_datas = self.page.query_selector_all(f"div#{self.eof_div_id}")

            conversation_datas = self.page.query_selector_all(
                f"div#{self.stream_div_id}"
            )
            if len(conversation_datas) == 0:
                continue

            full_event_message = None

            try:
                event_raw = base64.b64decode(conversation_datas[0].inner_html())
                if len(event_raw) > 0:
                    event = json.loads(event_raw)
                    if event is not None:
                        self.parent_message_id = event["message"]["id"]
                        self.conversation_id = event["conversation_id"]
                        full_event_message = "\n".join(
                            event["message"]["content"]["parts"]
                        )
            except Exception:
                yield (
                    "Failed to read response from ChatGPT.  Tips:\n"
                    " * Try again.  ChatGPT can be flaky.\n"
                    " * Use the `session` command to refresh your session, and then try again.\n"
                    " * Restart the program in the `install` mode and make sure you are logged in."
                )
                break

            if full_event_message is not None:
                chunk = full_event_message[len(last_event_msg):]
                last_event_msg = full_event_message
                yield chunk

            # if we saw the eof signal, this was the last event we
            # should process and we are done
            if len(eof_datas) > 0 or (((time.time() - start_time) > self.timeout) and full_event_message is None):
                break

            sleep(0.2)

        self._cleanup_divs()

    def ask(self, message: str) -> str:
        """
        Send a message to chatGPT and return the response.

        Args:
            message (str): The message to send.

        Returns:
            str: The response received from OpenAI.
        """
        response = list(self.ask_stream(message))
        return (
            reduce(operator.add, response)
            if len(response) > 0
            else "Unusable response produced, maybe login session expired. Try 'pkill firefox' and 'chatgpt install'"
        )

    def new_conversation(self):
        self.parent_message_id = str(uuid.uuid4())
        self.conversation_id = None


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
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "cookies")):
        chatgpt = ChatGPT(headless=False, timeout=90)
        print("Running ChatGPT for the first time. Please log in to OpenAI.com and then press CTRL+C to continue...")
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                chatgpt._cleanup()
                break

    print("Setting up ChatGPT, Speech Recognition and Text-To-Speech...")
    with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
        q = queue.Queue()
        bot = ChatGPT()
        r = sr.Recognizer()
        tts = TTS(model_name=TTS_MODEL, progress_bar=False)

    listener = pk.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    pygame.init()
    ssound = pygame.mixer.Sound(REC_START_FX)
    esound = pygame.mixer.Sound(REC_END_FX)

    device_info = sd.query_devices(None, 'input')
    samplerate = int(device_info['default_samplerate'])

    _ = bot.ask(BASE_PROMPT.replace("TRIGGER WORDS", TRIGGER_WORDS))

    recording = False
    try:
        print("\nWelcome to ChatGPT!  Press ALT to start talking, and release to stop.")
        print("Press CTRL+C to exit and wait for the program to finish.\n")
        while True:
            if recording:
                with tempfile.NamedTemporaryFile(suffix='.wav') as youtf:
                    with sf.SoundFile(youtf.name, mode='w', samplerate=samplerate, channels=1, subtype=None) as file:
                        with sd.InputStream(samplerate=samplerate, device=None, channels=1, callback=callback):
                            ssound.play()
                            ssound.set_volume(VOICE_VOLUME*0.1)
                            pygame.time.wait(int(ssound.get_length() * 1000))
                            #print("Recording started...")
                            while True:
                                file.write(q.get())
                                if not recording:
                                    esound.play()
                                    esound.set_volume(VOICE_VOLUME*0.1)
                                    pygame.time.wait(int(esound.get_length() * 1000))
                                    #print("Recording stopped...")
                                    break

                    with sr.AudioFile(youtf.name) as source:
                        audio = r.record(source)
                        try:
                            text = r.recognize_google(audio, show_all=True, language=SPEECH_LANG)
                            final_pred = text['alternative'][0]['transcript']
                            print(f"\nYou: {final_pred}")

                            response = bot.ask(final_pred).replace('\n', ' ')
                            with tempfile.NamedTemporaryFile(suffix='.wav') as bottf:
                                with open(os.devnull, "w") as f, contextlib.redirect_stdout(f):
                                    tts.tts_to_file(text=response, file_path=bottf.name)
                                print(f"Bot: {response}")
                                vresponse = pygame.mixer.Sound(bottf.name)
                                vresponse.play()
                                vresponse.set_volume(VOICE_VOLUME)
                                pygame.time.wait(int(vresponse.get_length() * 1000))
                        except:
                            print("Bot: Sorry, I didn't catch that.")

    except KeyboardInterrupt:
        print('Bot: Goodbye!')
        listener.stop()
        pygame.quit()