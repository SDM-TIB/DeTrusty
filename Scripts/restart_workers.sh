#!/bin/sh

PID=$(cat /DeTrusty/DeTrusty/.pid)
kill -s HUP "$PID"
