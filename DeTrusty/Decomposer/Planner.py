__author__ = 'Kemele M. Endris and Philipp D. Rohde'

import urllib.parse
import urllib.request
from multiprocessing import Process, Queue

import DeTrusty.Decomposer.utils as utils
from DeTrusty.Decomposer.Tree import Leaf, Node
from DeTrusty.Operators.AnapsidOperators.Xbind import Xbind
from DeTrusty.Operators.AnapsidOperators.Xdistinct import Xdistinct
from DeTrusty.Operators.AnapsidOperators.Xfilter import Xfilter
from DeTrusty.Operators.AnapsidOperators.Xgjoin import Xgjoin
from DeTrusty.Operators.AnapsidOperators.Xgoptional import Xgoptional
from DeTrusty.Operators.AnapsidOperators.Xgroupby import Xgroupby
from DeTrusty.Operators.AnapsidOperators.Xhaving import Xhaving
from DeTrusty.Operators.AnapsidOperators.Xlimit import Xlimit
from DeTrusty.Operators.AnapsidOperators.Xoffset import Xoffset
from DeTrusty.Operators.AnapsidOperators.Xorderby import Xorderby
from DeTrusty.Operators.AnapsidOperators.Xproject import Xproject
from DeTrusty.Operators.AnapsidOperators.Xunion import Xunion
from DeTrusty.Operators.BlockingOperators.Union import Union
from DeTrusty.Operators.NonBlockingOperators.NestedHashJoinFilter import NestedHashJoinFilter as NestedHashJoin
from DeTrusty.Operators.NonBlockingOperators.NestedHashOptionalFilter import  NestedHashOptionalFilter as NestedHashOptional
from DeTrusty.Sparql.Parser.services import Bind, Filter, Service, Optional, UnionBlock, JoinBlock


class Planner(object):

    def __init__(self, query,  wc, contact, endpointType, config):
        self.query = query
        self.withcounts = wc
        self.contact = contact
        self.endpType = endpointType
        self.config = config
        self.buffersize = 16384
        self.adaptive = True

    def createPlan(self):
        if self.query is None:
            return None

        query = self.query
        operatorTree = self.includePhysicalOperatorsQuery()
        aggs = list()

        over_all_triples = utils.collectVars(query.args, query.group_by, query.having, aggs)  # TODO: test & fix
        # print(query.args, query.group_by, query.having, aggs, over_all_triples)

        # Adds the group by operator to the plan.
        if (len(query.group_by) > 0):
            operatorTree = TreePlan(Xgroupby(query.group_by), operatorTree.vars, operatorTree)

        # Adds the group by operator to the plan.
        # if aggs:
            # operatorTree = TreePlan(Xaggregate(aggs, over_all_triples, query.group_by, query.prefs), operatorTree.vars, operatorTree)

        # Adds the having operator to the plan.
        if query.having is not None:
            operatorTree = TreePlan(Xhaving(query.having), operatorTree.vars, operatorTree)

        # Adds the order by operator to the plan.
        if (len(query.order_by) > 0):
            operatorTree = TreePlan(Xorderby(query.order_by), operatorTree.vars, operatorTree)

        # Adds the project operator to the plan.
        operatorTree = TreePlan(Xproject(query.args), operatorTree.vars, operatorTree)

        # Adds the distinct operator to the plan.
        if (query.distinct):
            operatorTree = TreePlan(Xdistinct(None), operatorTree.vars, operatorTree)

        # Adds the offset operator to the plan.
        if (query.offset != -1):
            operatorTree = TreePlan(Xoffset(None, query.offset), operatorTree.vars, operatorTree)

        # Adds the limit operator to the plan.
        if (query.limit != -1):
            # print "query.limit", query.limit
            operatorTree = TreePlan(Xlimit(None, query.limit), operatorTree.vars, operatorTree)

        return operatorTree

    def includePhysicalOperatorsQuery(self):
        return self.includePhysicalOperatorsUnionBlock(self.query.body)

    def includePhysicalOperatorsUnionBlock(self, ub):
        r = []
        for jb in ub.triples:
            pp = self.includePhysicalOperatorsJoinBlock(jb)
            r.append(pp)

        while len(r) > 1:
            left = r.pop(0)
            right = r.pop(0)
            all_variables = left.vars | right.vars
            if self.adaptive:
                n = TreePlan(Xunion(left.vars, right.vars), all_variables, left, right)
            else:
                n = TreePlan(Union(left.vars, right.vars, self.query.distinct), all_variables, left, right)
            r.append(n)

        if len(r) == 1:
            n = r[0]
            for f in ub.filters:
                n = TreePlan(Xfilter(f), n.vars, n)
            return n
        else:
            return None

    def includePhysicalOperatorsJoinBlock(self, jb):
        tl = []
        ol = []
        if isinstance(jb.triples, list):
            for bgp in jb.triples:
                if isinstance(bgp, Node) or isinstance(bgp, Leaf):
                    tl.append(self.includePhysicalOperators(bgp))
                elif isinstance(bgp, Optional):
                    ol.append(self.includePhysicalOperatorsUnionBlock(bgp.bgg))
                elif isinstance(bgp, UnionBlock):
                    tl.append(self.includePhysicalOperatorsUnionBlock(bgp))
        elif isinstance(jb.triples, Node) or isinstance(jb.triples, Leaf):
            tl = [self.includePhysicalOperators(jb.triples)]
        else:  # this should never be the case..
            pass

        while len(tl) > 1:
            l = tl.pop(0)
            r = tl.pop(0)
            n = self.includePhysicalOperatorJoin(l, r)
            tl.append(n)

        if len(tl) == 1:
            nf = self.includePhysicalOperatorsOptional(tl[0], ol)
            if isinstance(tl[0], TreePlan) and (isinstance(tl[0].operator, Xfilter) or isinstance(tl[0].operator, Xbind)):
                return nf
            else:
                if len(jb.filters) > 0 and isinstance(tl[0].operator, Xfilter):
                    for f in jb.filters:
                        nf = TreePlan(Xfilter(f), nf.vars, nf)
                if len(jb.filters) > 0 and isinstance(tl[0].operator, Xbind):
                    for f in jb.filters:
                        nf = TreePlan(Xbind(f), nf.vars, nf)
                    return nf
                else:
                    return nf
        else:
            return None

    def includePhysicalOperators(self, tree):
        if isinstance(tree, Leaf):
            if isinstance(tree.service, Service):
                if tree.filters == []:
                    return IndependentOperator(self.query, tree, self.contact, self.config)
                else:
                    n = IndependentOperator(self.query, tree, self.contact, self.config)
                    for f in tree.filters:
                        vars_f = f.getVarsName()
                        if set(n.vars) & set(vars_f) == set(vars_f):
                            n = TreePlan(Xfilter(f), n.vars, n)
                    return n
            elif isinstance(tree.service, UnionBlock):
                return self.includePhysicalOperatorsUnionBlock(tree.service)
            elif isinstance(tree.service, JoinBlock):
                if tree.filters == []:
                    return self.includePhysicalOperatorsJoinBlock(tree.service)
                else:
                    n = self.includePhysicalOperatorsJoinBlock(tree.service)
                    for f in tree.filters:
                        vars_f = f.getVarsName()
                        if set(n.vars) & set(vars_f) == set(vars_f):
                            n = TreePlan(Xfilter(f), n.vars, n)
                    return n
            else:
                print("tree.service" + str(type(tree.service)) + str(tree.service))
                print("Error Type not considered")

        elif isinstance(tree, Node):
            left_subtree = self.includePhysicalOperators(tree.left)
            right_subtree = self.includePhysicalOperators(tree.right)
            if tree.filters == []:
                return self.includePhysicalOperatorJoin(left_subtree, right_subtree)
            else:
                n = self.includePhysicalOperatorJoin(left_subtree, right_subtree)
                for f in tree.filters:
                    vars_f = f.getVarsName()
                    if set(n.vars) & set(vars_f) == set(vars_f):
                        if isinstance(f, Filter):
                            n = TreePlan(Xfilter(f), n.vars, n)
                    if isinstance(f, Bind):
                        n.vars = set(n.vars) | set(vars_f)
                        if n.vars & set(vars_f) == set(vars_f):
                            n = TreePlan(Xbind(f), n.vars, n)
            return n

    def includePhysicalOperatorJoinX(self, l, r):
        join_variables = l.vars & r.vars
        all_variables = l.vars | r.vars
        n, dependent_join = self.joinIndependentAnapsid(l, r)
        if n and isinstance(n.left, IndependentOperator) and isinstance(n.left.tree, Leaf):
            if (n.left.constantPercentage() <= 0.5) and not (n.left.tree.service.allTriplesGeneral()):
                n.left.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
        # elif not decided:
            # n = TreePlan(Xgjoin(join_variables), all_variables, l, r)
        # print "n: ", n
        if isinstance(n.right, IndependentOperator) and isinstance(n.right.tree, Leaf):
            if not dependent_join:
                if (n.right.constantPercentage() <= 0.5) and not (n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit right ..."
            else:
                new_constants = 0
                for v in join_variables:
                    new_constants = new_constants + n.right.query.show().count(v)
                if ((n.right.constantNumber() + new_constants) / n.right.places() <= 0.5) and not (n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
        return n

    def includePhysicalOperatorJoin(self, l, r):
        join_variables = l.vars & r.vars
        all_variables = l.vars | r.vars
        # noInstantiatedLeftStar = False
        # noInstantiatedRightStar = False
        lowSelectivityLeft = l.allTriplesLowSelectivity()
        lowSelectivityRight = r.allTriplesLowSelectivity()
        n = None
        dependent_join = False

        if isinstance(l, IndependentOperator) and isinstance(l.tree.service.triples, list) and l.tree.service.triples[0].subject.constant:
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
        elif isinstance(r, IndependentOperator) and isinstance(r.tree.service.triples, list) and r.tree.service.triples[0].subject.constant:
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                dependent_join = True
        elif isinstance(r, TreePlan) and r.operator.__class__.__name__ == "Xunion" and \
                isinstance(l, TreePlan) and l.operator.__class__.__name__ == "Xunion":
            # both are Union operators
            n = TreePlan(Xgjoin(join_variables), all_variables, l, r)

        elif not lowSelectivityLeft and not lowSelectivityRight and (
                not isinstance(l, TreePlan) or not isinstance(r, TreePlan)):
            # if both are selective and one of them (or both) are Independent Operator
            if len(join_variables) > 0:
                if l.constantPercentage() > r.constantPercentage():
                    if not isinstance(r, TreePlan):
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                        dependent_join = True
                    else:
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                else:
                    if not isinstance(l, TreePlan):
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                        dependent_join = True
                    else:
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)

        elif not lowSelectivityLeft and lowSelectivityRight and not isinstance(r, TreePlan):

            # If left is selective, if left != NHJ and right != NHJ -> NHJ (l,r)
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True

                # if not isinstance(l, TreePlan):
                #     if isinstance(r, TreePlan):
                #         if not isinstance(r.operator, NestedHashJoin) and not isinstance(r.operator, Xgjoin):
                #             n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                #             dependent_join = True
                #     else:
                #         # IF both are Independent Operators
                #         n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                #         dependent_join = True
                # elif isinstance(l, TreePlan) and not isinstance(l.operator, NestedHashJoin):
                #     if not isinstance(r, TreePlan):
                #         n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                #         dependent_join = True
                #     elif isinstance(r, TreePlan) and not isinstance(r.operator, NestedHashJoin) and not isinstance(r.operator, Xgjoin):
                #         n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                #         dependent_join = True

        elif lowSelectivityLeft and not lowSelectivityRight and not isinstance(l, TreePlan):
            # if right is selective if left != NHJ and right != NHJ -> NHJ (r,l)
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                dependent_join = True

                # if not isinstance(r, TreePlan):
                #     if isinstance(l, TreePlan):
                #         if not isinstance(l.operator, NestedHashJoin) and not isinstance(l.operator, Xgjoin):
                #             n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                #             dependent_join = True
                #     else:
                #         # IF both are Independent Operators
                #         n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                #         dependent_join = True
                # elif isinstance(r, TreePlan) and not isinstance(r.operator, NestedHashJoin):
                #     if not isinstance(l, TreePlan):
                #         n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                #         dependent_join = True
                #     elif isinstance(l, TreePlan) and not isinstance(l.operator, NestedHashJoin) and not isinstance(l.operator, Xgjoin):
                #         n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                #         dependent_join = True
        elif not lowSelectivityLeft and lowSelectivityRight \
                and (isinstance(l, TreePlan) and not l.operator.__class__.__name__ == "NestedHashJoinFilter") \
                and (isinstance(r, TreePlan) and not (r.operator.__class__.__name__ == "NestedHashJoinFilter"
                                                      or r.operator.__class__.__name__ == "Xgjoin")):
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
        elif lowSelectivityLeft and not lowSelectivityRight and (isinstance(r, TreePlan) and not r.operator.__class__.__name__ == "NestedHashJoinFilter") \
                and (isinstance(l, TreePlan) and not (l.operator.__class__.__name__ == "NestedHashJoinFilter" or l.operator.__class__.__name__ == "Xgjoin")):
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                dependent_join = True
        elif lowSelectivityLeft and lowSelectivityRight and isinstance(l, IndependentOperator) and isinstance(r, IndependentOperator):
            # both are non-selective and both are Independent Operators
            n = TreePlan(Xgjoin(join_variables), all_variables, r, l)

        if n is None:
            n = TreePlan(Xgjoin(join_variables), all_variables, l, r)

        if n and isinstance(n.left, IndependentOperator) and isinstance(n.left.tree, Leaf):
            if (n.left.constantPercentage() <= 0.5) and not (n.left.tree.service.allTriplesGeneral()):
                n.left.tree.service.limit = 10000  # Fixed value, this can be learnt in the future

        if isinstance(n.right, IndependentOperator) and isinstance(n.right.tree, Leaf):
            if not dependent_join:
                if (n.right.constantPercentage() <= 0.5) and not (n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit right ..."
            else:
                new_constants = 0
                for v in join_variables:
                    new_constants = new_constants + n.right.query.show().count(v)
                if ((n.right.constantNumber() + new_constants) / n.right.places() <= 0.5) and not (n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
        return n

    def includePhysicalOperatorsOptional(self, left, rightList):
        l = left
        for right in rightList:
            all_variables = l.vars | right.vars
            lowSelectivityLeft = l.allTriplesLowSelectivity()
            lowSelectivityRight = right.allTriplesLowSelectivity()
            join_variables = l.vars & right.vars
            dependent_op = False
            # if left.operator.__class__.__name__ == "NestedHashJoinFilter":
            #     l = TreePlan(Xgoptional(left.vars, right.vars), all_variables, l, right)
            # Case 1: left operator is highly selective and right operator is low selective
            if not (lowSelectivityLeft) and lowSelectivityRight and not (isinstance(right, TreePlan)):
                l = TreePlan(NestedHashOptional(l.vars, right.vars), all_variables, l, right)
                dependent_op = True

            # Case 2: left operator is low selective and right operator is highly selective
            elif lowSelectivityLeft and not (lowSelectivityRight) and not (isinstance(right, TreePlan)):
                l = TreePlan(NestedHashOptional(l.vars, right.vars), all_variables, right, l)
                dependent_op = True

            elif not lowSelectivityLeft and lowSelectivityRight and not (isinstance(left, TreePlan) and (left.operator.__class__.__name__ == "NestedHashJoinFilter" or left.operator.__class__.__name__ == "Xgjoin")) \
                    and not (isinstance(right, IndependentOperator)) \
                    and not (right.operator.__class__.__name__ == "NestedHashJoinFilter" or right.operator.__class__.__name__ == "Xgjoin") \
                    and (right.operator.__class__.__name__ == "Xunion"):
                l = TreePlan(NestedHashOptional(l.vars, right.vars), all_variables, l, right)
                dependent_op = True
            # Case 3: both operators are low selective
            else:
                l = TreePlan(Xgoptional(l.vars, right.vars), all_variables, l, right)
                # print "Planner CASE 3: xgoptional"

            if isinstance(l.left, IndependentOperator) and isinstance(l.left.tree, Leaf) and not l.left.tree.service.allTriplesGeneral():
                if l.left.constantPercentage() <= 0.5:
                    l.left.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit optional left ..."

            if isinstance(l.right, IndependentOperator) and isinstance(l.right.tree, Leaf):
                if not dependent_op:
                    if (l.right.constantPercentage() <= 0.5) and not (l.right.tree.service.allTriplesGeneral()):
                        l.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                        # print "modifying limit optional right ..."
                else:
                    new_constants = 0
                    for v in join_variables:
                        new_constants = new_constants + l.right.query.show().count(v)
                    if ((l.right.constantNumber() + new_constants) / l.right.places() <= 0.5) and not l.right.tree.service.allTriplesGeneral():
                        l.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                        # print "modifying limit optional right ..."

        return l

    def joinIndependentAnapsid(self, l, r):
        join_variables = l.vars & r.vars
        all_variables = l.vars | r.vars
        noInstantiatedLeftStar = False
        noInstantiatedRightStar = False
        lowSelectivityLeft = l.allTriplesLowSelectivity()
        lowSelectivityRight = r.allTriplesLowSelectivity()

        dependent_join = False
        # if (noInstantiatedRightStar) or ((not wc) and (l.constantPercentage() >= 0.5) and (len(join_variables) > 0) and c):
        # Case 1: left operator is highly selective and right operator is low selective
        if not (lowSelectivityLeft) and lowSelectivityRight and not (isinstance(r, TreePlan)):
            n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
            dependent_join = True
            # print "Planner CASE 1: nested loop", type(r)
        # Case 2: left operator is low selective and right operator is highly selective
        elif lowSelectivityLeft and not (lowSelectivityRight) and not (isinstance(l, TreePlan)):
            n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
            dependent_join = True
            # print "Planner CASE 2: nested loop swapping plan", type(r)
        elif not (lowSelectivityLeft) and lowSelectivityRight and (
                not (isinstance(l, TreePlan)) or not (l.operator.__class__.__name__ == "NestedHashJoinFilter")) and (
                not (isinstance(r, TreePlan)) or not (
                r.operator.__class__.__name__ == "Xgjoin" or r.operator.__class__.__name__ == "NestedHashJoinFilter")):
            if (isinstance(r, TreePlan) and (set(l.vars) & set(r.operator.vars_left) != set([])) and (
                    set(l.vars) & set(r.operator.vars_right) != set([]))):
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
            elif (isinstance(l, TreePlan) and (set(r.vars) & set(l.operator.vars_left) != set([])) and (
                    set(r.vars) & set(l.operator.vars_right) != set([]))):
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
            else:
                n = TreePlan(Xgjoin(join_variables), all_variables, l, r)
            # print "Planner case 2.5", type(r)
        # Case 3: both operators are low selective

        else:
            n = TreePlan(Xgjoin(join_variables), all_variables, l, r)
            # print "Planner CASE 3: xgjoin"

        if isinstance(n.left, IndependentOperator) and isinstance(n.left.tree, Leaf):
            if (n.left.constantPercentage() <= 0.5) and not (n.left.tree.service.allTriplesGeneral()):
                n.left.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                # print "modifying limit left ..."

        if isinstance(n.right, IndependentOperator) and isinstance(n.right.tree, Leaf):
            if not (dependent_join):
                if (n.right.constantPercentage() <= 0.5) and not (n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit right ..."
            else:
                new_constants = 0
                for v in join_variables:
                    new_constants = new_constants + n.right.query.show().count(v)
                if ((n.right.constantNumber() + new_constants) / n.right.places() <= 0.5) and not (
                n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit right ..."

        return n, dependent_join

    def joinIndependentMULDER(self, l, r):
        join_variables = l.vars & r.vars
        all_variables = l.vars | r.vars
        # noInstantiatedLeftStar = False
        # noInstantiatedRightStar = False
        lowSelectivityLeft = l.allTriplesLowSelectivity()
        lowSelectivityRight = r.allTriplesLowSelectivity()
        n = None
        dependent_join = False

        if isinstance(l, IndependentOperator) and l.tree.service.triples[0].subject.constant:
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
        elif isinstance(r, IndependentOperator) and r.tree.service.triples[0].subject.constant:
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                dependent_join = True
        elif isinstance(r, TreePlan) and r.operator.__class__.__name__ == "Xunion" and \
                isinstance(l, TreePlan) and l.operator.__class__.__name__ == "Xunion":
            # both are Union operators
            n = TreePlan(Xgjoin(join_variables), all_variables, l, r)
        elif not lowSelectivityLeft and not lowSelectivityRight and (
                not isinstance(l, TreePlan) or not isinstance(r, TreePlan)):
            # if both are selective and one of them (or both) are Independent Operator
            if len(join_variables) > 0:
                if l.constantPercentage() > r.constantPercentage():
                    if not isinstance(r, TreePlan):
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                        dependent_join = True
                    else:
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                else:
                    if not isinstance(l, TreePlan):
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                        dependent_join = True
                    else:
                        n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)

        elif not lowSelectivityLeft and lowSelectivityRight and not isinstance(r, TreePlan):

            # If left is selective, if left != NHJ and right != NHJ -> NHJ (l,r)
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
        elif lowSelectivityLeft and not lowSelectivityRight and not isinstance(l, TreePlan):
            # if right is selective if left != NHJ and right != NHJ -> NHJ (r,l)
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                dependent_join = True
        elif not lowSelectivityLeft and lowSelectivityRight and not l.__class__.__name__ == "NestedHashJoinFilter" and not (
                r.__class__.__name__ == "NestedHashJoinFilter" or r.__class__.__name__ == "Xgjoin"):
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, l, r)
                dependent_join = True
        elif lowSelectivityLeft and not lowSelectivityRight and not r.__class__.__name__ == "NestedHashJoinFilter" and not (
                l.__class__.__name__ == "NestedHashJoinFilter" or l.__class__.__name__ == "Xgjoin"):
            if len(join_variables) > 0:
                n = TreePlan(NestedHashJoin(join_variables), all_variables, r, l)
                dependent_join = True
        elif lowSelectivityLeft and lowSelectivityRight and isinstance(l, IndependentOperator) and isinstance(r, IndependentOperator):
            # both are non-selective and both are Independent Operators
            n = TreePlan(Xgjoin(join_variables), all_variables, r, l)

        if n is None:
            n = TreePlan(Xgjoin(join_variables), all_variables, l, r)

        if isinstance(n.left, IndependentOperator) and isinstance(n.left.tree, Leaf):
            if (n.left.constantPercentage() <= 0.5) and not (n.left.tree.service.allTriplesGeneral()):
                n.left.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                # print "modifying limit left ..."

        if isinstance(n.right, IndependentOperator) and isinstance(n.right.tree, Leaf):
            if not (dependent_join):
                if (n.right.constantPercentage() <= 0.5) and not (n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit right ..."
            else:
                new_constants = 0
                for v in join_variables:
                    new_constants = new_constants + n.right.query.show().count(v)
                if ((n.right.constantNumber() + new_constants) / n.right.places() <= 0.5) and not (
                n.right.tree.service.allTriplesGeneral()):
                    n.right.tree.service.limit = 10000  # Fixed value, this can be learnt in the future
                    # print "modifying limit right ..."

        return n, dependent_join


class TreePlan(object):
    """
    Represents a plan to be executed by the engine.

    It is composed by a left node, a right node, and an operator node.
    The left and right nodes can be leaves to contact sources, or subtrees.
    The operator node is a physical operator, provided by the engine.

    The execute() method evaluates the plan.
    It creates a process for every node of the plan.
    The left node is always evaluated.
    If the right node is an independent operator or a subtree, it is evaluated.
    """
    def __init__(self, operator, vars, left=None, right=None):
        self.operator = operator
        self.vars = vars
        self.left = left
        self.right = right
        self.cardinality = None
        self.joinCardinality = []

    def __repr__(self):
        return self.aux(" ")

    def instantiate(self, d):
        l = None
        r = None
        if self.left:
            l = self.left.instantiate(d)
        if self.right:
            r = self.right.instantiate(d)
        newvars = self.vars - set(d.keys())

        return TreePlan(self.operator.instantiate(d), newvars, l, r)

    def instantiateFilter(self, d, filter_str):
        l = None
        r = None
        if self.left:
            l = self.left.instantiateFilter(d, filter_str)
        if self.right:
            r = self.right.instantiateFilter(d, filter_str)
        newvars = self.vars - set(d)
        return TreePlan(self.operator.instantiateFilter(d, filter_str), newvars, l, r)

    def allTriplesLowSelectivity(self):
        a = True
        if self.left:
            a = self.left.allTriplesLowSelectivity()
        if self.right:
            a = a and self.right.allTriplesLowSelectivity()
        return a

    def places(self):
        p = 0
        if self.left:
            p = self.left.places()
        if self.right:
            p = p + self.right.places()
        return p

    def constantNumber(self):
        c = 0
        if self.left:
            c = self.left.constantNumber()
        if self.right:
            c = c + self.right.constantNumber()
        return c

    def constantPercentage(self):
        return self.constantNumber()/self.places()

    def getCardinality(self):
        if self.cardinality is None:
            self.cardinality = self.operator.getCardinality(self.left, self.right)
        return self.cardinality

    def getJoinCardinality(self, vars):
        c = None
        for (v, c2) in self.joinCardinality:
            if v == vars:
                c = c2
                break
        if c is None:
            c = self.operator.getJoinCardinality(self.left, self.right, vars)
            self.joinCardinality.append((vars, c))
        return c

    def aux(self, n):
        s = n + str(self.operator) + "\n" + n + str(self.vars) + "\n"
        if self.left:
            s = s + self.left.aux(n+"  ")

        if self.right:
            s = s + self.right.aux(n + "  ")
        return s

    def json(self, triples=None, sub_queries=None):
        if triples is None:
            triples = {}
        if sub_queries is None:
            sub_queries = [0]
        tree = {'name': self.operator.name}
        children = []
        if self.left:
            child, _ = self.left.json(triples, sub_queries)
            children.append(child)
        if self.right:
            child, _ = self.right.json(triples, sub_queries)
            children.append(child)
        if children:
            tree['children'] = children
        return tree, triples

    def execute(self, outputqueue, processqueue=Queue()):
        # Evaluates the execution plan.
        if self.left:  # and this.right: # This line was modified by mac in order to evaluate unary operators
            qleft  = Queue()
            qright = Queue()

            # The left node is always evaluated.
            # Create process for left node
            # print("self.right:", self.right)
            # print("self.left:", self.left)

            p1 = Process(target=self.left.execute, args=(qleft, processqueue, ))
            p1.start()
            # processqueue.put(p1.pid)
            if "Nested" in self.operator.__class__.__name__:
                p3 = Process(target=self.operator.execute, args=(qleft, self.right, outputqueue, processqueue, ))
                p3.start()
                # processqueue.put(p3.pid)
                return

            # Check the right node to determine if evaluate it or not.
            if self.right and ((self.right.__class__.__name__ == "IndependentOperator") or (self.right.__class__.__name__ == "TreePlan")):
                p2 = Process(target=self.right.execute, args=(qright, processqueue, ))
                p2.start()
                # processqueue.put(p2.pid)
            else:
                qright = self.right  # qright.put("EOF")

            # Create a process for the operator node.
            p = Process(target=self.operator.execute, args=(qleft, qright, outputqueue, processqueue, ))
            # print("left and right")
            # Execute the plan
            p.start()
            # processqueue.put(p.pid)


class IndependentOperator(object):
    """
    Implements an operator that can be resolved independently.

    It receives as input the url of the server to be contacted, the
    filename that contains the query, the header size of the messages.

    The execute() method reads tuples from the input queue and
    response message and the buffer size (length of the string)
    place them in the output queue.
    """
    def __init__(self, query, tree, c, config):
        (e, sq, vs) = tree.getInfoIO(query)
        self.contact = c
        self.server = e
        self.query = query
        self.tree = tree
        self.query_str = sq
        self.vars = vs
        self.buffersize = 163840
        self.config = config
        self.cardinality = None
        self.joinCardinality = []
        # self.limit = limit

    def __repr__(self):
        return str(self.tree)

    def json(self, triples, sub_queries):
        sub_queries[0] += 1
        name = 'SSQ' + str(sub_queries[0])
        triples[name] = {
            'endpoint': self.server,
            'triples': '\n'.join([str(x).strip() for x in self.tree.service.triples])
        }
        return {'name': name, 'endpoint': self.server}, None

    def instantiate(self, d):
        new_tree = self.tree.instantiate(d)
        return IndependentOperator(self.query, new_tree, self.contact, self.config)

    def instantiateFilter(self, vars_instantiated, filter_str):
        new_tree = self.tree.instantiateFilter(vars_instantiated, filter_str)
        return IndependentOperator(self.query, new_tree, self.contact, self.config)

    def getCardinality(self):
        if self.cardinality is None:
            self.cardinality = self.askCount(self.query, self.tree, set(), self.contact)
        return self.cardinality

    def askCount(self, query, tree, vars, contact):
        (server, query) = tree.getCount(query, vars, None)
        q = Queue()
        contact(server, query, q)

        res = q.get()
        # print res
        v = -1
        if res == "EOF":
            return 20000
        for k in res:
            v = res[k]
        q.get()
        return int(v)

    def getJoinCardinality(self, vars):
        c = None
        for (v, c2) in self.joinCardinality:
            if v == vars:
                c = c2
                break
        if c is None:
            if len(vars) == 0:
                c = self.getCardinality()
            else:
                c = self.askCount(self.query, self.tree, vars, self.contact)
            self.joinCardinality.append((vars, c))
        return c

    def allTriplesLowSelectivity(self):
        return self.tree.service.allTriplesLowSelectivity()

    def places(self):
        return self.tree.places()

    def constantNumber(self):

        return self.tree.constantNumber()

    def constantPercentage(self):
        return self.constantNumber()/self.places()

    def aux(self, n):
        return self.tree.aux(n)

    def execute(self, outputqueue, processqueue=Queue()):

        if self.tree.service.limit == -1:
            self.tree.service.limit = 10000  # TODO: Fixed value, this can be learnt in the future

        # Evaluate the independent operator.

        # self.q = Queue()

        p = Process(target=self.contact, args=(self.server, self.query_str, outputqueue, self.config, self.tree.service.limit))
        p.start()
        # processqueue.put(p.pid)

        # i = 0
        # while True:
        #     # Get the next item in queue.
        #     res = self.q.get(True)
        #     # Put the result into the output queue.
        #     #print res
        #     i += 1
        #     outputqueue.put(res)
        #     # Check if there's no more data.
        #     if res == "EOF":
        #         break

        # p.terminate()


def contactSource(molecule, query, queue, config, limit=-1):
    # Contacts the datasource (i.e. real endpoint).
    # Every tuple in the answer is represented as Python dictionaries
    # and is stored in a queue.
    # print "in *NEW* contactSource"
    b = None
    cardinality = 0
    # moleculeMetadata = config.findMolecule(molecule)
    # wrappers = [w for w in moleculeMetadata['wrappers']]
    # if len(wrappers) == 0:
    #     queue.put("EOF")
    # server = wrappers[0]['url']
    server = molecule

    referer = server
    server = server.split("http://")[1]
    if '/' in server:
        (server, path) = server.split("/", 1)
    else:
        path = ""
    host_port = server.split(":")
    port = 80 if len(host_port) == 1 else host_port[1]
    card = 0
    if limit == -1:
        b, card = contactSourceAux(referer, server, path, port, query, queue)
    else:
        # Contacts the datasource (i.e. real endpoint) incrementally,
        # retreiving partial result sets combining the SPARQL sequence
        # modifiers LIMIT and OFFSET.

        # Set up the offset.
        offset = 0

        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            b, cardinality = contactSourceAux(referer, server, path, port, query_copy, queue)
            card += cardinality
            if cardinality < limit:
                break

            offset = offset + limit

    # Close the queue
    queue.put("EOF")
    return b


def contactSourceAux(referer, server, path, port, query, queue):
    # Setting variables to return.
    b = None
    reslist = 0

    if '0.0.0.0' in server:
        server = server.replace('0.0.0.0', 'localhost')

    js = "application/sparql-results+json"
    params = {'query': query, 'format': js}
    headers = {"User-Agent":
                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
               "Accept": js}
    try:
        data = urllib.parse.urlencode(params)
        data = data.encode('utf-8')
        req = urllib.request.Request(referer, data, headers)
        with urllib.request.urlopen(req) as response:
            resp = response.read()
            resp = resp.decode()
            res = resp.replace("false", "False")
            res = res.replace("true", "True")
            res = eval(res)
            reslist = 0
            if type(res) == dict:
                b = res.get('boolean', None)

                if 'results' in res:
                    # print "raw results from endpoint", res
                    for x in res['results']['bindings']:
                        for key, props in x.items():
                            # Handle typed-literals and language tags
                            suffix = ''
                            if props['type'] == 'typed-literal':
                                if isinstance(props['datatype'], bytes):
                                    suffix = "^^<" + props['datatype'].decode('utf-8') + ">"
                                else:
                                    suffix = "^^<" + props['datatype'] + ">"
                            elif "xml:lang" in props:
                                suffix = '@' + props['xml:lang']
                            try:
                                if isinstance(props['value'], bytes):
                                    x[key] = props['value'].decode('utf-8') + suffix
                                else:
                                    x[key] = props['value'] + suffix
                            except:
                                x[key] = props['value'] + suffix

                        queue.put(x)
                        reslist += 1
                    # Every tuple is added to the queue.
                    # for elem in reslist:
                        # print elem
                        # queue.put(elem)

            else:
                print("the source " + str(server) + " answered in " + res.getheader("content-type") + " format, instead of"
                       + " the JSON format required, then that answer will be ignored")
    except Exception as e:
        print("Exception while sending request to ", referer, "msg:", e)

    # print "b - ", b
    # print server, query, len(reslist)

    # print "Contact Source returned: ", len(reslist), ' results'
    return b, reslist
