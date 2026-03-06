# Makefile for managing the dependencies of DeTrusty's Flask app

.PHONY: help install bundle outdated

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  install        to install all build dependencies"
	@echo "  bundle         to pack all dependencies for use in the tool"
	@echo "  outdated   to list all outdated dependencies"

install:
	python3 -m pip install -r ../../requirements-dev.txt
	npm i

bundle:
	python3 bundle-assets.py

outdated:
	npm outdated || true
