#!/usr/bin/env python3

import getopt
import json
import sys

from DeTrusty.Molecule.MTCreation import DEFAULT_OUTPUT_PATH, create_rdfmts, logger
from DeTrusty.Molecule.MTManager import MTCreationConfig


def get_options(argv):
    try:
        opts, args = getopt.getopt(argv, 'h:s:o:p')
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    endpoints_file = None
    output = DEFAULT_OUTPUT_PATH
    plain_text = False
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt == '-s':
            endpoints_file = arg
        elif opt == '-o':
            output = arg
        elif opt == '-p':
            plain_text = True

    if not endpoints_file:
        usage()
        sys.exit(1)

    config = MTCreationConfig()
    if plain_text:
        with open(endpoints_file, 'r') as f:
            endpoints = f.readlines()
            if len(endpoints) == 0:
                logger.critical("The endpoints file should contain at least one URL")
                sys.exit(1)
            config.setEndpoints([e.strip('\n') for e in endpoints])
    else:
        with open(endpoints_file, 'r') as f:
            data = json.load(f)
            for elem in data:
                url = elem.pop('url')
                config.addEndpoint(url, elem)

    if '.json' not in output:
        output += '.json'
    return config, output


def usage():
    usage_str = (
        'Usage: {program} -s <path/to/endpoints.txt> [-o <path/to/output.json>]\n'
        'where\n'
        '    <path/to/endpoints.txt> - path to a text file containing a list of SPARQL endpoint URLs\n'
        '    <path/to/output.json> - name of output file\n'
    )
    print(usage_str.format(program=sys.argv[0]),)


if __name__ == '__main__':
    config, output = get_options(sys.argv[1:])
    create_rdfmts(config, output)
