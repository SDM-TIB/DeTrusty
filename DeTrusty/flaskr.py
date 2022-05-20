__author__ = "Philipp D. Rohde"

import logging

from flask import Flask, Response, request, jsonify, render_template
from DeTrusty import get_logger
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Decomposer.Decomposer import Decomposer
from DeTrusty.Decomposer.Planner import Planner
from DeTrusty.Wrapper.RDFWrapper import contact_source
from multiprocessing import Queue
import time
import os
import re

logger = get_logger(__name__)

app = Flask(__name__)
app.config['VERSION'] = os.environ.get("VERSION")
app.config['JSON_AS_ASCII'] = False
app.config['CONFIG'] = ConfigFile('/DeTrusty/Config/rdfmts.json')
app.config['JOIN_STARS_LOCALLY'] = os.environ.get("JOIN_STARS_LOCALLY", True)

re_https = re.compile("https?://")
re_service = re.compile(r".*[^:][Ss][Ee][Rr][Vv][Ii][Cc][Ee]\s*<.+>\s*{.*", flags=re.DOTALL)


@app.route('/version', methods=['POST'])
def version():
    """Returns the version of the running DeTrusty instance."""
    return Response('DeTrusty v' + app.config['VERSION'] + "\n", mimetype='text/plain')


def run_query(query: str,
              decomposition_type: str = "STAR",
              sparql_one_dot_one: bool = False,
              config: ConfigFile = app.config['CONFIG'],
              print_result: bool = True,
              yasqe: bool = False):
    start_time = time.time()
    decomposer = Decomposer(query, config,
                            decompType=decomposition_type,
                            joinstarslocally=app.config['JOIN_STARS_LOCALLY'],
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


@app.route('/sparql', methods=['POST'])
def sparql():
    """Retrieves a SPARQL query and returns the result."""
    try:
        query = request.values.get("query", None)
        if query is None:
            return jsonify({"result": [], "error": "No query passed."})
        sparql1_1 = request.values.get("sparql1_1", False)
        decomposition_type = request.values.get("decomp", "STAR")
        yasqe = request.values.get("yasqe", False)

        logger = logging.getLogger('gunicorn.error')
        logger.critical("\n****************************************\nQUERY\n" + query + "\n****************************************")
        logger.critical("Query includes SERVICE: " + str(re_service.match(query)))
        logger.critical("Query includes HTTP(S): " + str(re_https.match(query)))

        if yasqe and re_service.match(query):
            sparql1_1 = True

        fake_result = {
            "cardinality": 2,
            "output_version": "2.0",
            "execution_time": "0.0000300312",
            "head": {
#                "link": [],
                "vars": [
                    "concept"
                ]
            },
            "results": {
#                "distinct": False,
#                "ordered": True,
                "bindings": [
                    {
                        "concept": {
                            "type": "uri",
                            "value": "http://www.openlinksw.com/schemas/virtrdf#QuadMapFormat"
                        }
                    },
                    {
                        "concept": {
                            "type": "uri",
                            "value": "http://www.openlinksw.com/schemas/virtrdf#QuadStorage"
                        }
                    }
                ]
            }
        }
        #return jsonify(fake_result)
        return jsonify(run_query(query, decomposition_type, sparql1_1, yasqe=yasqe))
    except Exception as e:
        logger.exception(e)
        import sys
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return jsonify({"result": [], "error": str(emsg)})


@app.route('/sparql', methods=['GET'])
def query_editor():
    return render_template('query-editor.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
