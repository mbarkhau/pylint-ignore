<div align="center">
<p align="center">
  <img alt="logo" src="https://gitlab.com/mbarkhau/pylint-ignore/-/raw/master/logo_256.png">
</p>
</div>


# [Pylint-Ignore][repo_ref]

Start with silence, not with noise. But do start!

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![CalVer 2020.1011][version_img]][version_ref]
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


## Developer Ergonomics

The main issue with Pylint is developer ergonomics. The messages produced by Pylint *can* be valuable, but you have to put in some work before you can use it productively. If you have an established codebase, you'll probably have to:

- research configuration options
- disable many unhelpful messages
- blindly litter your code with `pylint:disable` comments.

Using Pylint-Ignore you can benefit from Pylint today. You won't have to wade through endless message noise first, won't have to spend time with configuration, you won't have to change anything about your code. Even though you start with all messages ignored for existing code, you can benefit from Pylint right away for any new code you write.

What about the wall of messages for your existing code? Well, at least you can gradually improve your situation, as you have time for it. In other words, you may be dug into a hole right now, but at least you can stop digging yourself any deeper and gradually start climbing back out.


## How it Works

The `pylint-ignore` command is a thin wrapper around the Pylint command. You can get started with a minimal configuration file such as this [`setup.cfg`](doc/setup.cfg) and running the following commands.

```shell
$ pip install pylint-ignore

Installing collected packages: astroid,isort,pylint,pylint-ignore
...
Successfully installed pylint-ignore-2020.1006

$ pylint-ignore --rcfile=setup.cfg src/

************* Module src/mymodule.py
src/mymodule.py:290:0: W0102: Dangerous default value sys.argv[1:] (builtins.list) as argument (dangerous-default-value)
...

-------------------------------------------------------------------
Your code has been rated at 9.92/10

$ echo $?     # exit status != 0
28
```

The `pylint-ignore` command reads a file called `pylint-ignore.md`, which you should keep as part of your repository. This file contains messages that should be ignored and it is automatically updated with new entries if you specify the `--update-ignorefile` parameter.

```shell
$ pylint-ignore --rcfile=setup.cfg src/ --update-ignorefile

-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 9.92/10, +0.08)

$ echo $?     # exit status == 0
0
```

The original message no longer shows up in the output, and it is instead logged in the `pylint-ignore.md`, which will now look something like this:

~~~
...
## File src/mymodule.py - Line 290 - W0102 (dangerous-default-value)

- message: Dangerous default value sys.argv[1:] (builtins.list) as argument
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T21:15:25

```
  289:
> 290: def main(args: Sequence[str] = sys.argv[1:]) -> ExitCode:
  291:     try:
```
~~~

Ideally you should only do this once when you start to use Pylint and going forward the file will only get smaller. As your time permits, the recommended approach to using `pylint-ignore` is the following:

1. If a message refers to a valid issue (errors and warnings in particular), update your code so the issue is resolved.
2. If a message is a false positive, add a comment of this form to your code:
   `# pylint:disable=<symbol> ; explain why this is a false positive`
3. If it is a useless message (e.g. a whitespace rule that conflicts with the behaviour of your code formatter) which should *always* be ignored, then do so via your `pylintrc` or `setup.cfg` file.

In principal these are the same options you have when using Pylint by itself. For the above example, `dangerous-default-value` [is a useful message in general](https://docs.python-guide.org/writing/gotchas/#mutable-default-arguments)) just not in this particular case. You might take the approach of option 2. and add a `pylint:disable` comment:

```python
def main(args: Sequence[str] = sys.argv[1:]) -> ExitCode:
    # pylint:disable=dangerous-default-value;  args is not mutated
    # mypy prevents this because Sequence[str] does not support mutation
    try:
```

With this change, the next time you run `pylint-ignore --update-ignorefile`, the corresponding entry will disappear and the backlog will shrink.


### CLI Usage

The `pylint-ignore` ignore command does not have its own help message. The `--help` argument will simply behave exactly the same as `pylint --help`. These are the parameters the `pylint-ignore` supports:

```
Usage: pylint-ignore [options]

Options:
  --ignorefile=<FILE>    Path to ignore file [default: pylint-ignore.md]
  --update-ignorefile    Update the ignorefile, adds new messages,
                         removes any messages that are no longer
                         emmitted by pylint (were fixed or disabled)
```

Normally the `pylint-ignore` command will not update the `pylint-ignore.md` file. This is appropriate for

- Normal development if it's your policy to not introduce any new issues.
- CI/CD build systems, where you want to report any issues that were newly introduced.

If you fix an issue or explicitly disable a message, you can cleanup obsolete entries by adding the `--update-ignorefile` argument.

```shell
$ pylint-ignore --update-ignorefile --ignorefile=etc/pylint-ignore.md \
    --rc-file=setup.cfg src/ test/
```

Caveat: If you change some code for which there is an entry in the `pylint-ignore.md` file, the entry may no longer be matched up with the message as it is generated by Pylint. Usually changes in line numbers will be detected as long as the code itself did not change and your build will not fail if that is the case. Hopefully you will not feel the need to blindly use the `--update-ignorefile` argument, but you may need to use it occasionally, simply to refresh an existing entry that became invalid. You can of course also take such an occasion as an opportunity to deal with the underlying issue.


### The `pylint-ignore.md`  file

You can view an example file here: [fixtures/pylint-ignore.md](https://gitlab.com/mbarkhau/pylint-ignore/-/blob/master/fixtures/pylint-ignore.md). You can consider this file as a backlog of possible issues. The entries are sorted first by category, i.e. errors and warnings first then by frequency. You can change the path/filename using the `--ignorefile` parameter: `pylint-ignore --ignorefile=etc/pylint-backlog.md`

The `pylint-ignore.md` file uses a bespoke format but it is valid markdown. This choice is primarily so that you can read it and review it more easily on platforms such as github/gitlab/bitbucket. You don't have to edit the file and it is not a format that any other program has to parse, so I think this is a reasonable choice.

What does this approach solve, why not just use Pylint by itself?


## Why use Pylint-Ignore

### Problem 1: Noise

There is a reason flake8 is used so much more often than Pylint. The problem of "noise" is acknowledged [early in the documentation](http://pylint.pycqa.org/en/stable/tutorial.html) of Pylint. In fact, the frustration of using Pylint is so obvious that it is even the topic of the projects tag-line: "It's not just a linter that annoys you!".

Pylint-Ignore doesn't get rid of this noise of course, but it does put in a dedicated place, rather than Spam in your terminal. Each issue with your code is one entry in a file, rather than a line that you have to scan again and again.

Once you've established silence as your baseline, you can trust that you  only have to deal with two states: OK and FAIL. This vastly reduces cognitive load for developers and makes it possible for you to integrate the linter into your CI system, even if you haven't yet dealt with every last Pylint message.


### Problem 2: Setup Cost

I won't belabour this point, but it's better if you can spend as little time as possible to just get started using a useful tool, rather than putting it off into the future, possibly indefinitely or only using it occasionally rather than making it a part of your regular workflow.

That being said, the sooner you take the time to pay down this setup cost, and to disable messages in your configuration that are actual noise, the more useful Pylint will be for you. Every useless message will increase the likelihood that you miss one of the more important messages.

Even if you've setup Pylint perfectly and are done with the initial cleanup of your codebase, there might be reason for you to continue to use Pylint-Ignore in your development workflow.


### Problem 3: Diligence is Scarce

Without Pylint-Ignore, chances are, you (or your teammates) will be overzealous with the `disable` section of your configuration. Sooner or later, you will be short on time and effectively turn the linter off. Who will later know or care to look if the message was disabled because it is genuinely useless or if you just had other priorities at that moment? You can try to remind yourself to review things, you can add a `TODO` comment which you hopefully remember to `grep` for regularly, but there is a high chance that such good intentions will sooner or later go by the wayside.

With Pylint-Ignore, you have a dedicated file in your repository, which is more explicit and visible than the other options. The entries are ordered by importance, rather than appearing more or less randomly on your terminal. You can focus your diligence on other things, and deal with minor linting issues when you have time, or perhaps leave them open as a first contribution for a new member of your team, just so they can get used to your workflow.


### Problem 4: Malicious Compliance

You may find some messages useful, but with an existing codebase, the work would be too much at once. You don't want to disable it, but you don't want to start with it enabled either. An example is perhaps the `missing-function-docstring` message. If you were to enabled it, you may find a pattern like this emerge:

```python
def get_author_name() -> str:
    """Gets the author name and returns it as a string."""
```

In case it's not obvious, the above doc-string is redundant, it adds no new information relative to what is already contained in the function name and types. In other words, the temptation is to pacify the linter by changing the code in ways that are at best a useless waste of time and at worst they are malicious and counterproductive.

You are in control, as you can just ignore and commit a change if you feel that ignoring the linter is justified by your current priorities. With Pylint-Ignore you don't have to halt the train because a delicate flower fainted in wagon 2 fainted at the sight of oil spraying all over her luggage and make your journey on-time. The `pylint-ignore.md` will keep track of the issue and you can deal with it once you've arrived at the station, not while you're running at full steam.


### Problem 5: False Positives

While you can and should deal with most false positives using `disable` comments, there are some cases where you'd rather not do that and [some cases where that isn't even possible](https://github.com/PyCQA/pylint/issues/214). For such edge cases, you can just permanently leave an entry in the `pylint-ignore.md` and still benefit from an otherwise useful message if new cases pop up.


## Motivation/Why use Pylint

If you are not convinced of the usefulness of Pylint, linters, or static analysis in general (and perhaps think they are mostly make-work for people who are overly pedantic) let me show you what convinced me to use Pylint.


### Dynamic Code and Scope Related Bugs

Some code may syntactically valid Python and will even execute without raising an error and yet is almost certainly not what the author intended. To be sure, if you have proper testing, you will catch such bugs, but even so, static analysis may pay its dues if it can help you catch such bugs more quickly.


```python
def frobnicate(seq: Sequence[int]):
    total = 0
    for value in seq:
        total += value
    return value / len(seq)
```

The above code will "work", depending on how you call it, it won't even throw an error and yet it is almost certainly not correct. Were the function longer than 5 lines, the bug would perhaps be less obvious. Just recently I spent at least an hour tracking down such a bug which had made it into production. In any case, Pylint will report the following message for such code:

```
W0631: Using possibly undefined loop variable 'value'
  (undefined-loop-variable)
```

There are other messages, related to [name shadowing](https://en.wikipedia.org/wiki/Variable_shadowing) and unused arguments that I have found to be particularly useful in that they have pointed to actual bugs, rather than "mere" preferences or "best-practices" according to the authors of Pylint.


### Supporting Code Review

The perhaps most important aspect of a linter, whenever working with other people, is that the feedback related to mundane issues of code styling will come from a computer rather than from another person. This is a benefit, both the reviewer and to the author:

- It is not fun to spend valuable time on giving repetitive feedback on mundane issues that can be automated.
- It's not fun, perhaps even embarrassing to have your own stupid mistakes be pointed out during review.

A linter also allows you establish a rule that will end discussions about subjective style preferences. Everybody might agree that any particular style is stupid, but the endless discussion about code style is even more stupid. So establish this rule: **If it passes the linter, the discussion is over** (except of course if the linter only passes because it was maliciously disabled). This is a similar argument as is made for the use of code formatters and it's main value is that it allows you to focus your review time on the actual problem related to the code.


### Catching Python Gotchas

Junior programmers and even (experienced programmers who are new to Python) may not be aware of common pitfalls of working with Python. They need every help they can get and you can look at static analysis as a form of codified knowledge and automated communication from experienced programmers. The code that *you* write may be perfect, but hell is other people, and Pylint can help to keep some minimum standards in your projects, even when you on-board new developers.


### A Nudge to Improve

When you're hacking away, focused entirely on solving the actual problem, getting the actual work™ done, you can end up with some code that may well work, may well pass all your test, may well be efficient and may well (let's just postulate for the sake of argument) actually be optimal and correct, that still doesn't mean it's understandable by anybody but the author.

```
R0902 Too many instance attributes (10/7) (too-many-instance-attributes)
```

Simple code metrics such as `too-many-locals`, `too-many-branches`, etc. may well be subjective, pedantic, paternalistic gamification nonsense and of course such [metrics should not be turned into targets](https://en.wikipedia.org/wiki/Goodhart%27s_law). The question is, how do you use them. If they are triggering very often, then the threshold may well be too low and you should increase it to a tolerable level.  If your code is actually perfect as it is, then there is no shame, perhaps it's even a badge of honor to add a comment such as this:

```python
class ToCoolForSchool():
    # pylint:disable=too-many-branches
    # behold this glorious perfection 🤘 — rockstar@unicorn.io
    ...
```

Such cases aside, a common reason for complicated code is that the author was ~~too lazy~~ didn't have the time to re-factor their code so that others could also understand it. I would caution against [code-golfing][href_wiki_code_golf] such cases, just to satisfy the linter. Just consider the message as a nudge to at least take a second look, to a least consider looking for obviously better ways to structure your code.


## Alternatives

To the extent that the excessive noise of Pylint has scared you away from using it, I hope you will find `pylint-ignore` helpful to at least get started. Here is another approach you may prefer.


### Selective Opt-In

An alternative approach is suggested by [Itamar Turner-Trauring with "Why Pylint is both useful and unusable, and how you can actually use it"](https://pythonspeed.com/articles/pylint/) is in essence to do the following:

 - First, setup Pylint to do nothing: disable all messages
 - Selectively enable some checks and keep them if they are valuable
 - Repeat

This is obviously abbreviated, so I encourage you to read his article if selective whitelisting is a better approach for you. For me, this approach suffers from the diligence issue, as it requires you to revisit the configuration at least a few times, keep track of what you've found to be valuable and so you run a higher risk of neglecting it.


### Automated disable comments

Another automated approach is to use [pylint-silent](https://pypi.org/project/pylint-silent/). Be sure to use version control if you consider this approach.


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

[version_img]: https://img.shields.io/static/v1.svg?label=CalVer&message=2020.1011&color=blue
[version_ref]: https://pypi.org/project/pycalver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/pylint-ignore.svg
[pyversions_ref]: https://pypi.python.org/pypi/pylint-ignore

[href_wiki_code_golf]: https://en.wikipedia.org/wiki/Code_golf
