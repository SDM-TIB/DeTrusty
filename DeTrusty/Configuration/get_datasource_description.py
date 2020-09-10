__author__ = "Philipp D. Rohde"


def get_datasource_description(endpoints):
    """At this point in time, only the endpoint URLs are stored.
    In a later version, a more sophisticated datasource description will be implemented."""
    endpoints = [e.strip() for e in endpoints.split(',') if e]
    with open('/DeTrusty/Config/datasource_description.txt', 'w') as f:
        for endpoint in endpoints:
            f.write(endpoint + "\n")


def parse_datasource_file(datasource_file):
    return [e.strip() for e in open(datasource_file, 'r').readlines()]
