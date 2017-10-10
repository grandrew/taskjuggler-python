# json parser implementation
from juggler import *
import json

class DictJugglerTaskDepends(JugglerTaskDepends):
    def load_from_issue(self, issue):
        """
        Args:
            issue["depends"] - a list of identifiers that this task depends on
        """
        if "depends" in issue: self.set_value([to_identifier(x) for x in issue["depends"]])

class DictJugglerTaskEffort(JugglerTaskEffort):
    UNIT = "h"
    def load_from_issue(self, issue):
        if "effort" in issue: self.set_value(int(issue["effort"]))

class DictJugglerTaskAllocate(JugglerTaskAllocate):
    def load_from_issue(self, issue):
        if "allocate" in issue: self.set_value(issue["allocate"])

class DictJugglerTask(JugglerTask):
    def load_default_properties(self, issue):
        self.set_property(DictJugglerTaskDepends(issue))
        self.set_property(DictJugglerTaskEffort(issue))
        self.set_property(DictJugglerTaskAllocate(issue))
    def load_from_issue(self, issue):
        self.set_id(to_identifier(issue["id"])) # TODO HERE: bi-directional ID decoder!
        if "summary" in issue: self.summary = issue["summary"]

class DictJuggler(GenericJuggler):
    """ a simple dictionary based format parser """
    # TODO HERE: configure and test allocations
    def __init__(self, issues):
        self.issues = issues
    def load_issues(self):
        return self.issues
    def create_task_instance(self, issue):
        return DictJugglerTask(issue)

class JsonJuggler(DictJuggler):
    def __init__(self, json_issues):
        self.issues = json.loads(json_issues)
    def toJSON(self):
        # TODO HERE: decode tasks back to JSON
        pass

