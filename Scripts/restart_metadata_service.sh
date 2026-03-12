#!/bin/sh

PID=$(cat /DeTrusty/DeTrusty/App/.metadata_pid)
kill -s HUP "$PID"
