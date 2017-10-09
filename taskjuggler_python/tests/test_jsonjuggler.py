"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from expecter import expect

from taskjuggler_python import jsonjuggler


def describe_DictJuggler():

    def when_dict():
        expect((jsonjuggler.DictJuggler({})).issues) == {}

