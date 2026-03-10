import logging

from flask import Flask, request, jsonify
from pyoxigraph import Store, Literal, QuerySolutions, QueryBoolean

from DeTrusty.Molecule.MTManager import TTLConfig

SEMSD_PATH = '/DeTrusty/Config/rdfmts.ttl'
app = Flask(__name__)
logger = logging.getLogger(__name__)

_store = Store()
with open(SEMSD_PATH, 'r') as file:
    _config = TTLConfig(file.read())


_store = _config.src_desc.ttl


@app.route('/')
def index():
    return 'Metadata KG'


@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    """Execute a SPARQL query against the federation metadata graph.

    Uses use_default_graph_as_union=True so both the unnamed default graph
    (original bulk-loaded data) and named graphs (data added via
    INSERT DATA { GRAPH ... }) are visible together.
    """
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
    """Execute a SPARQL Update and persist to disk via TTLConfig.saveToFile()."""
    query = request.data.decode()
    if not query:
        return jsonify({'error': 'No update query provided'}), 400

    try:
        _store.update(query)
        _config.saveToFile(SEMSD_PATH)
        return 'success'
    except Exception as e:
        logger.exception(e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Bind to localhost only — this service is never exposed directly.
    app.run(host='127.0.0.1', port=9000)
