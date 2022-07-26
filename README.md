[![Latest Release](http://img.shields.io/github/release/SDM-TIB/DeTrusty.svg?logo=github)](https://github.com/SDM-TIB/DeTrusty/releases)
[![Docker Image](https://img.shields.io/badge/Docker%20Image-sdmtib/detrusty-blue?logo=Docker)](https://hub.docker.com/r/sdmtib/detrusty)
[![DOI](https://zenodo.org/badge/294416497.svg)](https://zenodo.org/badge/latestdoi/294416497)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

[![Python Versions](https://img.shields.io/pypi/pyversions/DeTrusty)](https://pypi.org/project/DeTrusty)
[![Package Format](https://img.shields.io/pypi/format/DeTrusty)](https://pypi.org/project/DeTrusty)
[![Package Status](https://img.shields.io/pypi/status/DeTrusty)](https://pypi.org/project/DeTrusty)
[![Package Version](https://img.shields.io/pypi/v/DeTrusty)](https://pypi.org/project/DeTrusty)

# DeTrusty

DeTrusty is a federated query engine.
At this stage, only SPARQL endpoints are supported.
DeTrusty differs from other query engines through its focus on the explainability and trustworthiness of the query result.

**Notice: DeTrusty is under active development! 
The current version is a federated query engine following the SPARQL 1.1 protocol, i.e., you can use the SERVICE clause to specify the endpoint.
However, the parts about the explainability and trustworthiness have not been implemented yet.**

DeTrusty only supports `SELECT` queries.
The following SPARQL 1.1 operations are not supported (yet):
- Aggregation functions, e.g., `COUNT`, `MAX`
- Conditional functions, e.g., `IF`, `BOUND`, `COALESCE` 
- `GROUP BY` clause (including `HAVING`)
- `BIND` clause
- Specifying RDF datasets using `FROM`, `FROM NAMED`, or `GRAPH`

This list might not be exhaustive. Please, let us know if we missed something.

## Running DeTrusty
DeTrusty can be used in two different ways: (i) as a Service by running it with Docker, and (ii) as a Python library within your own project.
Both methods will be explained in the following section.

### DeTrusty as a Service
In order to use DeTrusty as a service, you need to execute the following steps:

1. Pull the Docker image `docker pull sdmtib/detrusty:latest`
2. Start the container `docker run --name DeTrusty -p 5000:5000 -v $(pwd)/Config:/DeTrusty/Config -d sdmtib/detrusty:latest`
3. Create the file `./Config/endpoints.txt`
4. Add the URLs to the SPARQL endpoints you want to include in the federation to that file; one URL per line and accessible from within the container.
5. Now it is time to collect the metadata necessary for DeTrusty to operate as expected. `docker exec -it DeTrusty bash -c 'create_rdfmts.py -s /DeTrusty/Config/endpoints.txt'`
6. Once the metadata is collected, restart the workers in order to reload the configuration. `docker exec -it DeTrusty restart_workers.sh`
7. After restarting the workers, you can use DeTrusty to query your federation. When running DeTrusty as a service, you can access it through (i) an API, (ii) a command line interface, and (iii) a graphical user interface.

#### DeTrusty as a Service: API
You can use DeTrusty by making POST requests to its API.
If you started the container as described above, the base URL of the API is `localhost:5000`.
In the following, the different API calls are described.

##### /version
Returns the version number of DeTrusty.

Example call:

```bash
curl -X POST localhost:5000/version
```

Example output:

``DeTrusty v0.5.0``

##### /sparql
This API call is used to send a query to the federation and retrieve the result.
The result will be returned as a JSON (see example below).

Example call:

```bash
curl -X POST -d "query=SELECT ?s WHERE { ?s a <http://dbpedia.org/ontology/Scientist> } LIMIT 10" localhost:5000/sparql
```

Example output for the above query (shortened to two results):

```yaml
{
  "cardinality": 10,
  "execution_time": 0.1437232494354248,
  "output_version": "2.0",
  "head": { "vars": ["s"] },
  "results": {
    "bindings": [
      {
        "__meta__": { "is_verified": True },
        "s": {
          "type": "uri",
          "value": "http://dbpedia.org/resource/A.E._Dick_Howard"
        }
      },
      {
        "__meta__": { "is_verified": True },
        "s": {
          "type": "uri",
          "value": "http://dbpedia.org/resource/A.F.P._Hulsewé"
        }
      },
    ]
  }
}
```

- 'cardinality' is the number (integer) of results retrieved
- 'execution_time' (float) gives the time in seconds the query engine has spent collecting the results
- 'output_version' (string) indicates the version number of the output format, i.e., to differentiate the current output from possibly changed output in the future
- 'variables' (list) returns a list of the variables found in the query
- 'result' is a list of dictionaries containing the results of the query, using the variables as keys;
  metadata about the result verification is included in the key '\_\_meta\_\_'.
  The current version returns all results as verified as can be seen in the key 'is_verified' of the metadata.

When sending a SPARQL 1.1 query with the SERVICE clause, you need to set the `sparql1_1` flag to `True`:
```bash
curl -X POST -d "query=SELECT ?s WHERE { SERVICE <https://dbpedia.org/sparql> { ?s a <http://dbpedia.org/ontology/Scientist> }} LIMIT 10" -d "sparql1_1=True" localhost:5000/sparql
```

#### DeTrusty as a Service: CLI
You can also run DeTrusty from the command line.
The following example call assumes a query stored in a file `./query.sparql`.

```bash
docker exec -it DeTrusty bash -c 'python runDeTrusty.py -q ./query.sparql'
```

If you want to execute a SPARQL 1.1 query with the SERVICE clause, add `-o True`.

#### DeTrusty as a Service: GUI
Starting with version 0.4.0, DeTrusty also comes with a Web interface.
Hence, you can run queries using your favorite browser.
The Web interface uses the JavaScript library [YASGUI](https://triply.cc/docs/yasgui).
If you started the container as described above, the interface is accessible at `localhost:5000/sparql`.

### DeTrusty as a Library
DeTrusty can also be used as a library. You first need to install it via `python3 -m pip install DeTrusty`.
The following example script shows how you can use DeTrusty within your project.

```python
from DeTrusty.Molecule.MTCreation import create_rdfmts
from DeTrusty import run_query

endpoints = ['http://url_to_endpoint_1', 'https://url_to_endpoint_2:port/sparql']
create_rdfmts(endpoints, './Config/rdfmts.json')

query = "SELECT ?s WHERE { ?s a <http://dbpedia.org/ontology/Scientist> } LIMIT 10"
query_result = run_query(query)

print(query_result)
```

Of course, you can also further process the results according to your needs.
If you want to execute a SPARQL 1.1 query with the SERVICE clause, add the parameter `sparql_one_dot_one=True` to your call of `run_query`.

## License
DeTrusty is licensed under GPL-3.0.
