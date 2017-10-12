"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from expecter import expect

from taskjuggler_python import jsonjuggler, juggler
import json, datetime, pytz
juggler.DEBUG = True

def describe_DictJuggler():

    def when_dict():
        expect((jsonjuggler.DictJuggler({})).issues) == {}

json_test_tasks = json.dumps([{"id": 2, "depends": [1], "allocate": "me", "effort": 1.2},{"id": 1, "effort": 3, "allocate": "me", "summary": "test"}])

def describe_JsonJuggler():
    def when_json():
        jj = jsonjuggler.JsonJuggler(json_test_tasks)
        jj.juggle()
        jj.walk(juggler.JugglerProject)[0].set_interval(datetime.datetime(2017, 10, 10), datetime.datetime(2035,10,10))
        expect(str(jj.write_file())) == juggler.JugglerSource.COMMENTS_HEADER + '''
 
project default "Default Project" 2017-10-10-00:00:00 - 2035-10-10-00:00:00  {

timezone "UTC"
outputdir "REPORT"
}
resource me "Default Resource"
icalreport "calendar"
task tjp_numid_2 "Task is not initialized" {
    depends !tjp_numid_1
    effort 2h
    allocate me

}
task tjp_numid_1 "test" {
    effort 3h
    allocate me

}'''
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
        jg.walk(juggler.JugglerProject)[0].set_interval(datetime.datetime(2017, 10, 10))
        # jg.juggle()
        jg.run()
        # d = dict(jg)
        # js = jg.toJSON()
        tasks = jg.walk(juggler.JugglerTask)
        expect(len(tasks)) == 2
        
        expect(tasks[0].walk(juggler.JugglerBooking)[0].start) == datetime.datetime(2017, 10, 10, 12, 0, tzinfo=pytz.utc)
        
        expect(jg.toJSON()) == """[
    {
        "allocate": "me",
        "booking": "2017-10-10T12:00:00+00:00",
        "depends": [
            1
        ],
        "effort": 1.2,
        "id": 2
    },
    {
        "allocate": "me",
        "booking": "2017-10-10T09:00:00+00:00",
        "effort": 3,
        "id": 1,
        "summary": "test"
    }
]"""