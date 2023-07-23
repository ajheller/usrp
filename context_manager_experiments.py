# Context manager experiments
#   Aaron Heller 22-Jul-2023

import contextlib

# Resources:
#   https://docs.python.org/3/library/contextlib.html
#   https://stackoverflow.com/questions/60367476/context-manager-that-handles-exceptions
#   https://realpython.com/python-with-statement/#coding-class-based-context-managers

# two ways...

# proxy for a system resourse like process priority

thing = 0


def set_thing(i):
    global thing
    thing = i


def get_thing():
    return thing


# this does it with a generator
@contextlib.contextmanager
def test1(new_value=0):
    print("entered ctx manager")
    try:
        saved_thing = get_thing()
        set_thing(new_value)
        print(thing, saved_thing)
        yield  # this makes test1 a generator, if "yield foo", the "as" varaible is bound to foo
    except Exception as e:
        print("Caught ", e)
        raise
    else:
        # do this if no exceptions
        print("no exceptions!")
    finally:
        # always do this
        print("cleanup")
        set_thing(saved_thing)


try:
    print("before cts:", get_thing())
    with test1(99):
        print("in cts:", get_thing())
        q = 1 / 1
    print("after ctx:", get_thing())

finally:
    print("finally:", get_thing())


# this does it with a custom context manager class


class test2(contextlib.AbstractContextManager):
    def __init__(self, new_value):
        self.new_value = new_value

    def __enter__(self):
        self.saved_thing = get_thing()
        set_thing(self.new_value)

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("cleanup", exc_type, exc_val, exc_tb)
        set_thing(self.saved_thing)


try:
    print("before cts:", get_thing())
    with test2(99):
        print("in cts:", get_thing())
        q = 1 / 0
    print("after ctx:", get_thing())

finally:
    print("finally:", get_thing())
