# json parser implementation
from juggler import *
import json

class DictJuggler(GenericJuggler):
    """ a simple dictionary based format parser """
    def __init__(self, issues):
        self.issues = issues
    def load_issues(self):
        return self.issues

class JsonJuggler(DictJuggler):
    def __init__(self, json_issues):
        self.issues = json.loads(json_issues)
        