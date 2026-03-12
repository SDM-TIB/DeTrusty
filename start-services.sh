#!/bin/bash
set -e

cd /DeTrusty/

METADATA_LOG="/var/log/detrusty/metadata.log"
mkdir -p "$(dirname "$METADATA_LOG")"

gunicorn \
    --workers 1 \
    --bind 127.0.0.1:9000 \
    --log-file "$METADATA_LOG" \
    --capture-output \
    "DeTrusty.App.metadata:app" &

METADATA_PID=$!
echo "$METADATA_PID" > /DeTrusty/DeTrusty/App/.metadata_pid

PROBE='curl -sf -X POST http://127.0.0.1:9000/sparql --data-urlencode "query=ASK {}" > /dev/null'

echo "Waiting for metadata service (PID $METADATA_PID)..."
until eval "$PROBE"; do
    # Bail out early if the metadata service process has already died.
    if ! kill -0 $METADATA_PID 2>/dev/null; then
        echo "ERROR: metadata service exited unexpectedly. Aborting."
        exit 1
    fi
    sleep 0.5
done
echo "Metadata service is up."

exec gunicorn -c DeTrusty/App/gunicorn.conf.py flaskr:app
