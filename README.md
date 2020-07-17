# [Pylint-Ignore][repo_ref]

Reduce Pylint noise. Triage messages. Ignore false positives.

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![PyCalVer 2020.1002][version_img]][version_ref]
[![PyPI Version][pypi_img]][pypi_ref]
[![PyPI Downloads][downloads_img]][downloads_ref]

Code Quality/CI:

[![Build Status][build_img]][build_ref]
[![Type Checked with mypy][mypy_img]][mypy_ref]
[![Code Coverage][codecov_img]][codecov_ref]
[![Code Style: sjfmt][style_img]][style_ref]


|                 Name                |        role       |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2020-06 | -     |


<!--
  To update the TOC:
  $ pip install md-toc
  $ md_toc --in-place README.md gitlab
-->


[](TOC)

[](TOC)


## Dealing with Messages, Case by Case

There is a reason flake8 is used so much more often than pylint. The ergonomics of pylint are not ideal. The problem of "noise" is acknowledged [early in the documentation](http://pylint.pycqa.org/en/stable/tutorial.html) of pylint. In fact, the frustration of using pylint is so obvious that it is even the topic of the projects tagline: "It's not just a linter that annoys you!".

If you want to use pylint on an existing codebase and add it to your CI setup, you have a few options:

 - Enable it and spend hours or days learning about which messages you should leave enabled and which are useful enough to leave enabled.
 - Spend hours or days fixing your code so that meaningful messages are no longer raised.
 - Disable almost everything so that it becomes practically useless and then opt-in to individual messages some time later™. This is the approach recomended at [pythonspeed.com](https://pythonspeed.com/articles/pylint/).

This is a bit facetious, but not by much. In any case you will either have to invest time or you risk ignoring meaningful messages. Wouldn't it be nice if you could at least start to use pylint, so that issues can be cought in any new code you write or update, without having to first clean up this mess that you've inherited?

Well look no further. With `pylint-ignore`, you can create a file that will keep track of all messages you either haven't dealt with yet, or which you want to permantly supress, because they are a false positive. You can check this into your repository and start using pylint in your CI setup, with minimal configuration.

From this point forward, if you deal with new messages as they crop up, you at least won't be making your situation worse. Secondly, you can deal with messages on a case by case basis and learn about best practices at your own pace.


## False Positives

A further issue with existing ways of using pylint is with false positives, messages that are useful in some cases, and sometimes not. How do you elimitate the noise of false positives without also silencing the true positives, such as this message.

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
distasteful and distracting clutter that doesn't belong in my code.

So what to do? In general I would like to have this warning enabled,
because I know that there are other (perhaps less intelligent) developers
who might make a mistake that this warning would help to catch. I could
try and remember to run pylint regularly with this warning enabled again
and review if any new cases appeard, but I would like to avoid any process that needs a human in the loop who has to pay careful attention.

What I'd really like to do is to tell pylint: "Yes, I understand, I
know what I'm doing, for this specific case, please leave me alone".
Preferably in not so many words, and preferably without cluttering up
my code with `# pylint disable=` comments.

Furthermore, if I disable a message selectively, it might need a short
text to justify the supression, because the next developer may not see why
this is a false positive and either introduce a bug while refactoring, or
waste time to figure out for themselves why it is a false positive. If
they disagree with the justification, they are free of course to proceed
with refactoring anyway.

There is a step by step approach you can and should take, even before you consider using pylint-ignore.

1. If you are running `pylint` for the first time, it is a good idea to run `pylint --errors-only`. The chance of false positives for this mode is very much reduced, and you should fix any error messages detected by pylint
2. If you are running `pylint` for the second time, try to get into the mindset of a pupil. Other developers have tried to determine what patterns in your code may be errors, may lead to errors, or may be expressed in a way that is more clear. You are free to take these messages under advisement, but consider how you would justify your own approach
1. run `pylint` and  every message it generates
2. if you are sure a message is always a false positive, add it to the list of globally disabled messages. You may for example want to disable bad-continuation


Another example: implementing an function that conforms to an api, but doesn't use all of its arguments will cause `W0613 (unused-argument)`


## Non-Silanceble messages

https://github.com/PyCQA/pylint/issues/214


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

You can get to OK/FAIL bliss with pylint, if you spend time to configure
it, such as is suggested by


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


## Acknowlege and Silence

TODO


## Other Projects

The [`pylint-patcher`](https://pypi.org/project/pylint-patcher/) is an alternate approach to the same problem.

    Individual lint exceptions are stored in a patchfile (.pylint-disable.patch)
    The patchfile is applied to the source before Pylint is run
    The patchfile is removed from the source after Pylint completes

The `pylint-ignore` project does not modify your files, but instead it invokes pylint as a subprocess and does postprocessing on the output it generates, ignoring any messages, on a case-by-case basis, that you previously marked to be ignored and which are stored in the `pylint-ignore.cfg` file.



[repo_ref]: https://gitlab.com/mbarkhau/pylint-ignore

[build_img]: https://gitlab.com/mbarkhau/pylint-ignore/badges/master/pipeline.svg
[build_ref]: https://gitlab.com/mbarkhau/pylint-ignore/pipelines

[codecov_img]: https://gitlab.com/mbarkhau/pylint-ignore/badges/master/coverage.svg
[codecov_ref]: https://mbarkhau.gitlab.io/pylint-ignore/cov

[license_img]: https://img.shields.io/badge/License-MIT-blue.svg
[license_ref]: https://gitlab.com/mbarkhau/pylint-ignore/blob/master/LICENSE

[mypy_img]: https://img.shields.io/badge/mypy-checked-green.svg
[mypy_ref]: https://mbarkhau.gitlab.io/pylint-ignore/mypycov

[style_img]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[style_ref]: https://gitlab.com/mbarkhau/straitjacket/

[pypi_img]: https://img.shields.io/badge/PyPI-wheels-green.svg
[pypi_ref]: https://pypi.org/project/pylint-ignore/#files

[downloads_img]: https://pepy.tech/badge/pylint-ignore/month
[downloads_ref]: https://pepy.tech/project/pylint-ignore

[version_img]: https://img.shields.io/static/v1.svg?label=PyCalVer&message=2020.1002&color=blue
[version_ref]: https://pypi.org/project/pycalver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/pylint-ignore.svg
[pyversions_ref]: https://pypi.python.org/pypi/pylint-ignore
