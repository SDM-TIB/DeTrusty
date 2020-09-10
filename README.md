# DeTrusty

DeTrusty is a federated query engine.
At this stage, only SPARQL endpoints are supported.
DeTrusty differs from other query engines through its focus on the explainability and trustworthiness of the query result.

**Notice: DeTrusty is under active development! This version is only a mock-up.
The mock-up version simply forwards the query to all endpoints in the federation.
The DISTINCT operator is performed in the engine if necessary.
However, operators like LIMIT are not yet implemented at query engine level.
In such cases, the query result is correct if and only if the federation consists of a single endpoint.**

## Running DeTrusty
In order to run DeTrusty, build the Docker image from the source code:

``docker build . -t sdmtib/detrusty:mockup``

Once the Docker image is built, you can start DeTrusty:

``docker run --name DeTrusty -d -p 5000:5000 sdmtib/detrusty:mockup``

You can now start to make POST requests to the DeTrusty API running at localhost:5000.

## DeTrusty API
You can use DeTrusty by making POST requests to its API.
In the following, the different API calls are described.

### /version
Returns the version number of DeTrusty.

Example call:

```bash
curl -X POST localhost:5000/version
```

Example output:

``DeTrusty Mock-Up``

### /create_datasource_description
This API call is used to create the datasource description for the endpoints in the federation that DeTrusty is used to query for.
The URL for the endpoints needs to be transmitted as a comma-separated list.

Example call:

```bash
curl -X POST -d "endpoints=http://dbpedia.org/sparql,http://wifo5-03.informatik.uni-mannheim.de/drugbank/sparql" localhost:5000/create_datasource_description
```

Example output:

``Datasource description updated.``

### /sparql
This API call is used to send a query to the federation and retrieve the result.
The result will be returned as a JSON (see example below).

Example call:

```bash
curl -X POST -d "query=SELECT ?s WHERE { ?s a <http://dbpedia.org/ontology/Scientist> }" localhost:5000/sparql
```

Example output for the above query (shortened to two results):

```yaml
{
    "cardinality": 10,
    "execution_time": 0.1437232494354248,
    "output_version": "1",
    "variables": ["s"],
    "result": [
        {
            "s": "http://dbpedia.org/resource/A.E._Dick_Howard",
            "__meta__": {"is_verified": True}
        },
        {
            "s": "http://dbpedia.org/resource/A.F.P._Hulsewé",
            "__meta__": {"is_verified": True}
        }
    ]
}
```
'cardinality' is the number (integer) of results retrieved,
'execution_time' (float) gives the time in seconds the query engine has spent collecting the results,
'output_version' (string) indicates the version number of the output format, i.e., to differentiate the current output from possibly changed output in the future,
'variables' (list) returns a list of the variables found in the query,
'result' is a list of dictionaries containing the results of the query, using the variables as keys;
metadata about the result verification is included in the key '\_\_meta\_\_'.
The mock-up version returns all results as verified as can be seen in the key 'is_verified' of the metadata.

## License
DeTrusty is licensed under GPL-3.0.