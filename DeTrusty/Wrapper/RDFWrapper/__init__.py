import urllib.parse
import urllib.request
from time import time

import requests

from DeTrusty.Logger import get_logger

logger = get_logger(__name__)


def contact_source(server, query, queue, buffersize=16384, limit=-1, params=None):
    # Contacts the datasource (i.e. real endpoint).
    # Every tuple in the answer is represented as Python dictionaries
    # and is stored in a queue.
    logger.info("Contacting endpoint: " + server)
    b = None
    cardinality = 0

    if limit == -1:
        b, cardinality = contact_source_aux(server, query, queue, params)
    else:
        # Contacts the datasource (i.e. real endpoint) incrementally,
        # retrieving partial result sets combining the SPARQL sequence
        # modifiers LIMIT and OFFSET.

        # Set up the offset.
        offset = 0

        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            b, card = contact_source_aux(server, query_copy, queue, params)
            cardinality += card
            if card < limit:
                break

            offset = offset + limit

    # Close the queue
    queue.put("EOF")
    return b, cardinality


def contact_source_aux(server, query, queue, params=None):
    # Setting variables to return.
    b = None
    cardinality = 0

    payload = {'query': query, 'format': 'JSON'}
    headers = {"User-Agent":
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
               "Accept": "application/sparql-results+json"}

    if params is not None and 'keycloak' in params and 'username' in params and 'password' in params:
        valid_token = False
        if 'token' in params and 'valid_until' in params:
            current = time()
            if params['valid_until'] > current:
                valid_token = True

        if valid_token:
            token = params['token']
        else:
            token, valid_until = __get_auth_token(params['keycloak'], params['username'], params['password'])
            params['token'] = token
            params['valid_until'] = valid_until
        headers['Authorization'] = 'Bearer ' + token

    try:
        data = urllib.parse.urlencode(payload)
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


def __get_auth_token(server, username, password):
    payload = 'grant_type=client_credentials&client_id=' + username + '&client_secret=' + password
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    start = time()
    response = requests.request('POST', server, headers=headers, data=payload)
    if response.status_code != 200:
        raise Exception(str(response.status_code) + ': ' + response.text)
    return response.json()['access_token'], start + response.json()['expires_in']
