"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

import datetime

from expecter import expect

from taskjuggler_python import juggler
juggler.DEBUG = True

def describe_to_identifier():
    def test_it():
        expect(juggler.to_identifier("ab-c")) == "ab"+juggler.TJP_DASH_PREFIX+"c"

def describe_JugglerSimpleProperty():
    def default_create():
        expect(str(juggler.JugglerSimpleProperty())) == '\nunknown_property '

def describe_JugglerCompoundKeyword():
    def default_create():
        expect(str(juggler.JugglerCompoundKeyword())) == "\nunknown_keyword "

def describe_JugglerProject():
    def default_create():
        p = juggler.JugglerProject()
        p.set_interval(datetime.datetime(2017, 10, 10), datetime.datetime(2035,10,10))
        expect(str(p)) == '\nproject default "Default Project" 2017-10-10-00:00:00 - 2035-10-10-00:00:00  {\n\ntimezone "UTC"\noutputdir "REPORT"\n}'
        
def describe_JugglerSource():
    def default_create():
        s = juggler.JugglerSource()
        s.walk(juggler.JugglerProject)[0].set_interval(datetime.datetime(2017, 10, 10), datetime.datetime(2035,10,10))
        expect(str(s)) == juggler.JugglerSource.COMMENTS_HEADER + '\n \nproject default "Default Project" 2017-10-10-00:00:00 - 2035-10-10-00:00:00  {\n\ntimezone "UTC"\noutputdir "REPORT"\n}\nresource me "Default Resource"\nicalreport "calendar"'
    def tasks_create():
        s = juggler.JugglerSource()
        s.walk(juggler.JugglerProject)[0].set_interval(datetime.datetime(2017, 10, 10), datetime.datetime(2035,10,10))
        t = juggler.JugglerTask()
        s.set_property(t)
        expect(str(s)) == juggler.JugglerSource.COMMENTS_HEADER + '\n \nproject default "Default Project" 2017-10-10-00:00:00 - 2035-10-10-00:00:00  {\n\ntimezone "UTC"\noutputdir "REPORT"\n}\nresource me "Default Resource"\nicalreport "calendar"\ntask unknown_task "Task is not initialized" {\n    allocate me\n    effort 1h\n\n}'

def describe_JugglerTaskPriority():
    p = juggler.JugglerTaskPriority()
    p.set_value(100)
    expect(str(p)) == "    priority 100\n"

def describe_GenericJuggler():
    jg = juggler.GenericJuggler()
    t = juggler.JugglerTask()
    t.set_property(juggler.JugglerTaskEffort(1))
    jg.add_task(t)
    jg.run()
    expect(len(jg.walk(juggler.JugglerBooking))) == 1
    
def describe_JugglerTaskStart():
    p = juggler.JugglerTaskStart()
    d = datetime.datetime.now()
    p.set_value(d)
    expect(str(p)) == "    start "+juggler.to_tj3time(d)+"\n"