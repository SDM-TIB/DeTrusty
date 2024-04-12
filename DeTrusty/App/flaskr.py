__author__ = "Philipp D. Rohde"

import os
from distutils.util import strtobool

from flask import Flask, Response, request, jsonify, render_template

from DeTrusty import run_query, Decomposer, Planner, __version__
from DeTrusty.Logger import get_logger
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger(__name__)

app = Flask(__name__)
app.config['VERSION'] = __version__
app.config['VERSION_STRING'] = 'DeTrusty v' + __version__
app.config['JSON_AS_ASCII'] = False
app.config['CONFIG'] = ConfigFile('/DeTrusty/Config/rdfmts.json')
app.config['JOIN_STARS_LOCALLY'] = bool(strtobool(os.environ.get('JOIN_STARS_LOCALLY', 'True')))


@app.route('/version', methods=['POST'])
def version():
    """Returns the version of the running DeTrusty instance."""
    return Response(app.config['VERSION_STRING'] + '\n', mimetype='text/plain')


@app.route('/sparql', methods=['POST'])
def sparql():
    """Retrieves a SPARQL query and returns the result."""
    try:
        query = request.values.get("query", None)
        if query is None:
            return jsonify({"result": [], "error": "No query passed."})
        decomposition_type = request.values.get("decomp", "STAR")
        yasqe = request.values.get("yasqe", False)

        return jsonify(
            run_query(
                query=query,
                decomposition_type=decomposition_type,
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
        emsg = str(repr(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        return jsonify({"result": [], "error": emsg})


@app.route('/sparql', methods=['GET'])
def query_editor():
    return render_template('query-editor.jinja2', title=app.config['VERSION_STRING'])


@app.route('/query_plan', methods=['GET'])
def query_editor_plan():
    return render_template('query-plan.jinja2', title=app.config['VERSION_STRING'])


@app.route('/query_plan', methods=['POST'])
def query_plan():
    query = request.values.get('query', None)
    decomposition_type = request.values.get('decomp', 'STAR')
    logger.warn("Got query: " + str(query))
    logger.warn("Type: " + str(type(query)))
    if query is None:
        return Response('No query was passed.', status=400, mimetype='text/plain')

    try:
        decomposer = Decomposer(query=query,
                                config=app.config['CONFIG'],
                                decompType=decomposition_type,
                                joinstarslocally=app.config['JOIN_STARS_LOCALLY'])
        decomposed_query = decomposer.decompose()
    except Exception as e:
        logger.exception(e)
        return Response('An error occurred while parsing. Please check your query', status=400, mimetype='text/plain')
    if decomposed_query is None:
        return Response('The query cannot be answered by the endpoints in the federation.',
                        status=400, mimetype='text/plain')

    try:
        planner = Planner(decomposed_query, True, contact_source, 'RDF', app.config['CONFIG'])
        plan = planner.createPlan()
        tree, details = plan.json()
    except Exception as e:
        logger.exception(e)
        return Response('An error occurred while planning the query. Please check the logs.',
                        status=400, mimetype='text/plain')

    return {'tree': tree, 'details': details}


if __name__ == "__main__":
    app.run(host='0.0.0.0')
