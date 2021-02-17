__author__ = "Philipp D. Rohde"

from flask import Flask, Response, request, jsonify
from DeTrusty import get_logger
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Decomposer.Decomposer import Decomposer
from DeTrusty.Decomposer.Planner import Planner
from DeTrusty.Wrapper.RDFWrapper import contact_source
from multiprocessing import Queue
import time
import os

logger = get_logger(__name__)

app = Flask(__name__)
app.config['VERSION'] = os.environ.get("VERSION")
app.config['JSON_AS_ASCII'] = False
app.config['CONFIG'] = ConfigFile('/DeTrusty/Config/rdfmts.json')


@app.route('/version', methods=['POST'])
def version():
    """Returns the version of DeTrusty that is being run."""
    return Response('DeTrusty v' + app.config['VERSION'] + "\n", mimetype='text/plain')


@app.route('/sparql', methods=['POST'])
def sparql():
    """Retrieves a SPARQL query and returns the result."""
    try:
        query = request.values.get("query", None)
        if query is None:
            return jsonify({"result": [], "error": "No query passed."})

        # execute the query
        start_time = time.time()
        decomposer = Decomposer(query, app.config['CONFIG'])
        decomposed_query = decomposer.decompose()

        if decomposed_query is None:
            return jsonify({"result": [], "error": "The query cannot be answered by the endpoints in the federation."})

        planner = Planner(decomposed_query, True, contact_source, 'RDF', app.config['CONFIG'])
        plan = planner.createPlan()

        output = Queue()
        plan.execute(output)

        result = []
        r = output.get()
        card = 0
        while r != 'EOF':
            card += 1
            r['__meta__'] = {"is_verified": True}
            result.append(r)
            r = output.get()
        end_time = time.time()

        return jsonify({"variables": decomposed_query.variables(),
                        "cardinality": card,
                        "result": result,
                        "execution_time": end_time - start_time,
                        "output_version": "1.0"})
    except Exception as e:
        logger.exception(e)
        import sys
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return jsonify({"result": [], "error": str(emsg)})


if __name__ == "__main__":
    app.run(host='0.0.0.0')
