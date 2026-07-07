#!/bin/bash

spotdl --download-deno || true

gunicorn app:app --timeout 300
