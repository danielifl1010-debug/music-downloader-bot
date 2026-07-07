#!/bin/bash

export DENO_INSTALL="/opt/render/project/.deno"
export PATH="$DENO_INSTALL/bin:$PATH"

echo "DENO:"
deno --version

spotdl --download-deno

gunicorn app:app --timeout 300
