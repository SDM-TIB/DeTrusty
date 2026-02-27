import pytest
from DeTrusty.Sparql.parser import parse
from DeTrusty.Sparql.utils import (
    Query, Triple, Argument, UnionBlock, JoinBlock, Optional,
    Filter, Values, Bind, Service
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _triples(query: Query) -> list[Triple]:
    """Recursively collect all Triple objects from a parsed query body."""
    def _collect(node) -> list[Triple]:
        if isinstance(node, Triple):
            return [node]
        if isinstance(node, (UnionBlock, JoinBlock)):
            result = []
            for child in node.triples:
                result.extend(_collect(child))
            return result
        if isinstance(node, Optional):
            return _collect(node.bgg)
        if isinstance(node, Filter):
            return []
        if isinstance(node, (Bind, Values, Service)):
            return []
        return []

    return _collect(query.body)


def _arg_name(arg: Argument) -> str:
    """Return the string value of an Argument, stripping surrounding quotes."""
    return arg.name.strip('"\'')


def _triple_object(t: Triple) -> Argument:
    """Return the object Argument of a Triple (stored as 'theobject')."""
    return t.theobject


def _triple_tuple(t: Triple) -> tuple[str, str, str]:
    return (_arg_name(t.subject), _arg_name(t.predicate), _arg_name(_triple_object(t)))


# ---------------------------------------------------------------------------
# Basic SELECT queries
# ---------------------------------------------------------------------------

class TestBasicSelect:

    def test_simple_triple(self):
        q = parse("SELECT ?s ?p ?o WHERE { ?s ?p ?o }")
        assert isinstance(q, Query)
        assert not q.distinct
        triples = _triples(q)
        assert len(triples) == 1
        assert _triple_tuple(triples[0]) == ("?s", "?p", "?o")

    def test_select_distinct(self):
        q = parse("SELECT DISTINCT ?s WHERE { ?s ?p ?o }")
        assert q.distinct is True

    def test_select_star(self):
        q = parse("SELECT * WHERE { ?s ?p ?o }")
        assert isinstance(q, Query)
        # args is empty list when SELECT *
        assert q.args == []

    def test_projected_variables(self):
        q = parse("SELECT ?s ?p WHERE { ?s ?p ?o }")
        names = [a.name for a in q.args]
        assert "?s" in names
        assert "?p" in names
        assert "?o" not in names

    def test_uri_subject(self):
        q = parse("SELECT ?p ?o WHERE { <http://example.org/subject> ?p ?o }")
        triples = _triples(q)
        assert len(triples) == 1
        assert "<http://example.org/subject>" in triples[0].subject.name

    def test_uri_predicate(self):
        q = parse("SELECT ?s WHERE { ?s <http://example.org/p> ?o }")
        triples = _triples(q)
        assert "<http://example.org/p>" in triples[0].predicate.name

    def test_uri_object(self):
        q = parse("SELECT ?s WHERE { ?s ?p <http://example.org/obj> }")
        triples = _triples(q)
        assert "<http://example.org/obj>" in _triple_object(triples[0]).name

    def test_literal_object(self):
        q = parse('SELECT ?s WHERE { ?s ?p "hello" }')
        triples = _triples(q)
        assert len(triples) == 1
        assert "hello" in _triple_object(triples[0]).name

    def test_rdf_type_shorthand_a(self):
        """Predicate 'a' must expand to rdf:type."""
        q = parse("SELECT ?s WHERE { ?s a <http://example.org/Class> }")
        triples = _triples(q)
        assert len(triples) == 1
        assert "rdf-syntax-ns#type" in triples[0].predicate.name

    def test_multiple_triples(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o . ?s ?p2 ?o2 }")
        triples = _triples(q)
        assert len(triples) == 2


# ---------------------------------------------------------------------------
# PREFIX handling
# ---------------------------------------------------------------------------

class TestPrefixes:

    def test_prefix_declared(self):
        q = parse("PREFIX ex: <http://example.org/> SELECT ?s WHERE { ?s ex:p ?o }")
        assert isinstance(q, Query)
        assert len(q.prefs) == 1

    def test_multiple_prefixes(self):
        q = parse(
            "PREFIX ex: <http://example.org/> "
            "PREFIX foaf: <http://xmlns.com/foaf/0.1/> "
            "SELECT ?s WHERE { ?s foaf:name ?n }"
        )
        assert len(q.prefs) == 2


# ---------------------------------------------------------------------------
# Semicolon shorthand  ( ?s :p1 :o1 ; :p2 :o2 )
# ---------------------------------------------------------------------------

class TestSemicolonShorthand:

    def test_two_predicates_same_subject(self):
        q = parse(
            "SELECT DISTINCT ?c WHERE { ?s a ?c ; <http://example.org/p> ?d }"
        )
        triples = _triples(q)
        assert len(triples) == 2
        subjects = {_arg_name(t.subject) for t in triples}
        assert subjects == {"?s"}, "Both triples must share the same subject"

    def test_first_predicate_is_rdf_type(self):
        q = parse(
            "SELECT DISTINCT ?c WHERE { ?s a ?c ; <http://example.org/p> ?d }"
        )
        triples = _triples(q)
        type_triple = next(t for t in triples if "rdf-syntax-ns#type" in t.predicate.name)
        assert _arg_name(_triple_object(type_triple)) == "?c"

    def test_second_predicate_correct(self):
        q = parse(
            "SELECT DISTINCT ?c WHERE { ?s a ?c ; <http://example.org/p> ?d }"
        )
        triples = _triples(q)
        p_triple = next(t for t in triples if "rdf-syntax-ns#type" not in t.predicate.name)
        assert "<http://example.org/p>" in p_triple.predicate.name
        assert _arg_name(_triple_object(p_triple)) == "?d"

    def test_three_predicates_via_semicolons(self):
        q = parse(
            "SELECT ?s WHERE { "
            "  ?s <http://example.org/p1> ?a ; "
            "     <http://example.org/p2> ?b ; "
            "     <http://example.org/p3> ?c "
            "}"
        )
        triples = _triples(q)
        assert len(triples) == 3
        subjects = {_arg_name(t.subject) for t in triples}
        assert subjects == {"?s"}

    def test_trailing_semicolon(self):
        """A trailing ';' before the closing '}' is valid SPARQL."""
        q = parse(
            "SELECT ?s WHERE { ?s <http://example.org/p1> ?a ; <http://example.org/p2> ?b ; }"
        )
        triples = _triples(q)
        assert len(triples) == 2

    def test_semicolon_with_explicit_period(self):
        """Semicolon block followed by a '.' and another triple."""
        q = parse(
            "SELECT ?s WHERE { "
            "  ?s <http://example.org/p1> ?a ; <http://example.org/p2> ?b . "
            "  ?x <http://example.org/p3> ?y "
            "}"
        )
        triples = _triples(q)
        assert len(triples) == 3


# ---------------------------------------------------------------------------
# Comma shorthand  ( ?s :p :o1 , :o2 )
# ---------------------------------------------------------------------------

class TestCommaShorthand:

    def test_two_objects_same_predicate(self):
        q = parse(
            "SELECT DISTINCT ?c WHERE { ?s a ?c , ?d }"
        )
        triples = _triples(q)
        assert len(triples) == 2
        subjects = {_arg_name(t.subject) for t in triples}
        predicates = {t.predicate.name for t in triples}
        assert len(subjects) == 1, "Both triples must share the same subject"
        assert len(predicates) == 1, "Both triples must share the same predicate"

    def test_comma_objects_correct_values(self):
        q = parse(
            "SELECT DISTINCT ?c WHERE { ?s a ?c , ?d }"
        )
        triples = _triples(q)
        objects = {_arg_name(_triple_object(t)) for t in triples}
        assert objects == {"?c", "?d"}

    def test_three_objects_via_commas(self):
        q = parse(
            "SELECT ?s WHERE { ?s <http://example.org/p> ?a , ?b , ?c }"
        )
        triples = _triples(q)
        assert len(triples) == 3

    def test_comma_with_uri_objects(self):
        q = parse(
            "SELECT ?s WHERE { "
            "  ?s <http://example.org/type> <http://example.org/A> , <http://example.org/B> "
            "}"
        )
        triples = _triples(q)
        assert len(triples) == 2
        objects = {_triple_object(t).name for t in triples}
        assert "<http://example.org/A>" in objects
        assert "<http://example.org/B>" in objects


# ---------------------------------------------------------------------------
# Combined ; and , shorthands
# ---------------------------------------------------------------------------

class TestCombinedShorthands:

    def test_semicolon_and_comma_combined(self):
        """?s :p1 :a , :b ; :p2 :c  →  3 triples, all same subject."""
        q = parse(
            "SELECT ?s WHERE { "
            "  ?s <http://example.org/p1> <http://example.org/a> , <http://example.org/b> ; "
            "     <http://example.org/p2> <http://example.org/c> "
            "}"
        )
        triples = _triples(q)
        assert len(triples) == 3
        subjects = {_arg_name(t.subject) for t in triples}
        assert subjects == {"?s"}

    def test_predicate_groups_correct(self):
        q = parse(
            "SELECT ?s WHERE { "
            "  ?s <http://example.org/p1> ?a , ?b ; "
            "     <http://example.org/p2> ?c "
            "}"
        )
        triples = _triples(q)
        p1_triples = [t for t in triples if "p1" in t.predicate.name]
        p2_triples = [t for t in triples if "p2" in t.predicate.name]
        assert len(p1_triples) == 2
        assert len(p2_triples) == 1


# ---------------------------------------------------------------------------
# OPTIONAL
# ---------------------------------------------------------------------------

class TestOptional:

    def test_optional_block(self):
        q = parse(
            "SELECT ?s ?name WHERE { "
            "  ?s <http://example.org/p> ?o . "
            "  OPTIONAL { ?s <http://xmlns.com/foaf/0.1/name> ?name } "
            "}"
        )
        assert isinstance(q, Query)
        # The body should contain at least one Optional node
        def has_optional(node) -> bool:
            if isinstance(node, Optional):
                return True
            if isinstance(node, (UnionBlock, JoinBlock)):
                return any(has_optional(c) for c in node.triples)
            return False
        assert has_optional(q.body)

    def test_optional_with_semicolon_inside(self):
        q = parse(
            "SELECT ?s WHERE { "
            "  ?s a <http://example.org/C> . "
            "  OPTIONAL { ?s <http://example.org/p1> ?a ; <http://example.org/p2> ?b } "
            "}"
        )
        assert isinstance(q, Query)


# ---------------------------------------------------------------------------
# FILTER
# ---------------------------------------------------------------------------

class TestFilter:

    def test_filter_equals(self):
        q = parse('SELECT ?s WHERE { ?s ?p ?o . FILTER (?o = "value") }')
        assert isinstance(q, Query)

    def test_filter_lang(self):
        q = parse('SELECT ?s WHERE { ?s ?p ?o . FILTER (LANG(?o) = "en") }')
        assert isinstance(q, Query)

    def test_filter_regex(self):
        q = parse('SELECT ?s WHERE { ?s ?p ?o . FILTER REGEX(?o, "pattern") }')
        assert isinstance(q, Query)

    def test_filter_with_semicolon_triples(self):
        q = parse(
            'SELECT ?s WHERE { ?s <http://example.org/p1> ?a ; <http://example.org/p2> ?b . '
            'FILTER (?a != ?b) }'
        )
        triples = _triples(q)
        assert len(triples) == 2


# ---------------------------------------------------------------------------
# UNION
# ---------------------------------------------------------------------------

class TestUnion:

    def test_simple_union(self):
        q = parse(
            "SELECT ?s WHERE { "
            "  { ?s <http://example.org/p1> ?o } "
            "  UNION "
            "  { ?s <http://example.org/p2> ?o } "
            "}"
        )
        assert isinstance(q, Query)
        assert isinstance(q.body, UnionBlock)

    def test_union_block_has_two_branches(self):
        q = parse(
            "SELECT ?s WHERE { "
            "  { ?s <http://example.org/p1> ?o } "
            "  UNION "
            "  { ?s <http://example.org/p2> ?o } "
            "}"
        )
        assert len(q.body.triples) == 2


# ---------------------------------------------------------------------------
# ORDER BY / LIMIT / OFFSET
# ---------------------------------------------------------------------------

class TestModifiers:

    def test_limit(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o } LIMIT 10")
        assert q.limit == "10"

    def test_offset(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o } OFFSET 5")
        assert q.offset == "5"

    def test_limit_and_offset(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o } LIMIT 10 OFFSET 20")
        assert q.limit == "10"
        assert q.offset == "20"

    def test_order_by_asc(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o } ORDER BY ASC(?s)")
        assert len(q.order_by) == 1
        assert q.order_by[0].desc is False

    def test_order_by_desc(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o } ORDER BY DESC(?s)")
        assert len(q.order_by) == 1
        assert q.order_by[0].desc is True


# ---------------------------------------------------------------------------
# GROUP BY / HAVING
# ---------------------------------------------------------------------------

class TestGroupBy:

    def test_group_by(self):
        q = parse("SELECT ?s WHERE { ?s ?p ?o } GROUP BY ?s")
        assert len(q.group_by) == 1
        assert q.group_by[0].name == "?s"

    def test_having(self):
        q = parse(
            "SELECT ?s (COUNT(?o) AS ?cnt) WHERE { ?s ?p ?o } "
            "GROUP BY ?s HAVING (?cnt > 5)"
        )
        assert q.having is not None


# ---------------------------------------------------------------------------
# BIND / VALUES
# ---------------------------------------------------------------------------

class TestBindAndValues:

    def test_bind(self):
        q = parse(
            'SELECT ?s ?label WHERE { ?s ?p ?o . BIND(STR(?o) AS ?label) }'
        )
        assert isinstance(q, Query)

    def test_values_single_var(self):
        q = parse(
            'SELECT ?s WHERE { ?s ?p ?o . VALUES ?o { <http://example.org/a> <http://example.org/b> } }'
        )
        assert isinstance(q, Query)

    def test_values_multiple_vars(self):
        q = parse(
            'SELECT ?s WHERE { ?s ?p ?o . VALUES (?s ?p) { (<http://ex.org/s> <http://ex.org/p>) } }'
        )
        assert isinstance(q, Query)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestParseErrors:

    def test_invalid_query_raises(self):
        with pytest.raises((TypeError, SyntaxError, Exception)):
            parse("THIS IS NOT SPARQL")

    def test_missing_where_raises(self):
        with pytest.raises((TypeError, SyntaxError, Exception)):
            parse("SELECT ?s { ?s ?p ?o }")

    def test_unclosed_brace_raises(self):
        with pytest.raises((TypeError, SyntaxError, Exception)):
            parse("SELECT ?s WHERE { ?s ?p ?o")

    def test_empty_string_returns_none(self):
        result = parse("")
        assert result is None


# ---------------------------------------------------------------------------
# Real-world style queries
# ---------------------------------------------------------------------------

class TestRealWorldQueries:

    def test_foaf_person_query(self):
        q = parse(
            "PREFIX foaf: <http://xmlns.com/foaf/0.1/> "
            "SELECT ?name ?email WHERE { "
            "  ?person a foaf:Person ; "
            "           foaf:name ?name ; "
            "           foaf:mbox ?email . "
            "}"
        )
        triples = _triples(q)
        assert len(triples) == 3
        subjects = {_arg_name(t.subject) for t in triples}
        assert subjects == {"?person"}

    def test_dbpedia_style_query(self):
        q = parse(
            "PREFIX dbo: <http://dbpedia.org/ontology/> "
            "PREFIX dbp: <http://dbpedia.org/property/> "
            "SELECT DISTINCT ?city ?pop WHERE { "
            "  ?city a dbo:City ; "
            "        dbp:populationTotal ?pop . "
            "  FILTER (?pop > 1000000) "
            "} ORDER BY DESC(?pop) LIMIT 10"
        )
        triples = _triples(q)
        assert len(triples) == 2
        assert q.distinct is True
        assert q.limit == "10"

    def test_complex_optional_and_filter(self):
        q = parse(
            "PREFIX ex: <http://example.org/> "
            "SELECT ?s ?name ?age WHERE { "
            "  ?s a ex:Person . "
            "  OPTIONAL { ?s ex:name ?name } "
            "  OPTIONAL { ?s ex:age ?age . FILTER (?age > 18) } "
            "}"
        )
        assert isinstance(q, Query)

    def test_semicolon_and_separate_triple(self):
        """Semicolon shorthand followed by a separate triple with '.'. """
        q = parse(
            "SELECT ?s ?o1 ?o2 ?x WHERE { "
            "  ?s <http://example.org/p1> ?o1 ; "
            "     <http://example.org/p2> ?o2 . "
            "  ?x <http://example.org/p3> ?s "
            "}"
        )
        triples = _triples(q)
        assert len(triples) == 3
