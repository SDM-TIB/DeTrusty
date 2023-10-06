__author__ = 'Philipp D. Rohde'

import os
import re

import requests

re_https = re.compile("https?://")


def is_url(url):
    return re_https.match(url)


def read_file_from_internet(url_file: str, json_response: bool = False):
    r = requests.get(url_file)
    if r.status_code != 200:
        raise requests.RequestException('Something went wrong trying to download the file.')
    if json_response:
        return r.json()
    else:
        return r.text


def get_query_string(query_arg: str):
    if os.path.isfile(query_arg):
        return open(query_arg, 'r').read()
    elif is_url(query_arg):
        return read_file_from_internet(query_arg)
    else:  # supposedly query_arg is already a query string
        return query_arg
