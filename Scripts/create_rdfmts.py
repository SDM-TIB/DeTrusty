#!/usr/bin/env python3

import getopt
from DeTrusty.Molecule.MTCreation import *


def get_options(argv):
    try:
        opts, args = getopt.getopt(argv, 'h:s:o:')
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    endpoints = None
    output = DEFAULT_OUTPUT_PATH
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt == '-s':
            endpoints = arg
        elif opt == '-o':
            output = arg

    if not endpoints:
        usage()
        sys.exit(1)

    if '.json' not in output:
        output += '.json'
    return endpoints, output


def usage():
    usage_str = (
        'Usage: {program} -s <path/to/endpoints.txt> [-o <path/to/output.json>]\n'
        'where\n'
        '    <path/to/endpoints.txt> - path to a text file containing a list of SPARQL endpoint URLs\n'
        '    <path/to/output.json> - name of output file\n'
    )
    print(usage_str.format(program=sys.argv[0]),)


if __name__ == '__main__':
    endpoints_file, output = get_options(sys.argv[1:])
    with open(endpoints_file, 'r') as f:
        endpoints = f.readlines()
        if len(endpoints) == 0:
            logger.critical("The endpoints file should contain at least one URL")
            sys.exit(1)
    endpoints = [e for e in [e.strip('\n') for e in endpoints] if e]
    create_rdfmts(endpoints, output)
