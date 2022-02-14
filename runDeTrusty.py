__author__ = "Philipp D. Rohde"

import getopt
import json
import sys

from DeTrusty import get_logger
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.flaskr import run_query

logger = get_logger(__name__)


def get_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:q:o:c:r:d:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    query_file = None
    sparql_one_dot_one = False
    config_file = "./Config/rdfmts.json"
    print_result = True
    decomposition_type = "STAR"
    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        elif opt == "-q":
            query_file = arg
        elif opt == "-o":
            sparql_one_dot_one = eval(arg)
        elif opt == "-c":
            config_file = arg
        elif opt == "-r":
            print_result = eval(arg)
        elif opt == "-d":
            decomposition_type = arg

    if not query_file:
        usage()
        sys.exit(1)

    return query_file, decomposition_type, sparql_one_dot_one, config_file, print_result


def usage():
    usage_str = "Usage: {program} -q <query_file> -c <config_file> -d <decomposition> -o <sparql1.1> -r <print_result>" \
                "\nwhere \n" \
                "<decomposition> is one in [STAR, EG] (default STAR). STAR decomposes the query into star-shaped sub-queries while EG follows the exclusive groups approach\n" \
                "<sparql1.1> is one in [True, False] (default False), when True, no decomposition is needed\n" \
                "<print_result> is one in [True, False] (default True), when False, only metadata is returned\n"
    print(usage_str.format(program=sys.argv[0]), )


def main():
    query_file, decomposition_tpye, sparql_one_dot_one, config_file, print_result = get_options()
    try:
        query = open(query_file, "r", encoding="utf8").read()
        config = ConfigFile(config_file)
        print(json.dumps(run_query(query, decomposition_tpye, sparql_one_dot_one, config, print_result), indent=2))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
