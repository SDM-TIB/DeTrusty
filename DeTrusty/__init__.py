__author__ = "Philipp D. Rohde"

import re, sys
import time
from multiprocessing import Queue

from DeTrusty.Decomposer import Decomposer, Planner
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Wrapper.RDFWrapper import contact_source


re_https = re.compile("https?://")


def run_query(query: str,
              decomposition_type: str = "STAR",
              sparql_one_dot_one: bool = False,
              config: ConfigFile = ConfigFile('./Config/rdfmts.json'),
              join_stars_locally: bool = True,
              print_result: bool = True,
              yasqe: bool = False):
    """Executes a SPARQL query over a federation of SPARQL endpoints.

    The SPARQL query is decomposed based on the specified decomposition type.
    DeTrusty identifies the possible sources for each sub-query using the
    metadata collected previously. If the query contains the SERVICE clause,
    DeTrusty executed the sub-query at the specified endpoint instead.

    Parameters
    ----------
    query : str
        The SPARQL query to be executed.
    decomposition_type : str, optional
        The decomposition type to be used for decomposing the query. Possible values
        are 'STAR' for a star-shaped decomposition, 'EG' for exclusive groups decomposition,
        and 'TRIPLE' for a triple-wise decomposition, i.e., each triple pattern of the query
        produces a sub-query. Default is 'STAR'.
    sparql_one_dot_one : bool, optional
        Indicates whether the query includes the SERVICE clause.
        'True' meaning the SERVICE clause is present in the query, 'False' otherwise.
        Default is 'False'.
    config : DeTrusty.Molecule.MTManager.ConfigFile, optional
        The configuration holding the metadata about the federation over which the
        SPARQL query should be executed. If no value is specified, DeTrusty will
        attempt to load the configuration from `./Config/rdfmts.json`.
    join_stars_locally : bool, optional
        Indicates whether joins should be performed at the query engine.
        'True' meaning joins will be performed in DeTrusty, 'False' leads to joins
        being executed in the sources if possible. Default behavior is join execution
        at the query engine level.
    print_result : bool, optional
        Indicates whether the actual query result should be returned.
        'True' meaning the result will be included in the answer.
        'False' only returns the metadata of the query result, like the cardinality.
        Default is 'True'.
    yasqe : bool, optional
        Indicates whether the SPARQL query was sent from the YASGUI interface of
        DeTrusty's Web interface. This is a workaround for YASQE not being able
        to show the query results when the validation data is included.
        Set to 'True' to omit the validation data. Default is 'False'.

    Returns
    -------
    dict
        A dictionary including the query answer and additional metadata following the SPARQL protocol.
        It returns an error message in the 'error' field if something went wrong. Other metadata might
        be omitted in that case.

    """
    start_time = time.time()
    decomposer = Decomposer(query, config,
                            decompType=decomposition_type,
                            joinstarslocally=join_stars_locally,
                            sparql_one_dot_one=sparql_one_dot_one)
    decomposed_query = decomposer.decompose()

    if decomposed_query is None:
        return {"results": {}, "error": "The query cannot be answered by the endpoints in the federation."}

    planner = Planner(decomposed_query, True, contact_source, 'RDF', config)
    plan = planner.createPlan()

    output = Queue()
    plan.execute(output)

    result = []
    r = output.get()
    card = 0
    while r != 'EOF':
        card += 1
        if print_result:
            res = {}
            for key, value in r.items():
                res[key] = {"value": value, "type": "uri" if re_https.match(value) else "literal"}
            if not yasqe:
                res['__meta__'] = {"is_verified": True}

            result.append(res)
        r = output.get()
    end_time = time.time()

    return {"head": {"vars": decomposed_query.variables()},
            "cardinality": card,
            "results": {"bindings": result} if print_result else "printing results was disabled",
            "execution_time": end_time - start_time,
            "output_version": "2.0"}
