from DeTrusty.Sparql.Parser.services import Aggregate, Expression

def getVars(sg):
    s = []
    if not sg.subject.constant:
        s.append(sg.subject.name)
    if not sg.theobject.constant:
        s.append(sg.theobject.name)
    return s

def getPrefs(ps):
    prefDict = dict()
    for p in ps:
         pos = p.find(":")
         c = p[0:pos].strip()
         v = p[(pos+1):len(p)].strip()
         prefDict[c] = v
    return prefDict


def getUri(p, prefs):
    if "'" in p.name or '"' in p.name:
        return p.name
    hasPrefix = prefix(p)
    if hasPrefix:
        (pr, su) = hasPrefix
        n = prefs[pr]
        n = n[:-1] + su + ">"
        return n
    return p.name


def prefix(p):
    s = p.name
    pos = s.find(":")
    if (not (s[0] == "<")) and pos > -1:
        return (s[0:pos].strip(), s[(pos+1):].strip())

    return None


def getTemplatesPerMolecule(molecules):
    moltemp = dict()
    for m in molecules:
        for t in molecules[m].templates:
            if m in moltemp:
                moltemp[m].append(t.pred)
            else:
                moltemp[m] = [t.pred]
    return moltemp

###################################################################


def collect_vars(proj):
    agg_exist = False
    implicit_grouping = []

    for var in proj:
        if isinstance(var, Aggregate):
            agg_exist = True
        elif isinstance(var, Expression):
            if not agg_exist:
                agg_exist = var.aggInside()
        else:
            implicit_grouping.append(var)

    if not agg_exist:
        implicit_grouping = []  # no grouping needed

    return (False if implicit_grouping else agg_exist), implicit_grouping


def valid_proj_vars(proj, group_by):
    for var in proj:
        if isinstance(var, Aggregate):
            continue
        if isinstance(var, Expression) and var.aggInside():
            continue
        if var not in group_by:
            return False
    return True
