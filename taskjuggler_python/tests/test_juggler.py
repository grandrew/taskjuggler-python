"""Sample unit test module using pytest-describe and expecter."""
# pylint: disable=redefined-outer-name,unused-variable,expression-not-assigned,singleton-comparison

from expecter import expect

from taskjuggler_python import juggler

def test_identifier():
    def test_it():
        expect(juggler.to_identifier("ab-c")) == "ab_c"
        
