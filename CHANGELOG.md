# Changelog for https://github.com/mbarkhau/pylint-ignore

## 2022.1025

- Pin `pylint<2.13`

Newer versions of pylint have different messages. Further work on
pylint-ignore is discouraged in favor of work on integrating
a "baseline" approach into pylint directly.

https://github.com/mbarkhau/pylint-ignore/issues/13


## 2021.1024

- Add/document support for [pre-commit](https://pre-commit.com/).
  Thank you James Quilty for this contribution [github/issue/9][gh_i9]
  [github/pull/10][gh_i10] :heart:.
- Fix [github #11][gh_i11]: MessagesHandlerMixIn has been removed in pylint 2.12
- Breaking: Drop support for `Python<3.7`
- Breaking: Drop support for `pylint<2.4`

  Due to internal API changes in pylint, older versions of pylint
  are no longer supported. If you need to use an older version of
  pylint, you will have to pin `pylint-ignore==2021.1021`.

[gh_i9]: https://github.com/mbarkhau/pylint-ignore/issues/9
[gh_i10]: https://github.com/mbarkhau/pylint-ignore/pull/10
[gh_i11]: https://github.com/mbarkhau/pylint-ignore/issues/11


## 2021.1020

- Fix [github #6][gh_i6]: Issue with paths on windows.

[gh_i6]: https://github.com/mbarkhau/pylint-ignore/issues/6

Thank you davidsheldon


## 2021.1019

- Fix [github #5][gh_i5]: Missing fixture files in source distribution
- Fix [github #4][gh_i4]: Bug related to trailing-whitespace

[gh_i5]: https://github.com/mbarkhau/pylint-ignore/issues/5
[gh_i4]: https://github.com/mbarkhau/pylint-ignore/issues/4

Thank you @agraul (Alexander Graul) for finding these issues.


## 2021.1018

- Fix [github #2][gh_i2]: Typerror

[gh_i2]: https://github.com/mbarkhau/pylint-ignore/issues/2


## 2020.1014

- Fix [gitlab #2][gl_i2]: Bug related to invokation with invalid arguments (which caused the underlying pylint error to be hidden).

[gl_i2]: https://gitlab.com/mbarkhau/pylint-ignore/-/issues/2


## 2020.1013

- Fix: bugs related to multiprocessing on MacOSX and Windows


## 2020.1012

- Fix: enable use of `--jobs=<n>` with `n > 1`


## 2020.1008 - 2020.1011

- Fix: compatability with python 2.7 and pylint 1.9.5


## 2020.1007

- Add overview section to `pylint-ignore.md` file.
- Fix: Handling of issues not related to a specific file or line (e.g. `duplicate-code` across multiple files)
- Fix: parsing of `--ignorefile` argument.
- Fix: parsing of `--jobs` argument.
- Allow ignore of `(E) error` messages again, prioritize entries, instead in ignorefile.


## 2020.1006

- Don't ignore messages of type `(E) error, for probable bugs in the code`

## 2020.1003

- Initial release
