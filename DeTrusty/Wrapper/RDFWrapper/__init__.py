import urllib.parse
import urllib.request

from DeTrusty.Logger import get_logger

logger = get_logger(__name__)


def contact_source(server, query, queue, buffersize=16384, limit=-1):
    # Contacts the datasource (i.e. real endpoint).
    # Every tuple in the answer is represented as Python dictionaries
    # and is stored in a queue.
    logger.info("Contacting endpoint: " + server)
    b = None
    cardinality = 0

    if limit == -1:
        b, cardinality = contact_source_aux(server, query, queue)
    else:
        # Contacts the datasource (i.e. real endpoint) incrementally,
        # retrieving partial result sets combining the SPARQL sequence
        # modifiers LIMIT and OFFSET.

        # Set up the offset.
        offset = 0

        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            b, card = contact_source_aux(server, query_copy, queue)
            cardinality += card
            if card < limit:
                break

            offset = offset + limit

    # Close the queue
    queue.put("EOF")
    return b


def contact_source_aux(server, query, queue):
    # Setting variables to return.
    b = None
    cardinality = 0

    js = "application/sparql-results+json"
    params = {'query': query, 'format': 'JSON'}
    headers = {"User-Agent":
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
               "Accept": js}
    try:
        data = urllib.parse.urlencode(params)
        data = data.encode('utf-8')
        req = urllib.request.Request(server, data, headers)
        with urllib.request.urlopen(req) as response:
            resp = response.read()
            resp = resp.decode()
            res = resp.replace("false", "False")
            res = res.replace("true", "True")
            res = eval(res)
            if type(res) == dict:
                b = res.get('boolean', None)

                if 'results' in res:
                    # print "raw results from endpoint", res
                    for x in res['results']['bindings']:
                        for key, props in x.items():
                            # Handle typed-literals and language tags
                            suffix = ''
#                            if props['type'] == 'typed-literal':
#                                if isinstance(props['datatype'], bytes):
#                                    suffix = "^^<" + props['datatype'].decode('utf-8') + ">"
#                                else:
#                                    suffix = "^^<" + props['datatype'] + ">"
#                            elif "xml:lang" in props:
#                                suffix = '@' + props['xml:lang']
                            try:
                                if isinstance(props['value'], bytes):
                                    x[key] = props['value'].decode('utf-8') + suffix
                                else:
                                    x[key] = props['value'] + suffix
                            except:
                                x[key] = props['value'] + suffix

                        queue.put(x)
                        cardinality += 1
                    # Every tuple is added to the queue.
                    # for elem in reslist:
                    # print elem
                    # queue.put(elem)

            else:
                logger.error("the source " + str(server) + " answered in " + res.getheader(
                    "content-type") + " format, instead of"
                      + " the JSON format required, then that answer will be ignored")
    except Exception as e:
        logger.error("Exception while sending request to " + str(server) + " - msg: " + str(e))
        return None, -2  # indicating an error during the query execution

    return b, cardinality
