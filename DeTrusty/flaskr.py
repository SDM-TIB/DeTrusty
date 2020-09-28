__author__ = "Philipp D. Rohde"

from flask import Flask, Response, request, jsonify
import traceback
from DeTrusty.Wrapper import RDFWrapper
from DeTrusty.Configuration.get_datasource_description import parse_datasource_file
from DeTrusty.Decomposer.Query import Query
from multiprocessing import Queue
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['DATASOURCE_DESCRIPTION_FILE'] = '/DeTrusty/Config/datasource_description.txt'
app.config['DATASOURCE_DESCRIPTION'] = parse_datasource_file(app.config['DATASOURCE_DESCRIPTION_FILE'])


@app.route('/version', methods=['POST'])
def version():
    """Returns the version of DeTrusty that is being run."""
    return Response('DeTrusty Mock-Up', mimetype='text/plain')


@app.route('/create_datasource_description', methods=['POST'])
def create_datasource_description():
    """This API call creates the datasource description for the posted endpoints."""
    endpoints = request.values.get("endpoints", None)
    if endpoints is None:
        return Response('Error: No endpoints passed.', mimetype='text/plain', status=400)
    try:
        from DeTrusty.Configuration.get_datasource_description import get_datasource_description
        get_datasource_description(endpoints)
        app.config['DATASOURCE_DESCRIPTION'] = parse_datasource_file(app.config['DATASOURCE_DESCRIPTION_FILE'])
    except Exception:
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return Response(str(emsg), mimetype='text/plain', status=500)
    return Response('Datasource description updated.', mimetype='text/plain', status=200)


@app.route('/sparql', methods=['POST'])
def sparql():
    """Retrieves a SPARQL query and returns the result."""
    try:
        query = request.values.get("query", None)
        if query is None:
            return jsonify({"result": [], "error": "No query passed."})

        # execute the query
        query = Query(query)
        output = Queue()

        start_time = time.time()
        if len(app.config['DATASOURCE_DESCRIPTION']) == 1:
            endpoint_url = app.config['DATASOURCE_DESCRIPTION'][0][0][1:-1]
            RDFWrapper.contact_source(endpoint_url, query.query_string, output)
        elif len(app.config['DATASOURCE_DESCRIPTION']) > 1:
            queues = []
            for endpoint in app.config['DATASOURCE_DESCRIPTION']:
                result_queue = Queue()
                RDFWrapper.contact_source(endpoint, query.query_string, result_queue)
                queues.append(result_queue)

            from DeTrusty.Operators.Xunion import Xunion
            while len(queues) > 1:
                left = queues.pop()
                right = queues.pop()
                out = Queue()
                Xunion(query.variables, query.variables).execute(left, right, out)
                queues.append(out)

            if query.distinct:
                from DeTrusty.Operators.Xdistinct import Xdistinct
                Xdistinct(query.variables).execute(queues[0], None, output)
            else:
                output = queues[0]
        else:
            return jsonify({"result": [],
                            "error": "No data sources set up. Please, configure your data sources first."})

        result = []
        r = output.get()
        card = 0
        while r != 'EOF':
            card += 1
            r['__meta__'] = {"is_verified": True}
            result.append(r)
            r = output.get()
        end_time = time.time()
        return jsonify({"variables": query.variables,
                        "cardinality": card,
                        "result": result,
                        "execution_time": end_time - start_time,
                        "output_version": 1})
    except Exception as e:
        logger.exception(e)
        import sys
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return jsonify({"result": [], "error": str(emsg)})


if __name__ == "__main__":
    app.run(host='0.0.0.0')
