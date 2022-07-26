#!/bin/sh

PID=$(cat /DeTrusty/DeTrusty/App/.pid)
kill -s HUP "$PID"
