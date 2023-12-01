[![Test Status](https://github.com/SDM-TIB/DeTrusty/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/SDM-TIB/DeTrusty/actions/workflows/test.yml)
[![Latest Release](http://img.shields.io/github/release/SDM-TIB/DeTrusty.svg?logo=github)](https://github.com/SDM-TIB/DeTrusty/releases)
[![Docker Image](https://img.shields.io/badge/Docker%20Image-sdmtib/detrusty-blue?logo=Docker)](https://hub.docker.com/r/sdmtib/detrusty)
[![DOI](https://zenodo.org/badge/294416497.svg)](https://zenodo.org/badge/latestdoi/294416497)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

[![Python Versions](https://img.shields.io/pypi/pyversions/DeTrusty)](https://pypi.org/project/DeTrusty)
[![Package Format](https://img.shields.io/pypi/format/DeTrusty)](https://pypi.org/project/DeTrusty)
[![Package Status](https://img.shields.io/pypi/status/DeTrusty)](https://pypi.org/project/DeTrusty)
[![Package Version](https://img.shields.io/pypi/v/DeTrusty)](https://pypi.org/project/DeTrusty)

# ![Logo](https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/images/logo.png "Logo")

DeTrusty is a federated query engine.
At this stage, only SPARQL endpoints are supported.
DeTrusty differs from other query engines through its focus on the explainability and trustworthiness of the query result.

> [!NOTE]
> DeTrusty is under **active development!**
> The current version is a federated query engine following the SPARQL 1.1 protocol, i.e., you can use the SERVICE clause to specify the endpoints manually.
> However, some features of SPARQL 1.1 and the parts about the explainability and trustworthiness have not been implemented yet.

Currently, DeTrusty only supports ``SELECT`` queries.
The following SPARQL 1.1 operations are not supported (yet).
This list might not be exhaustive. Please, let us know if we missed something.
- Conditional functions, e.g., `IF`, `BOUND`, `COALESCE`
- Built-in functions, e.g., `isIRI`, `STRLEN`, `abs`, `floor`, `now`, `month`, `MD5`
- Specifying RDF datasets using `FROM`, `FROM NAMED`, or `GRAPH`

If you want to know more, check out the [documentation](https://sdm-tib.github.io/DeTrusty/).

## Running DeTrusty
You can use DeTrusty as a Python3 library or a Web-based service using Docker.
The documentation includes detailed examples and explanations for both scenarios.

* [DeTrusty as a Library](https://sdm-tib.github.io/DeTrusty/library.html)
* [DeTrusty as a Service](https://sdm-tib.github.io/DeTrusty/service.html)

## License
DeTrusty is licensed under GPL-3.0.
