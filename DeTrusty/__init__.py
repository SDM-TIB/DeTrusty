__author__ = "Philipp D. Rohde"

import multiprocessing
import time
import warnings
from multiprocessing import Queue

from DeTrusty.Decomposer import Decomposer, Planner
from DeTrusty.Molecule.MTManager import Config, get_config
from DeTrusty.Wrapper.RDFWrapper import contact_source
from DeTrusty.utils import is_url, get_query_string
from .Logger import get_logger
from .__version__ import __version__

logger = get_logger(__name__)

def run_query(query: str,
              decomposition_type: str = "STAR",
              sparql_one_dot_one: bool = None,
              config: Config = get_config('./Config/rdfmts.json'),
              join_stars_locally: bool = True,
              print_result: bool = True,
              yasqe: bool = False,
              timeout: float = 0):
    """Executes a SPARQL query over a federation of SPARQL endpoints.

    The SPARQL query is decomposed based on the specified decomposition type.
    DeTrusty identifies the possible sources for each sub-query using the
    metadata collected previously. If the query contains the SERVICE clause,
    DeTrusty executed the sub-query at the specified endpoint instead.

    Parameters
    ----------
    query : str
        The SPARQL query to be executed. Might be a string holding the SPARQL query or path to
        a query file. The query file can be local or remote (accessible via GET request).
    decomposition_type : str, optional
        The decomposition type to be used for decomposing the query. Possible values
        are 'STAR' for a star-shaped decomposition, 'EG' for exclusive groups decomposition,
        and 'TRIPLE' for a triple-wise decomposition, i.e., each triple pattern of the query
        produces a sub-query. Default is 'STAR'.
    sparql_one_dot_one : bool, optional
        .. deprecated:: 0.15.0
            No longer needed. DeTrusty is using one parser now.
    config : DeTrusty.Molecule.MTManager.Config, optional
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
    timeout: float, optional
        .. warning::
            This feature is currently considered experimental and will not produce partial results!
        .. versionadded:: 0.17.0

        DeTrusty will stop the query execution once the timeout is reached.
        The timeout is specified in seconds. The default is 0 and reflects no limit.

    Returns
    -------
    dict
        A dictionary including the query answer and additional metadata following the SPARQL protocol.
        It returns an error message in the 'error' field if something went wrong. Other metadata might
        be omitted in that case.

    Examples
    --------
    The example calls assume that an object ``config`` with the source descriptions exists.

    >>> run_query('SELECT ?s WHERE { ?s a <http://example.com/Person> }', config=config)

    >>> run_query('./query.rq', config=config)

    >>> run_query('http://example.com/queries/query.rq', config=config)

    >>> run_query('./query.rq', config=config, timeout=10)

    """
    if sparql_one_dot_one is not None:
        warnings.warn(
            'The sparql_one_dot_one parameter is deprecated. DeTrusty is using only one parser now.',
            DeprecationWarning, 2
        )

    if timeout < 0:
        raise ValueError('The timeout parameter accepts only positive values but a negative one was given.')
    elif timeout == 0:
        return _execute_query(query, decomposition_type, config, join_stars_locally, print_result, yasqe)
    else:
        # execute DeTrusty with query timeout
        manager = multiprocessing.Manager()
        result_value = manager.dict()
        p = multiprocessing.Process(target=_execute_query, args=(query, decomposition_type, config, join_stars_locally, print_result, yasqe, result_value))
        p.start()
        p.join(timeout=timeout)

        if p.is_alive():
            p.terminate()
            p.join()

        if not result_value:
            return {'results': {}, 'error': 'Query timed out.'}
        else:
            return result_value._getvalue()


def _execute_query(query: str,
                   decomposition_type: str = "STAR",
                   config: Config = get_config('./Config/rdfmts.json'),
                   join_stars_locally: bool = True,
                   print_result: bool = True,
                   yasqe: bool = False,
                   return_value: dict = None):
    """Private method that actually executes a SPARQL query over a federation of SPARQL endpoints.

    The SPARQL query is decomposed based on the specified decomposition type.
    DeTrusty identifies the possible sources for each sub-query using the
    metadata collected previously. If the query contains the SERVICE clause,
    DeTrusty executed the sub-query at the specified endpoint instead.

    Parameters
    ----------
    query : str
        The SPARQL query to be executed. Might be a string holding the SPARQL query or path to
        a query file. The query file can be local or remote (accessible via GET request).
    decomposition_type : str, optional
        The decomposition type to be used for decomposing the query. Possible values
        are 'STAR' for a star-shaped decomposition, 'EG' for exclusive groups decomposition,
        and 'TRIPLE' for a triple-wise decomposition, i.e., each triple pattern of the query
        produces a sub-query. Default is 'STAR'.
    config : DeTrusty.Molecule.MTManager.Config, optional
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
    return_value : dict, optional
        An optional dictionary that can be used to pass the query result to a DictProxy
        from multiprocessing in case DeTrusty is executed with a query timeout.

    Returns
    -------
    dict
        A dictionary including the query answer and additional metadata following the SPARQL protocol.
        It returns an error message in the 'error' field if something went wrong. Other metadata might
        be omitted in that case.

    """
    if return_value is None:
        return_value = dict()

    start_time = time.time()
    decomposer = Decomposer(get_query_string(query), config,
                            decompType=decomposition_type,
                            joinstarslocally=join_stars_locally)
    decomposed_query = decomposer.decompose()

    if decomposed_query is None:
        return_value['results'] = {}
        return_value['error'] = 'The query cannot be answered by the endpoints in the federation.'
        return return_value

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
                res[key] = value
            if not yasqe:
                res['__meta__'] = {"is_verified": True}

            result.append(res)
        r = output.get()
    end_time = time.time()

    # sometimes, subprocesses are still running even though they are done
    # TODO: this is supposed to be a workaround, we should solve the issue at the source
    active = multiprocessing.active_children()
    for child in active:
        child.kill()

    return_value['head'] = {'vars': decomposed_query.variables()}
    return_value['cardinality'] = card
    return_value['results'] = {'bindings': result}
    return_value['execution_time'] = end_time - start_time
    return_value['output_version'] = '2.0'
    return return_value
