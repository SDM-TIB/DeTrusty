FROM python:3.6.12-slim-buster
MAINTAINER Philipp D. Rohde <philipp.rohde@tib.eu>

COPY requirements.txt /DeTrusty/requirements.txt
RUN pip3 install --upgrade pip && pip3 install -r /DeTrusty/requirements.txt

COPY . /DeTrusty
RUN cd /DeTrusty && python3 setup.py install && mkdir -p Config
WORKDIR /DeTrusty/DeTrusty

ENTRYPOINT ["python3", "flaskr.py"]