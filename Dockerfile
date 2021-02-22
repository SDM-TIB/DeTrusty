FROM python:3.8.6-slim-buster
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

ENV VERSION="0.2.0"

# install dependencies
COPY requirements.txt /DeTrusty/requirements.txt
RUN pip3 install --upgrade --no-cache-dir pip==21.0.1 setuptools==53.0.0 gunicorn==20.0.4 && pip3 install -r /DeTrusty/requirements.txt

# copy the source code into the container
COPY . /DeTrusty
RUN cd /DeTrusty && python3 setup.py install && mkdir -p Config
WORKDIR /DeTrusty/DeTrusty

# start the Flask app
ENTRYPOINT ["bash", "-c", "cd /DeTrusty/DeTrusty; gunicorn --workers 4 --timeout 300 --graceful-timeout 300 --bind 0.0.0.0:5000 flaskr:app"]