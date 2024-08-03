FROM python:3.8.19-slim-bullseye

RUN apt update && apt-get install -y zlib1g-dev libjpeg-dev gcc imagemagick libmagickwand-dev ffmpeg

WORKDIR /app

COPY . /app

COPY /app/check_mi.py /usr/local/bin/
RUN chmod +x /usr/local/bin/check_mi.py

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sleep", "infinity"]
