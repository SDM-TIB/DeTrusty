# v0.15.2 - 13 Feb 2024
- Use StreamHandler for loggers if FileHandler cannot be established

# v0.15.1 - 07 Feb 2024
- Fix query result format issue while creating the source descriptions 

# v0.15.0 - 01 Dec 2023
- Merge parsers
  - DeTrusty uses only one parser now, hence,
  - Deprecate sparql_one_dot_one parameter of run_query()
- Add support for parsing SPARQL queries with comments
- Fix issue with COUNT(*)

# v0.14.0 - 28 Nov 2023
- Add complex expressions
- Update return format to match with the SPARQL specification, i.e., include type and datatype, not just the value
- Fix minor issues in aggregate functions
- Fix implicit grouping
- Fix error of executing a query with no matched source if only rdf:type statement in query
- Fix issue with non-grouped optional variables
- Fix filters
  - ... for URIs
  - ... over optional variables
- Fix wrong splitting of VALUES clause when using multiple variables
- Throw error if
  - projected variables are not grouped or aggregates
  - projected variables are not defined in the body
  - variables in ORDER BY are not projected
  - variables in GROUP BY are not defined in the body
- Add functionality for ordering by multiple variables
- Adjust Xorderby to use datatypes

# v0.13.2 - 01 Nov 2023
- Fix argument parsing in create_rdfmts.py
- Docker: update Python

# v0.13.1 - 25 Oct 2023
- Change extension of Jinja templates
- Add project URLs to setup.py
- Add support for Python 3.12
- Fix planning of OPTIONAL, i.e., which implementation to choose

# v0.13.0 - 13 Oct 2023
- Add documentation to GitHub pages
- Add feature to get source description file via GET request
- Add feature to get query string from file via GET request

# v0.12.3 - 29 Jun 2023
- Fix sub-query selectivity

# v0.12.2 - 21 Jun 2023
- Update dependencies
- Docker: update Python
- Fix selectivity of sub-queries with filters

# v0.12.1 - 17 May 2023
- Fix decomposition error for typed molecules including repeated predicates
- Docker: update Python

# v0.12.0 - 02 May 2023
- Consider more cases for extracting the RDF class from an RML mapping
- Complete the source description using the endpoint if the RML mapping includes template classes
- Update dependencies

# v0.11.3 - 27 Apr 2023
- Fix duplicated BIND clause when using NHJF
- Fix query plan JSON for cases where the triples of an endpoint are not a list
- Fix searching endpoints serving predicates with prefixes
- Add operator name for Xfilter
- Fix display of constants in query plan
- Fix filter issue in triple-wise decomposition

# v0.11.2 - 23 Feb 2023
- Fix paths for query plan

# v0.11.1 - 14 Feb 2023
- Fix query variables when using SERVICE clause

# v0.11.0 - 03 Feb 2023
- Docker: update Python and PIP
- Add query plan visualization at route `/query_plan`

# v0.10.0 - 31 Jan 2023
- Added collecting source descriptions from Wikidata
- Added feature to disable interlinking in source description collection

# v0.9.1 - 06 Dec 2022
- Fixed not pushing down BIND in some cases
- Fixed missing module error in `create_rdfmts.py`

# v0.9.0 - 24 Nov 2022
- Added GROUP BY clause
- Added aggregates
- Added BIND clause
- Added ability to process simple expressions
- Added function `year`

# v0.8.0 - 05 Nov 2022
- Improved Xunion operator
- Fixed issue for filters with different data types
- Improved the RDF wrapper
- Updated Python base image to 3.11.0

# v0.7.2 - 30 Sep 2022
- Fix bug when config file is empty
- Disable caching for YASGUI
- Update YASGUI

# v0.7.1 – 19 Sep 2022
- Fix bug where sub-queries with constants where not considered for merging

# v0.7.0 – 17 Sep 2022
- Added feature to restrict the metadata collection of an endpoint to specific classes

# v0.6.4 – 16 Sep 2022
- Fix quoted special chars in query string

# v0.6.3 – 05 Sep 2022
- Added basic authentication with Base64 encoding

# v0.6.2 – 31 Aug 2022
- Add possibility to create configuration instance from JSON string
- Add method to save a configuration instance to file
- Update Python base image to 3.9.13 on bullseye

# v0.6.1 – 16 Aug 2022
- Fix a type hint for Python versions < 3.10
- Create config object on import of `DeTrusty.Molecule.MTCreation`
- Raise exceptions during metadata collection instead of just logging them
- Fix issue when using a list of endpoints and not a dictionary
- Prevent generation of parsetab.py
- Rename log from metadata creation to `.rdfmts.log`

# v0.6.0 – 13 Aug 2022
- Exclude tests from Docker image
- Fix loggers
- Update dependencies
- Add capability to query private knowledge graphs
- Update RDF Molecule Template creation
  - Collect metadata from private endpoints
  - Gather metadata from RML mappings
- Fix issue with non-ASCII characters in query 

# v0.5.1 – 27 Jul 2022
- Add checks (directory exists, file writeable) for the metadata output file before collecting the metadata
- Keep a list of all triple patterns in the decomposer
- Remove Flask from the list of dependencies of the library

# v0.5.0 – 26 Jul 2022
- Some changes in order to use DeTrusty as a library and a service

# v0.4.5 – 30 Jun 2022
- Fixed use of incorrect set of variables for OPTIONALs

# v0.4.4 – 14 Jun 2022
- Fixed request payload to work with the Wikidata endpoint (https://query.wikidata.org/sparql)

# v0.4.3 – 22 May 2022
- Fixed issue in response header when the SELECT clause included an asterisk (*) to retrieve all variables

# v0.4.2 – 21 May 2022
- Fix endpoint path behind proxy

# v0.4.1 – 20 May 2022
- Fix for joining sub-queries at remote source configuration

# v0.4.0 – 20 May 2022
- Web interface using YASGUI added
- Configuration for joining sub-queries at remote source

# v0.3.0 – 19 May 2022
- Support for VALUES clause
- Update of installation method
- Update of dependencies
- Support for new decomposition types
  - Triple-wise
  - Exclusive Groups

# v0.2.0 – 07 Feb 2022
- Support for SERVICE clause
- Minor fixes for the use as a service

# v0.1.0 – 17 Dec 2020
- First version of DeTrusty as a SPARQL 1.0 federated query engine