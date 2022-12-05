from easypub.utils import cached_property


class Example:
    def __init__(self, calls=0):
        self.calls = calls

    @cached_property
    def expensive(self):
        self.calls += 1
        return self.calls


def test_multiple_calls_cached():
    a = Example()

    assert a.expensive == 1
    assert a.expensive == 1


def test_multiple_instances():
    a = Example(0)
    b = Example(1)

    assert a.expensive == 1
    assert a.expensive == 1

    assert b.expensive == 2
    assert b.expensive == 2


def test_delete():
    a = Example()

    a.expensive

    del a.__dict__["expensive"]

    assert a.expensive == 2
