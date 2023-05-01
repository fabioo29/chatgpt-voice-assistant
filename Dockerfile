FROM python:3.9-slim-buster

WORKDIR /app

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    pkg-config fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libcairo2-dev libnspr4 libnss3 lsb-release xdg-utils libxss1 libdbus-glib-1-2 \
    curl unzip wget libpq-dev gcc xvfb libgbm1 libgbm1 libvulkan1 libu2f-udev espeak \
    portaudio19-dev python-all-dev python-gi-dev libsndfile1 libgirepository1.0-dev \
    sox ffmpeg libcairo2 libjack-jackd2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt &&\
    apt-get autoremove -y && \
    apt-get clean && \
    rm requirements.txt && \
    playwright install firefox

COPY .env /app/.env
RUN chmod 0644 /app/.env
RUN chown root:root /app/.env

COPY *.py ./
COPY cookies.tar.* ./

COPY config.* /app/

RUN cat cookies.tar.* | tar -xzf - --checkpoint=.1000 --checkpoint-action=dot

#CMD ["tail", "-f", "/dev/null"]
CMD ["python", "main.py"]
