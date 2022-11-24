__author__ = "Philipp D. Rohde"

import getopt
import json
import sys

from DeTrusty.Logger import get_logger
from DeTrusty import run_query
from DeTrusty.Molecule.MTManager import ConfigFile

logger = get_logger(__name__)


def get_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:q:o:c:r:d:j:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    query_file = None
    sparql_one_dot_one = False
    config_file = "./Config/rdfmts.json"
    print_result = True
    decomposition_type = "STAR"
    join_stars_locally = True
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
        elif opt == "-j":
            join_stars_locally = eval(arg)

    if not query_file:
        usage()
        sys.exit(1)

    return query_file, decomposition_type, sparql_one_dot_one, config_file, print_result, join_stars_locally


def usage():
    usage_str = "Usage: {program} -q <query_file> -c <config_file> -d <decomposition> -o <sparql1.1> -r <print_result> -j <join_stars_locally>" \
                "\nwhere \n" \
                "<decomposition> is one in [STAR, EG, TRIPLE] (default STAR). STAR decomposes the query into star-shaped sub-queries, EG follows the exclusive groups approach, TRIPLE generates a triple-wise decomposition.\n" \
                "<sparql1.1> is one in [True, False] (default False), when True, no decomposition is needed\n" \
                "<print_result> is one in [True, False] (default True), when False, only metadata is returned\n" \
                "<join_stars_locally> is one in [True, False] (default True), when False, joins are pushed to the sources\n"
    print(usage_str.format(program=sys.argv[0]), )


def main():
    query_file, decomposition_type, sparql_one_dot_one, config_file, print_result, join_stars_locally = get_options()
    try:
        query = open(query_file, "r", encoding="utf8").read()
        config = ConfigFile(config_file)
        print(json.dumps(run_query(query, decomposition_type, sparql_one_dot_one, config, print_result=print_result, join_stars_locally=join_stars_locally), indent=2))
    except Exception as e:
        import sys
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(emsg)


if __name__ == '__main__':
    main()
