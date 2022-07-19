#!/bin/bash

cd /DeTrusty/
gunicorn -c DeTrusty/App/gunicorn.conf.py flaskr:app
