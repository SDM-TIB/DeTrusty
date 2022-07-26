FROM python:3.9.10-slim-buster
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

ENV VERSION="0.5.0"

# install dependencies
COPY requirements.txt /DeTrusty/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==22.0.* setuptools==60.9.* gunicorn==20.1.* && \
    python -m pip install --no-cache-dir -r /DeTrusty/requirements.txt

# copy the source code into the container
COPY . /DeTrusty
RUN cd /DeTrusty && python -m pip install -e . && mkdir -p Config
WORKDIR /DeTrusty/DeTrusty

# start the Flask app
ENTRYPOINT ["/DeTrusty/start-services.sh"]
