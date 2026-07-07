#!/bin/bash

apt-get update -y
apt-get install -y ffmpeg

pip install -U yt-dlp

gunicorn app:app --bind 0.0.0.0:$PORT
