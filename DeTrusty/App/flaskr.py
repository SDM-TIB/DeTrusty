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


def _proxy(method: str, path: str, **kwargs):
    """Forward a request to the metadata service and return its response verbatim.

    Parameters
    ----------
    method : str
        HTTP method (``'GET'``, ``'POST'``, ``'DELETE'``).
    path : str
        Path on the metadata service, e.g. ``'/federation/endpoint'``.
    **kwargs
        Passed directly to :func:`requests.request` (e.g. ``params=``, ``data=``).
    """
    resp = http_client.request(method, _METADATA_URL + path, **kwargs)
    return jsonify(resp.json()), resp.status_code


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


@app.route('/admin', methods=['GET'])
def federation_admin():
    return render_template('federation-admin.jinja2', title='DeTrusty - Federation Admin')


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


@app.route('/federations', methods=['GET'])
def federations():
    """Return the list of named graphs (federations) — proxied from metadata service."""
    return _proxy('GET', '/federations')


@app.route('/classes', methods=['GET'])
def classes():
    """Return all RDF Molecule classes — proxied from metadata service."""
    return _proxy('GET', '/classes', params=request.args)


@app.route('/predicates', methods=['GET'])
def predicates():
    """Return all predicates — proxied from metadata service."""
    return _proxy('GET', '/predicates', params=request.args)


@app.route('/namespaces', methods=['GET'])
def namespaces():
    """Return namespace URIs and declared prefixes — proxied from metadata service."""
    return _proxy('GET', '/namespaces', params=request.args)


@app.route('/federation/sparql', methods=['GET', 'POST'])
@require_admin
def federation_sparql():
    """Forward a read SPARQL query to the metadata service."""
    if request.method == 'POST':
        return _proxy('POST', '/sparql', data=request.form)
    return _proxy('GET', '/sparql', params=request.args)



@app.route('/federation/endpoints', methods=['GET'])
@require_admin
def federation_endpoints():
    """Return all registered endpoints for a federation — proxied from metadata service."""
    return _proxy('GET', '/federation/endpoints', params=request.args)


@app.route('/federation/endpoint', methods=['POST'])
@require_admin
def federation_add_endpoint():
    """Add a SPARQL endpoint to the federation — proxied to metadata service."""
    return _proxy('POST', '/federation/endpoint', data=request.form)


@app.route('/federation/endpoint', methods=['DELETE'])
@require_admin
def federation_delete_endpoint():
    """Remove a SPARQL endpoint from the federation — proxied to metadata service."""
    return _proxy('DELETE', '/federation/endpoint', data=request.form)


@app.route('/federation/prefix', methods=['POST'])
@require_admin
def federation_add_prefix():
    """Add or replace a user-declared prefix suggestion — proxied to metadata service."""
    return _proxy('POST', '/federation/prefix', data=request.form)


@app.route('/federation/prefix', methods=['DELETE'])
@require_admin
def federation_delete_prefix():
    """Remove a user-declared prefix suggestion — proxied to metadata service."""
    return _proxy('DELETE', '/federation/prefix', data=request.form)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
