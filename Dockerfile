FROM python:3.12.12-slim-bookworm
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

# install dependencies
COPY requirements.txt /DeTrusty/requirements.txt
RUN python -m pip install --upgrade --no-cache-dir pip==25.3.* setuptools==80.9.* gunicorn==23.0.* && \
    python -m pip install --no-cache-dir -r /DeTrusty/requirements.txt

# copy the source code into the container
COPY . /DeTrusty
RUN cd /DeTrusty && python -m pip install -e . && mkdir -p Config && \
    ln -s /DeTrusty/images/icon.png /DeTrusty/DeTrusty/App/static/favicon.png
WORKDIR /DeTrusty/DeTrusty

# start the Flask app
ENTRYPOINT ["/DeTrusty/start-services.sh"]
