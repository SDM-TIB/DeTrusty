__author__ = "Philipp D. Rohde"


class Query:
    """Simple representation of a SPARQL query. Object to be changed in later versions."""

    def __init__(self, query_string):
        self.query_string = query_string
        self.distinct = True if "distinct" in query_string.lower() else False

        variables = query_string.lower().split("where", 1)[0]
        variables = variables.lower().replace("select", "").replace("distinct", "")
        variables = ''.join(variables.split())
        variables = variables.split("?")
        self.variables = []
        for variable in variables:
            if variable:
                self.variables.append(variable.strip())

        prefixes = query_string.split("SELECT", 1)[0]
        if prefixes:
            prefixes = prefixes.split("\n")
            self.prefixes = [(prefix.strip()[7:prefix.strip().find(':')], prefix.strip()[prefix.strip().find(':')+1:]) for prefix in prefixes if prefix]
        else:
            self.prefixes = []

    def get_variables(self):
        return self.variables

    def get_query_string(self):
        return self.query_string

    def get_distinct(self):
        return self.distinct

    def get_prefixes(self):
        return self.prefixes
