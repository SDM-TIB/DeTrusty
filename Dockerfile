FROM python:3.11.6-slim-bullseye
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

ENV VERSION="0.15.1"

# install dependencies
COPY requirements.txt /DeTrusty/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==23.1.* setuptools==67.8.* gunicorn==20.1.* && \
    python -m pip install --no-cache-dir -r /DeTrusty/requirements.txt

# copy the source code into the container
COPY . /DeTrusty
RUN cd /DeTrusty && python -m pip install -e . && mkdir -p Config
WORKDIR /DeTrusty/DeTrusty

# start the Flask app
ENTRYPOINT ["/DeTrusty/start-services.sh"]
