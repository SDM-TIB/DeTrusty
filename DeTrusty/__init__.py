__author__ = "Philipp D. Rohde"

import re
import time
from multiprocessing import Queue

from DeTrusty.Decomposer import Decomposer, Planner
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Wrapper.RDFWrapper import contact_source


re_https = re.compile("https?://")


def run_query(query: str,
              decomposition_type: str = "STAR",
              sparql_one_dot_one: bool = False,
              config: ConfigFile = ConfigFile('./Config/rdfmts.json'),
              join_stars_locally: bool = True,
              print_result: bool = True,
              yasqe: bool = False):
    start_time = time.time()
    decomposer = Decomposer(query, config,
                            decompType=decomposition_type,
                            joinstarslocally=join_stars_locally,
                            sparql_one_dot_one=sparql_one_dot_one)
    decomposed_query = decomposer.decompose()

    if decomposed_query is None:
        return {"results": {}, "error": "The query cannot be answered by the endpoints in the federation."}

    planner = Planner(decomposed_query, True, contact_source, 'RDF', config)
    plan = planner.createPlan()

    output = Queue()
    plan.execute(output)

    result = []
    r = output.get()
    card = 0
    while r != 'EOF':
        card += 1
        if print_result:
            res = {}
            for key, value in r.items():
                res[key] = {"value": value, "type": "uri" if re_https.match(value) else "literal"}
            if not yasqe:
                res['__meta__'] = {"is_verified": True}

            result.append(res)
        r = output.get()
    end_time = time.time()

    return {"head": {"vars": decomposed_query.variables()},
            "cardinality": card,
            "results": {"bindings": result} if print_result else "printing results was disabled",
            "execution_time": end_time - start_time,
            "output_version": "2.0"}
