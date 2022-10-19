__author__ = "Philipp D. Rohde"

import getopt
import os
import signal
from multiprocessing import Queue, Process, active_children
from pathlib import Path
import sys

from typing import IO

from time import time

from DeTrusty import Decomposer, Planner
from DeTrusty.Logger import get_logger
from DeTrusty.Molecule.MTManager import ConfigFile
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger(__name__)

q_name = 'Q'
time1 = 0.0
t1 = -1
tn = -1
c1 = 0
cn = 0
dt = -1
pt = -1
result_time: IO
result_trace: IO


def run_query(query, decomposition_type, sparql_one_dot_one, config, result_folder, query_id):
    global q_name
    global t1
    global tn
    global c1
    global cn
    global dt
    global pt
    global result_time
    global result_trace

    q_name = query_id
    result_time = open(os.path.join(result_folder, 'results.csv'), 'a+', encoding='utf8')
    result_trace = open(os.path.join(result_folder, 'traces.csv'), 'a+', encoding='utf8')

    global time1
    time1 = time()

    decomposer = Decomposer(query, config,
                            decompType=decomposition_type,
                            sparql_one_dot_one=sparql_one_dot_one)
    decomposed_query = decomposer.decompose()

    dt = time() - time1

    if decomposed_query is None:
        time2 = time() - time1
        t1 = time2
        tn = time2
        pt = time2
        print_info()
        print_traces()
        result_trace.close()
        result_time.close()
        return

    planner = Planner(decomposed_query, True, contact_source, 'RDF', config)
    plan = planner.createPlan()

    pt = time() - time1

    res = Queue()
    p2 = Process(target=plan.execute, args=(res,))
    p2.start()
    p3 = Process(target=conclude, args=(res, p2,))
    p3.start()
    signal.signal(12, onSignal1)

    while True:
        if p2.is_alive() and not p3.is_alive():
            try:
                os.kill(p2.pid, 9)
            except Exception as ex:
                continue
            break
        elif not p2.is_alive() and not p3.is_alive():
            break


def conclude(res, p2):
    signal.signal(12, onSignal2)
    global t1
    global tn
    global c1
    global cn
    global time1

    ri = res.get()
    if ri == 'EOF':
        next_time(time1)
        print_traces()
        print_info()
        return

    while ri != 'EOF':
        cn += 1
        if cn == 1:
            time2 = time() - time1
            t1 = time2
            c1 = 1
        next_time(time1)
        print_traces()
        ri = res.get(True)

    next_time(time1)
    print_info()

    global result_time
    global result_trace
    result_time.close()
    result_trace.close()

    p2.terminate()


def next_time(time_):
    global tn
    tn = time() - time_


def print_info():
    global tn
    global result_time
    global cn
    if tn == -1:
        tn = time() - time1
    lr = (q_name + '\t' + str(dt) + '\t' + str(pt) + '\t' + str(t1) + '\t' + str(tn) + '\t' + str(c1) + '\t' + str(cn))
    result_time.write('\n' + lr)


def print_traces():
    global tn
    global result_trace
    global cn
    if tn == -1:
        tn = time() - time1
    lt = (q_name + ',' + str(cn) + ',' + str(tn))
    result_trace.write('\n' + lt)


def onSignal1(s, stackframe):
    cs = active_children()
    for c in cs:
        try:
            os.kill(c.pid, s)
        except OSError:
            continue
    sys.exit(s)


def onSignal2(s, stackframe):
    print_info()
    sys.exit(s)


def get_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:q:o:c:r:d:")
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    query_file = None
    sparql_one_dot_one = False
    config_file = "./Config/rdfmts.json"
    result_folder = './'
    decomposition_type = "STAR"
    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        elif opt == "-q":
            query_file = arg
        elif opt == "-o":
            sparql_one_dot_one = eval(arg)
        elif opt == "-c":
            config_file = arg
        elif opt == "-r":
            result_folder = arg
        elif opt == "-d":
            decomposition_type = arg

    if not query_file:
        usage()
        sys.exit(1)

    return query_file, decomposition_type, sparql_one_dot_one, config_file, result_folder


def usage():
    usage_str = "Usage: {program} -q <query_file> -c <config_file> -d <decomposition> -o <sparql1.1> -r <result_folder>" \
                "\nwhere \n" \
                "<decomposition> is one in [STAR, EG, TRIPLE] (default STAR). STAR decomposes the query into star-shaped sub-queries, EG follows the exclusive groups approach, TRIPLE generates a triple-wise decomposition.\n" \
                "<sparql1.1> is one in [True, False] (default False), when True, no decomposition is needed\n" \
                "<result_folder> an existing folder to store results.csv and traces.csv\n"
    print(usage_str.format(program=sys.argv[0]), )


def main():
    query_file, decomposition_type, sparql_one_dot_one, config_file, result_folder = get_options()
    query_id = str(Path(query_file).stem)
    try:
        query = open(query_file, "r", encoding="utf8").read()
        config = ConfigFile(config_file)
        run_query(query, decomposition_type, sparql_one_dot_one, config, result_folder, query_id)
    except Exception as e:
        import sys
        import traceback
        exc_type, exc_value, exc_traceback = sys.exc_info()
        emsg = repr(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(emsg)


if __name__ == '__main__':
    main()
