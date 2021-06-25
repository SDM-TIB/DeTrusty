import getopt
import json
import re
import sys
import time
from multiprocessing import Queue

from DeTrusty import get_logger
from DeTrusty.Decomposer.Decomposer import Decomposer
from DeTrusty.Decomposer.Planner import Planner
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger(__name__)


def run_query(query: str, sparql_one_dot_one: bool = False):
    config = ConfigFile('./Config/rdfmts.json')
    re_https = re.compile("https?://")

    start_time = time.time()
    decomposer = Decomposer(query, config, sparql_one_dot_one=sparql_one_dot_one)
    decomposed_query = decomposer.decompose()

    if decomposed_query is None:
        return json.dumps({"results": {}, "error": "The query cannot be answered by the endpoints in the federation."})

    planner = Planner(decomposed_query, True, contact_source, 'RDF', config)
    plan = planner.createPlan()

    output = Queue()
    plan.execute(output)

    result = []
    r = output.get()
    card = 0
    while r != 'EOF':
        card += 1
        res = {}
        for key, value in r.items():
            res[key] = {"value": value, "type": "uri" if re_https.match(value) else "literal"}
        res['__meta__'] = {"is_verified": True}

        result.append(res)
        r = output.get()
    end_time = time.time()

    return json.dumps({"head": {"vars": decomposed_query.variables()},
                    "cardinality": card,
                    "results": {"bindings": result},
                    "execution_time": end_time - start_time,
                    "output_version": "2.0"}, indent=2)


def get_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:q:o:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    query_file = None
    sparql_one_dot_one = False
    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        elif opt == "-q":
            query_file = arg
        elif opt == "-o":
            sparql_one_dot_one = eval(arg)

    if not query_file:
        usage()
        sys.exit(1)

    return query_file, sparql_one_dot_one


def usage():
    usage_str = "Usage: {program} -q <query>"
    print(usage_str.format(program=sys.argv[0]), )


def main():
    query_file, sparql_one_dot_one = get_options()
    try:
        query = open(query_file, "r", encoding="utf8").read()
        print(run_query(query, sparql_one_dot_one))
    except Exception as e:
        print(e)


if __name__ == '__main__':
    main()
