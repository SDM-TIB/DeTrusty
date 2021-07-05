import getopt
import json
import sys

from DeTrusty import get_logger
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.flaskr import run_query

logger = get_logger(__name__)


def get_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:q:o:c:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    query_file = None
    sparql_one_dot_one = False
    config_file = "./Config/rdfmts.json"
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

    if not query_file:
        usage()
        sys.exit(1)

    return query_file, sparql_one_dot_one, config_file


def usage():
    usage_str = "Usage: {program} -q <query_file> -c <config_file> -o <sparql1.1>" \
                "\nwhere \n" \
                "<sparql1.1> is one in [True, False], when True, no decomposition is needed\n"
    print(usage_str.format(program=sys.argv[0]), )


def main():
    query_file, sparql_one_dot_one, config_file = get_options()
    try:
        query = open(query_file, "r", encoding="utf8").read()
        config = ConfigFile(config_file)
        print(json.dumps(run_query(query, sparql_one_dot_one, config), indent=2))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
