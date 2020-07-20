<div align="center">
  <img alt="logo" src="https://gitlab.com/mbarkhau/pylint-ignore/-/raw/master/logo_256.png">
</div>

# [Pylint-Ignore][repo_ref]

More signal, less noise.

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![CalVer 2020.1005][version_img]][version_ref]
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


## Developer Ergonomics

The main issue with `pylint` is developer ergonomics. The messages produced by `pylint` can be valuable, but you have to put in some work before you can enable it in your CI setup. If you have an established codebase, you'll probably have to research its configuration options, disable many invalid messages and/or blindly litter your code with `pylint:disable` comments.

The goal of `pylint-ignore` is to let you benefit from `pylint` right now, without having to first wade through endless message noise and without having to delay using it because you don't have time to configure every detail.


## How it Works

The `pylint-ignore` command is a thin wrapper around the `pylint` command.

```shell
$ pip install pylint-ignore
Installing collected packages: astroid,isort,pylint,pylint-ignore
...
Successfully installed pylint-ignore-2020.1004
```

Assuming you have a minimal configuration such as this [`setup.cfg`](doc/setup.cfg).


You can invoke `pylint-ignore` like this:

```shell
$ pylint-ignore --rcfile=setup.cfg src/
************* Module src/mymodule.py
src/mymodule.py:290:0: W0102: Dangerous default value sys.argv[1:] (builtins.list) as argument (dangerous-default-value)
...

-------------------------------------------------------------------
Your code has been rated at 9.92/10 (previous run: 10.00/10, -0.08)
```

The `pylint-ignore` command reads its own configuration file called `pylint-ignore.md`. This file contains messages that should be ignored and it is automatically updated with new entries if you specify the `--update-ignorefile` parameter.

```shell
$ pylint-ignore --rcfile=setup.cfg src/ --update-ignorefile
-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 9.92/10, +0.08)
```

The `pylint-ignore.md` will now look something like this:

~~~shell
$ grep --after-context=15 --max-count=1 "## File" pylint-ignore.md

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

The recommended approach to using `pylint-ignore` is:

1. If a message refers to a valid issue, update your code rather than
   ignoring the message.
2. If a message should *always* be ignored (globally), then to do so
   via the usual `pylintrc` or `setup.cfg` files rather than this
  `pylint-ignore.md` file.
3. If a message is a false positive, add a comment of this form to your code:
   `# pylint:disable=<symbol> ; explanation why this is a false positive`


In principal these are the same options you have with `pylint` by itself. For this particular case I would prefer option 3.:

```python
def main(args: Sequence[str] = sys.argv[1:]) -> ExitCode:
    # pylint:disable=dangerous-default-value; args is not mutated, mypy ensures this
    try:
```

With this change, when you run `pylint-ignore --update-ignorefile` again, the entry in `pylint-ignore.md` is removed.

What does this solve?


## Problem1: Setup Cost

If you have a large existing project, your codebase will inevitably trigger many linting messages the first time you use `pylint`. You might take a first pass and try to reduce the noise. During this first pass, you will encounter two issues:

1. You will be overwhelmed at all the configuration options that you will need before you can trust that the output of `pylint` is meaningful.
2. You will find messages that might be useful in general, but after looking at particular cases, you find that the message is only useful sometimes.

An example of case 1. is perhaps the `missing-function-docstring` message. You know that is going to be way more work than is justified for your project. Even if you could justify the work in principle and agree that the message is valid, if you did enabled it, you may find a pattern like this emerge:

```python
def get_author_name() -> str:
    """Gets the author name and returns it as a string."""
```

In case it isn't obvious, the above doc-string is redundant because it adds no information that isn't already in the function signature. In other words, your colleagues are likely to pacify the linter by changing the code in ways that are at best a useless waste of time and at worst they are counterproductive.


## Problem2: Time Constraint

As you investigate messages, you will inevitably run across some that you disagree with, if not in general, then at least for the particular cases you're dealing with. Take for example this message:

```
R0902 Too many instance attributes (10/7) (too-many-instance-attributes)
```

Where you put the cutoff for "too-many" is a subjective matter. I would caution against [code-golfing][href_wiki_code_golf] such cases, just to satisfy the linter. It's a good message to have in general, if for no other reason than to wag a finger when somebody introduces some smelly code. Such a message can be a nudge to investigate further if there are reasonable ways to refactor the code and improve it.

With `pylint-ignore` you have a file in your repository that serves as a reminder of such cases, until you have time to look at them. In the meantime, because any *new messages* generated by `pylint` are not ignored, if any new code is introduced that is similarly smelly, you can catch it in your CI build.


## CLI Usage

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

- CI/CD build systems, where you want to report any issues that were newly introduced.
- Normal development, when you don't want to introduce any new issues.

If you fix an issue or explicitly disable a message, you can cleanup obsolete entries by adding the `--update-ignorefile` argument.

```shell
$ pylint-ignore --update-ignorefile --ignorefile=etc/pylint-ignore.md \
    --rc-file=setup.cfg src/ test/
```

Usually changes in line numbers will be detected and not cause your build to fail, but occasionally a message that was previously tracked may no longer be recognized. This can happen for example after you move some code to a different file. For such cases you may also want to use `--update-ignorefile` (or deal with the actual issue while you're refactoring...).


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

[version_img]: https://img.shields.io/static/v1.svg?label=CalVer&message=2020.1005&color=blue
[version_ref]: https://pypi.org/project/pycalver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/pylint-ignore.svg
[pyversions_ref]: https://pypi.python.org/pypi/pylint-ignore

[href_wiki_code_golf]: https://en.wikipedia.org/wiki/Code_golf
