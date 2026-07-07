#!/bin/bash

pip install -U yt-dlp

gunicorn app:app --bind 0.0.0.0:$PORT
