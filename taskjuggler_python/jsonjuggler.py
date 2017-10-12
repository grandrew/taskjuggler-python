# json parser implementation
from juggler import *
import json, re, math
import dateutil.parser

class DictJugglerTaskDepends(JugglerTaskDepends):
    def load_from_issue(self, issue):
        """
        Args:
            issue["depends"] - a list of identifiers that this task depends on
        """
        if "depends" in issue: 
            # TODO HERE: remove ID normalization!
            if isinstance(issue["depends"], str) or isinstance(issue['depends'], unicode):
                self.set_value([int(x) for x in re.findall(r"[\w']+", issue["depends"])])
            # TODO check for list, else add idfr
            else: self.set_value([int(x) for x in issue["depends"]])

class DictJugglerTaskPriority(JugglerTaskPriority):
    def load_from_issue(self, issue):
        if "priority" in issue: self.set_value(int(issue["priority"]))
        
class DictJugglerTaskStart(JugglerTaskStart):
    def load_from_issue(self, issue):
        if "start" in issue: 
            if isinstance(issue["start"], str) or isinstance(issue['start'], unicode):
                self.set_value(dateutil.parser.parse(issue["start"]))
            else:
                self.set_value(issue["start"])
        
class DictJugglerTaskEffort(JugglerTaskEffort):
    UNIT = "h"
    def load_from_issue(self, issue):
        if "effort" in issue: self.set_value(math.ceil(issue["effort"]))

class DictJugglerTaskAllocate(JugglerTaskAllocate):
    def load_from_issue(self, issue):
        if "allocate" in issue: self.set_value(issue["allocate"])
        else: self.set_value("me") # stub!

class DictJugglerTask(JugglerTask):
    def load_default_properties(self, issue):
        self.set_property(DictJugglerTaskDepends(issue))
        self.set_property(DictJugglerTaskEffort(issue))
        self.set_property(DictJugglerTaskAllocate(issue))
        self.set_property(DictJugglerTaskStart(issue))
        self.set_property(DictJugglerTaskPriority(issue))
    def load_from_issue(self, issue):
        self.set_id(issue["id"])
        if "summary" in issue: self.summary = issue["summary"]

class DictJuggler(GenericJuggler):
    """ a simple dictionary based format parser """
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
        for t in self.walk(JugglerTask):
            for i in self.issues:
                if t.get_id() == i["id"]:
                    i["booking"] = t.walk(JugglerBooking)[0].decode()[0].isoformat()
        return json.dumps(self.issues, sort_keys=True, indent=4, separators=(',', ': '))

