import logging

from flask import Flask, request, jsonify
from pyoxigraph import Literal, QuerySolutions, QueryBoolean

from DeTrusty.Molecule import SEMSD
from DeTrusty.Molecule.MTManager import TTLConfig

SEMSD_PATH = '/DeTrusty/Config/rdfmts.ttl'
app = Flask(__name__)
logger = logging.getLogger(__name__)

with open(SEMSD_PATH, 'r') as file:
    _config = TTLConfig(file.read())

_store = _config.src_desc.ttl


def _persist():
    """Persist the current in-memory store back to the TTL file on disk."""
    _config.saveToFile(SEMSD_PATH)


@app.route('/')
def index():
    return 'Metadata KG'


@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    """Execute a SPARQL query against the federation metadata graph."""
    query = (request.form if request.method == 'POST' else request.args).get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    try:
        results = _store.query(query, use_default_graph_as_union=True)

        if isinstance(results, QuerySolutions):
            response = {
                'head': {'vars': [var.value for var in results.variables]},
                'results': {'bindings': []}
            }
            for result in results:
                binding = {}
                for var in results.variables:
                    if result[var] is None:
                        continue
                    value = result[var].value
                    if not isinstance(result[var], Literal):
                        binding[var.value] = {'type': 'uri', 'value': value}
                    elif result[var].datatype is not None:
                        binding[var.value] = {'type': 'typed-literal', 'value': value,
                                              'datatype': result[var].datatype.value}
                    else:
                        binding[var.value] = {'type': 'literal', 'value': value}
                response['results']['bindings'].append(binding)
            return jsonify(response)

        if isinstance(results, QueryBoolean):
            return jsonify({'boolean': bool(results)})

        return jsonify({'error': 'Unsupported query result type.'}), 400

    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/sparql-update', methods=['POST'])
def sparql_update():
    """Execute a SPARQL Update and persist to disk."""
    query = request.data.decode()
    if not query:
        return jsonify({'error': 'No update query provided'}), 400
    try:
        _store.update(query)
        _persist()
        return 'success'
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federations', methods=['GET'])
def federations():
    """Return the list of named graphs (federations) in the metadata store."""
    try:
        graphs = []
        results = _store.query(
            'SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }',
            use_default_graph_as_union=True
        )
        for row in results:
            if row['g'] is not None:
                graphs.append(row['g'].value)
        return jsonify({'federations': sorted(graphs)})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/classes', methods=['GET'])
def classes():
    """Return all RDF Molecule classes in the metadata graph.

    Query parameters
    ----------------
    federation : str, optional
        URI of the named graph to scope the lookup.
    """
    federation = request.args.get('federation') or None
    try:
        return jsonify({'classes': _config.get_molecules(federation)})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/predicates', methods=['GET'])
def predicates():
    """Return all predicates in the metadata graph.

    Query parameters
    ----------------
    federation : str, optional
        URI of the named graph to scope the lookup.
    """
    federation = request.args.get('federation') or None
    try:
        return jsonify({'predicates': _config.get_predicates(federation)})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/namespaces', methods=['GET'])
def namespaces():
    """Return all namespace URIs and user-declared prefix mappings for the federation.

    Namespace URIs are derived from all class and predicate URIs in the source
    descriptions by extracting everything up to and including the last ``#`` or
    ``/``.  User-declared ``semsd:PrefixDeclaration`` triples are returned
    separately so the frontend can offer them as named autocomplete suggestions.

    Response shape::

        {
          "namespaces": ["http://...", ...],
          "prefixes":   {"k4covid": "http://research.tib.eu/covid-19/vocab/", ...}
        }

    Query parameters
    ----------------
    federation : str, optional
        Named graph URI to scope the lookup.
    """
    federation = request.args.get('federation') or None
    try:
        if federation:
            where = (
                f'GRAPH <{federation}> {{'
                f' {{ ?uri a <{SEMSD.Class}> }}'
                f' UNION'
                f' {{ ?c <{SEMSD.hasProperty}> ?uri }}'
                f' }}'
            )
        else:
            where = (
                f'{{ ?uri a <{SEMSD.Class}> }}'
                f' UNION'
                f' {{ ?c <{SEMSD.hasProperty}> ?uri }}'
            )

        results = _store.query(
            f'SELECT DISTINCT ?uri WHERE {{ {where} }}',
            use_default_graph_as_union=True
        )

        federation_namespaces = set()
        for row in results:
            if row['uri'] is not None:
                uri = row['uri'].value
                sep = max(uri.rfind('#'), uri.rfind('/'))
                if sep > 0:
                    federation_namespaces.add(uri[:sep + 1])

        return jsonify({
            'namespaces': sorted(federation_namespaces),
            'prefixes': _config.get_prefixes(federation),
        })
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federation/endpoint', methods=['POST'])
def federation_add_endpoint():
    """Add a SPARQL endpoint to the federation.

    Authentication is enforced by the flaskr gateway; this route is only
    reachable from localhost.

    Form parameters
    ---------------
    endpoint : str
        URL of the SPARQL endpoint to add.
    federation : str, optional
        Named graph to add the endpoint to.
    username, password, keycloak : str, optional
    """
    endpoint_url = request.values.get('endpoint', '').strip()
    if not endpoint_url:
        return jsonify({'error': 'No endpoint URL provided.'}), 400
    federation = request.values.get('federation') or None
    try:
        _config.add_endpoint(
            endpoint_url,
            federation=federation,
            username=request.values.get('username') or None,
            password=request.values.get('password') or None,
            keycloak=request.values.get('keycloak') or None,
        )
        _persist()
        return jsonify({'status': 'ok', 'endpoint': endpoint_url})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federation/endpoint', methods=['DELETE'])
def federation_delete_endpoint():
    """Remove a SPARQL endpoint from the federation.

    Authentication is enforced by the flaskr gateway; this route is only
    reachable from localhost.

    Form parameters
    ---------------
    endpoint : str
        URL of the SPARQL endpoint to remove.
    federation : str, optional
        Named graph from which to remove the endpoint.
    """
    endpoint_url = request.values.get('endpoint', '').strip()
    if not endpoint_url:
        return jsonify({'error': 'No endpoint URL provided.'}), 400
    federation = request.values.get('federation') or None
    try:
        _config.delete_endpoint(endpoint_url, federation=federation)
        _persist()
        return jsonify({'status': 'ok', 'endpoint': endpoint_url})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federation/prefix', methods=['POST'])
def federation_add_prefix():
    """Add or replace a user-declared prefix suggestion.

    The declaration is stored as a ``semsd:PrefixDeclaration`` triple and
    persisted to disk immediately.

    Authentication is enforced by the flaskr gateway; this route is only
    reachable from localhost.

    Form parameters
    ---------------
    name : str
        The short prefix label (e.g. ``"k4covid"``).
    uri : str
        The namespace URI.
    federation : str, optional
        Named graph to scope the declaration to.  When omitted the declaration
        is written to the global default graph and applies to all federations.
    """
    name = request.values.get('name', '').strip()
    uri  = request.values.get('uri', '').strip()
    if not name or not uri:
        return jsonify({'error': 'Both "name" and "uri" parameters are required.'}), 400
    federation = request.values.get('federation') or None
    try:
        _config.add_prefix_declaration(name, uri, federation)
        _persist()
        return jsonify({'status': 'ok', 'name': name, 'uri': uri})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


@app.route('/federation/prefix', methods=['DELETE'])
def federation_delete_prefix():
    """Remove a user-declared prefix suggestion.

    Authentication is enforced by the flaskr gateway; this route is only
    reachable from localhost.

    Form parameters
    ---------------
    name : str
        The short prefix label to remove.
    federation : str, optional
        Named graph from which to remove the declaration.
    """
    name = request.values.get('name', '').strip()
    if not name:
        return jsonify({'error': 'The "name" parameter is required.'}), 400
    federation = request.values.get('federation') or None
    try:
        _config.delete_prefix_declaration(name, federation)
        _persist()
        return jsonify({'status': 'ok', 'name': name})
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Bind to localhost only — this service is never exposed directly.
    app.run(host='127.0.0.1', port=9000)
