from DeTrusty.Sparql.Parser.services import Aggregate, HavingHelper, Expression

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

def collectVars(proj, group, having, agg):
    implicit_group = not group 
    agg_exist = False
    over_all_triples = True
    index = 0

    for var in proj:
        if type(var) is Aggregate or type(var) is Expression:
            agg_exist = True
            break

    for var in proj:
        if type(var) is not Aggregate and type(var) is not Expression:
            over_all_triples = False
            if implicit_group and agg_exist:
                group.append(var)
        else:
            var.name = "?callret-" + str(index)
            agg.append(var)
        index += 1

    if having:
        tmp = havingVars(having.args)
        for arg in tmp:
            if arg not in agg:
                agg.append(arg)

    return over_all_triples

def havingVars(tmp):
    ret = list()
    for x in tmp:
        if type(x) is HavingHelper:
            ret.append(x.agg) 
        else:
            ret += havingVars(x.args)
    return ret
