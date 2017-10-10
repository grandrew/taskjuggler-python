"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from expecter import expect

from taskjuggler_python import juggler

def describe_to_identifier():
    def test_it():
        expect(juggler.to_identifier("ab-c")) == "ab_c"

def describe_JugglerSimpleProperty():
    def default_create():
        expect(str(juggler.JugglerSimpleProperty())) == '\nunknown_property '

def describe_JugglerCompoundKeyword():
    def default_create():
        expect(str(juggler.JugglerCompoundKeyword())) == "\nunknown_keyword "

def describe_JugglerProject():
    def default_create():
        expect(str(juggler.JugglerProject())) == '\nproject default "Default Project" 2017-10-10 - 2035-10-10  {\n\ntimezone "Europe/Dublin"\noutputdir "REPORT"\n}'
        
def describe_JugglerSource():
    def default_create():
        expect(str(juggler.JugglerSource())) == juggler.JugglerSource.COMMENTS_HEADER + '\n \nproject default "Default Project" 2017-10-10 - 2035-10-10  {\n\ntimezone "Europe/Dublin"\noutputdir "REPORT"\n}\nresource me "Default Resource"\nicalreport "calendar"'
    def tasks_create():
        s = juggler.JugglerSource()
        t = juggler.JugglerTask()
        s.set_property(t)
        expect(str(s)) == juggler.JugglerSource.COMMENTS_HEADER + '\n \nproject default "Default Project" 2017-10-10 - 2035-10-10  {\n\ntimezone "Europe/Dublin"\noutputdir "REPORT"\n}\nresource me "Default Resource"\ntask unknown_task "Task is not initialized"\nicalreport "calendar"'

