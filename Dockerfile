FROM python:3.8.19-slim-bullseye

RUN apt update && apt-get install -y zlib1g-dev libjpeg-dev gcc imagemagick libmagickwand-dev ffmpeg

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

CMD ["sleep", "infinity"]
