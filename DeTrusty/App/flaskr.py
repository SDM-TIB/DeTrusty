__author__ = "Philipp D. Rohde"

from flask import Flask, Response, request, jsonify, render_template
from DeTrusty.Logger import get_logger
from DeTrusty import run_query
from DeTrusty.Molecule.MTManager import ConfigFile
import os
import re
from distutils.util import strtobool

logger = get_logger(__name__)

app = Flask(__name__)
app.config['VERSION'] = os.environ.get("VERSION")
app.config['JSON_AS_ASCII'] = False
app.config['CONFIG'] = ConfigFile('/DeTrusty/Config/rdfmts.json')
app.config['JOIN_STARS_LOCALLY'] = bool(strtobool(os.environ.get("JOIN_STARS_LOCALLY", 'True')))

re_service = re.compile(r".*[^:][Ss][Ee][Rr][Vv][Ii][Cc][Ee]\s*<.+>\s*{.*", flags=re.DOTALL)


@app.route('/version', methods=['POST'])
def version():
    """Returns the version of the running DeTrusty instance."""
    return Response('DeTrusty v' + app.config['VERSION'] + "\n", mimetype='text/plain')


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

        if yasqe and re_service.match(query):
            sparql1_1 = True

        return jsonify(
            run_query(
                query=query,
                decomposition_type=decomposition_type,
                sparql_one_dot_one=sparql1_1,
                config=app.config['CONFIG'],
                join_stars_locally=app.config['JOIN_STARS_LOCALLY'],
                yasqe=yasqe
            )
        )
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
