"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from expecter import expect

from taskjuggler_python import jsonjuggler, juggler
import json

def describe_DictJuggler():

    def when_dict():
        expect((jsonjuggler.DictJuggler({})).issues) == {}

def describe_JsonJuggler():
    def when_json():
        js = json.dumps([{"id": 2, "depends": [1], "allocate": "me", "effort": 1.2},{"id": 1, "effort": 3, "allocate": "me", "summary": "test"}])
        jj = jsonjuggler.JsonJuggler(js)
        expect(str(jj.write_file())) == juggler.JugglerSource.COMMENTS_HEADER + '''
 
project default {

timezone "Europe/Dublin"
outputdir "REPORT"
}
task id2 "Task is not initialized" {
    depends !id1
    effort 1h
    allocate me

}
task id1 "test" {
    effort 3h
    allocate me

}
icalreport "calendar"'''

