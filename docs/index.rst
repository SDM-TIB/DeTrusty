.. |release| image:: http://img.shields.io/github/release/SDM-TIB/DeTrusty.svg?logo=github
   :target: https://github.com/SDM-TIB/DeTrusty/releases
.. |docker| image:: https://img.shields.io/badge/Docker%20Image-sdmtib/detrusty-blue?logo=Docker
   :target: https://hub.docker.com/r/sdmtib/detrusty
.. |zenodo| image:: https://zenodo.org/badge/294416497.svg
   :target: https://zenodo.org/badge/latestdoi/294416497
.. |license| image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://github.com/SDM-TIB/DeTrusty/blob/master/LICENSE
.. |python| image:: https://img.shields.io/pypi/pyversions/DeTrusty
.. |format| image:: https://img.shields.io/pypi/format/DeTrusty
.. |status| image:: https://img.shields.io/pypi/status/DeTrusty
.. |version| image:: https://img.shields.io/pypi/v/DeTrusty
   :target: https://pypi.org/project/DeTrusty

|release| |docker| |zenodo| |license| |python| |format| |status| |version|

********
DeTrusty
********

.. image:: _images/logo.png
   :align: center

DeTrusty is a federated query engine.
At this stage, only SPARQL endpoints are supported.
DeTrusty differs from other query engines through its focus on the explainability and trustworthiness of the query result.

.. NOTE::

   DeTrusty is under **active development!**
   The current version is a federated query engine following the SPARQL 1.1 protocol, i.e., you can use the SERVICE clause to specify the endpoints manually.
   However, some features of SPARQL 1.1 and the parts about the explainability and trustworthiness have not been implemented yet.

Currently, DeTrusty only supports ``SELECT`` queries.
The following SPARQL 1.1 operations are not supported (yet).
This list might not be exhaustive.
Please, let us know if we missed something.

* Conditional functions, e.g., ``IF``, ``BOUND``, ``COALESCE``
* Built-in functions, e.g., ``isIRI``, ``STRLEN``, ``abs``, ``floor``, ``now``, ``month``, ``MD5``
* Specifying RDF datasets using ``FROM``, ``FROM NAMES``, or ``GRAPH``

Known issues:
- Query parser throws an error if the last line before a ``}`` includes a comment

.. toctree::
   :hidden:

   source_description
   decomposition
   library
   service

.. toctree::
   :hidden:
   :titlesonly:

   changelog
   reference
