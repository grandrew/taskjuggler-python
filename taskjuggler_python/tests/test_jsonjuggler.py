"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from expecter import expect

from taskjuggler_python import jsonjuggler, juggler
import json, datetime, pytz

def describe_DictJuggler():

    def when_dict():
        expect((jsonjuggler.DictJuggler({})).issues) == {}

json_test_tasks = json.dumps([{"id": 2, "depends": [1], "allocate": "me", "effort": 1.2},{"id": 1, "effort": 3, "allocate": "me", "summary": "test"}])

def describe_JsonJuggler():
    def when_json():
        jj = jsonjuggler.JsonJuggler(json_test_tasks)
        jj.juggle()
        expect(str(jj.write_file())) == juggler.JugglerSource.COMMENTS_HEADER + '''
 
project default "Default Project" 2017-10-10 - 2035-10-10  {

timezone "Europe/Dublin"
outputdir "REPORT"
}
resource me "Default Resource"
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
    def test_walk1():
        jg = jsonjuggler.JsonJuggler(json_test_tasks)
        jg.juggle()
        tasks = jg.walk(juggler.JugglerTask)
        expect(len(tasks)) == 2
        
    def test_walk2():
        jg = jsonjuggler.JsonJuggler(json_test_tasks)
        jg.juggle()
        rep = jg.walk(juggler.JugglerIcalreport)
        expect(len(rep)) == 1
        
        
    def when_full_workflow():
        jg = jsonjuggler.JsonJuggler(json_test_tasks)
        # jg.juggle()
        jg.run()
        # d = dict(jg)
        # js = jg.toJSON()
        tasks = jg.walk(juggler.JugglerTask)
        expect(len(tasks)) == 2
        
        expect(tasks[0].walk(juggler.JugglerBooking)[0].start) == datetime.datetime(2017, 10, 10, 11, 0, tzinfo=pytz.utc)