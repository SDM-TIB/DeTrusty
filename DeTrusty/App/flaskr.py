__author__ = "Philipp D. Rohde"

import functools
import os
from distutils.util import strtobool

import requests as http_client
from flask import Flask, Response, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from DeTrusty import run_query, Decomposer, Planner, __version__
from DeTrusty.Logger import get_logger
from DeTrusty.Molecule.MTManager import SPARQLConfig, FederationConfig
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger(__name__)

_METADATA_URL = os.environ.get('METADATA_SERVICE_URL', 'http://127.0.0.1:9000')

_ADMIN_KEY = os.environ.get('FEDERATION_ADMIN_KEY', '')
"""Set FEDERATION_ADMIN_KEY in the environment to a strong secret.

Requests to /federation/* must carry the header:
    Authorization: Bearer <FEDERATION_ADMIN_KEY>
"""
if not _ADMIN_KEY:
    logger.warning('FEDERATION_ADMIN_KEY is not set. Federation management endpoints are disabled.')


def require_admin(f):
    """Decorator that enforces Bearer-token admin authentication."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not _ADMIN_KEY:
            return jsonify({'error': 'Federation management is disabled: FEDERATION_ADMIN_KEY not configured.'}), 403
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer ') or auth[len('Bearer '):] != _ADMIN_KEY:
            return jsonify({'error': 'Unauthorized.'}), 401
        return f(*args, **kwargs)
    return wrapper


def _build_config() -> SPARQLConfig:
    """Instantiate SPARQLConfig directly against the metadata service."""
    cfg = SPARQLConfig(_METADATA_URL + '/sparql')
    cfg.set_update_credentials(_METADATA_URL + '/sparql-update', '', '')
    return cfg


def _federation_config(federation: str = None):
    """Return the appropriate config for the given federation.

    No federation (None / empty string) → the base SPARQLConfig is returned
    directly so that source selection runs across all named graphs.

    A specific federation URI → a FederationConfig scoped to that named graph.
    """
    if not federation:
        return app.config['CONFIG']
    return FederationConfig(app.config['CONFIG'], graph=federation)


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
app.config['VERSION'] = __version__
app.config['VERSION_STRING'] = 'DeTrusty v' + __version__
app.config['JSON_AS_ASCII'] = False
app.config['CONFIG'] = _build_config()
app.config['JOIN_STARS_LOCALLY'] = bool(strtobool(os.environ.get('JOIN_STARS_LOCALLY', 'True')))


@app.context_processor
def inject_version():
    return {'version_string': app.config['VERSION_STRING']}


@app.route('/', methods=['GET'])
def home():
    return render_template('home.jinja2', title='DeTrusty - Home')


@app.route('/sparql', methods=['GET'])
def query_editor():
    return render_template('query-editor.jinja2', title='DeTrusty - Query Editor')


@app.route('/query_plan', methods=['GET'])
def query_editor_plan():
    return render_template('query-plan.jinja2', title='DeTrusty - Query Plan')


@app.route('/version', methods=['POST'])
def version():
    """Returns the version of the running DeTrusty instance."""
    return Response(app.config['VERSION_STRING'] + '\n', mimetype='text/plain')


@app.route('/sparql', methods=['POST'])
def sparql():
    """Retrieves a SPARQL query and returns the result."""
    try:
        query = request.values.get('query', None)
        if query is None:
            return jsonify({'result': [], 'error': 'No query passed.'})
        decomposition_type = request.values.get('decomp', 'STAR')
        yasqe = request.values.get('yasqe', False)

        federation = request.values.get('federation', None)
        fed_cfg = _federation_config(federation)
        return jsonify(
            run_query(
                query=query,
                decomposition_type=decomposition_type,
                config=fed_cfg,
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
        return jsonify({'result': [], 'error': emsg})


@app.route('/query_plan', methods=['POST'])
def query_plan():
    query = request.values.get('query', None)
    decomposition_type = request.values.get('decomp', 'STAR')
    logger.warn('Got query: ' + str(query))
    logger.warn('Type: ' + str(type(query)))
    if query is None:
        return Response('No query was passed.', status=400, mimetype='text/plain')

    federation = request.values.get('federation', None)
    fed_cfg = _federation_config(federation)

    try:
        decomposer = Decomposer(query=query,
                                config=fed_cfg,
                                decompType=decomposition_type,
                                joinstarslocally=app.config['JOIN_STARS_LOCALLY'])
        decomposed_query = decomposer.decompose()
    except Exception as e:
        logger.exception(e)
        return Response('An error occurred while parsing. Please check your query.', status=400, mimetype='text/plain')
    if decomposed_query is None:
        return Response('The query cannot be answered by the endpoints in the federation.',
                        status=400, mimetype='text/plain')

    try:
        planner = Planner(decomposed_query, True, contact_source, 'RDF', fed_cfg)
        plan = planner.createPlan()
        tree, details = plan.json()
    except Exception as e:
        logger.exception(e)
        return Response('An error occurred while planning the query. Please check the logs.',
                        status=400, mimetype='text/plain')

    return {'tree': tree, 'details': details}


@app.route('/federation/sparql', methods=['GET', 'POST'])
@require_admin
def federation_sparql():
    """Forward a read SPARQL query to the metadata service."""
    try:
        if request.method == 'POST':
            resp = http_client.post(_METADATA_URL + '/sparql', data=request.form)
        else:
            resp = http_client.get(_METADATA_URL + '/sparql', params=request.args)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federation/endpoint', methods=['POST'])
@require_admin
def federation_add_endpoint():
    """Add a SPARQL endpoint to the federation.

    Form parameters
    ---------------
    endpoint : str
        URL of the SPARQL endpoint to add.
    federation : str, optional
        Named graph (federation) to add the endpoint to.
    username : str, optional
    password : str, optional
    keycloak : str, optional
        URL of the token server providing access tokens.
    """
    endpoint_url = request.values.get('endpoint')
    if not endpoint_url:
        return jsonify({'error': 'No endpoint URL provided.'}), 400

    fed_cfg = _federation_config(request.values.get('federation'))
    try:
        fed_cfg.add_endpoint(
            endpoint_url,
            username=request.values.get('username') or None,
            password=request.values.get('password') or None,
            keycloak=request.values.get('keycloak') or None,
        )
        return jsonify({'status': 'ok', 'endpoint': endpoint_url})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federation/endpoint', methods=['DELETE'])
@require_admin
def federation_delete_endpoint():
    """Remove a SPARQL endpoint from the federation.

    Form parameters
    ---------------
    endpoint : str
        URL of the SPARQL endpoint to remove.
    federation : str, optional
        Named graph (federation) from which to remove the endpoint.
    """
    endpoint_url = request.values.get('endpoint')
    if not endpoint_url:
        return jsonify({'error': 'No endpoint URL provided.'}), 400

    fed_cfg = _federation_config(request.values.get('federation'))
    try:
        fed_cfg.delete_endpoint(endpoint_url)
        return jsonify({'status': 'ok', 'endpoint': endpoint_url})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federations', methods=['GET'])
def federations():
    """Return the list of named graphs (federations) available in the metadata store.

    No authentication required — this is read-only and needed by the UI to
    populate the federation selector on the query pages.
    """
    try:
        resp = http_client.get(
            _METADATA_URL + '/sparql',
            params={'query': 'SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }'}
        )
        resp.raise_for_status()
        bindings = resp.json().get('results', {}).get('bindings', [])
        graphs = [b['g']['value'] for b in bindings if 'g' in b]
        return jsonify({'federations': graphs})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0')
