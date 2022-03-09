#!/bin/bash

cd /DeTrusty/
gunicorn -c DeTrusty/gunicorn.conf.py flaskr:app
