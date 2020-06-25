# `pylint-ignore`

Reduce Pylint noise by ignoring messages, case by case.


## OK/FAIL Workflow

The goal here is to:

 - not have to globally ignore potentially useful messages that are safe sometimes, but not always.
 - not have to sprinkle your codebase with `# pylint disable` comments.
 - cause a CI failure if pylint shows any *new* messages that haven't been explicitly ignored.

The key word here is *new*, which of course implies some statefulness.



The usefulness of a linter is vastly increased when you only have two
states to consider: OK and FAIL. This vastly reduces cognitive load for
developers. It allows them to treat errors seriously, rather than ignoring
messages because they are hidden among all the noise that is too tiresome
to read again and again.

The problem of "noise" is acknowledged [early in the
documentation](http://pylint.pycqa.org/en/stable/tutorial.html) of pylint.
You can get to OK/FAIL bliss with pylint, if you spend time to configure
it, such as is suggested by
[pythonspeed.com](https://pythonspeed.com/articles/pylint/)

The unfortunate thing about this approach is that it reduces the
usefulness of pylint in cases where a message is valid only some of
the time. Take for example this code

```python
def makeExtension(**kwargs)
    ...
```

Pylint will complain with the following message:

```
__init__.py:20:0: C0103: Function name "makeExtension"
    doesn't conform to snake_case naming style (invalid-name)
```

Generally speaking this is a valid warning, but in this particular
case I am forced to use this function name as it is part of an API
convention. Presumably I could change the code to something like this:

```python
def _make_extension(**kwargs)
    ...

# name that conforms with the Markdown extension API
# https://python-markdown.github.io/extensions/api/#dot_notation
makeExtension = _make_extension
```

That is actually a bit better, now that I think about it, but even so, there's a question of cost benefit. If I encounter these kinds of messages that are not actual errors, it makes me want to not use pylint in a commit hook. Let's see another example, where I'm certainly not going to change the code for pylint.

```python
@pytest.fixture()
def myfixture():
    # setup
    yield value
    # teardown


def test_the_thing(myfixture):
    ...
```

Pylint will complain with the following message:

```
test/test_stuff.py:67:17: W0621: Redefining name 'myfixture'
    from outer scope (line 61) (redefined-outer-name)
```

A message that warns me about shadowed names? Sign me up! Unfortunately
for this case, that's very intentional behaviour. The `myfixture` argument
is a bit of dependency injection magic by the pytest library that I don't
want to change. I certainly don't want to turn this warning off globally,
so maybe I could clutter the code for this particular file with `# pylint:
disable=redefined-outer-name` comments. Frankly I don't want to, I find it
distasteful and distracting.

So what to do? In general I would like to have this warning enabled,
because I know that there are other (less intelligent) developers who
might make a mistake that this warning would help to catch. I could
try and remember to run pylint regularly with this warning enabled
again and review if any new cases appeard, but that hardly seems
scalable.

What I'd really like to do is to tell pylint: "Yes, I understand, I
know what I'm doing, for this specific case, please leave me alone".
Preferably in not so many words, and preferably without cluttering up
my code with `# pylint disable=` comments.

Furthermore, if I disable a message, I might also like to see a
justification, so that I can judge if it is still valid later on down the
line.


## Acknowlege and Silence

TODO


## Other Projects

The [`pylint-patcher`](https://pypi.org/project/pylint-patcher/) is an alternate approach to the same problem.

    Individual lint exceptions are stored in a patchfile (.pylint-disable.patch)
    The patchfile is applied to the source before Pylint is run
    The patchfile is removed from the source after Pylint completes

The `pylint-ignore` project does not modify your files, but instead it invokes pylint as a subprocess and does postprocessing on the output it generates, ignoring any messages, on a case-by-case basis, that you previously marked to be ignored and which are stored in the `pylint-ignore.cfg` file.


