# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import time
import shutil
import textwrap

import pytest
import pathlib2 as pl

from pylint_ignore import catalog

PROJECT_DIR = pl.Path(__file__).parent.parent

INIT_FILE_PATH = str(PROJECT_DIR / "src" / "pylint_ignore" / "__init__.py")


LINE_TEST_CASES = [
    "## File: src/pylint_ignore/__main__.py",
    "### Line 91 - R0902 (too-many-instance-attributes)",
    "## File: src/pylint_ignore/catalog.py",
    "## File: pylint_ignore/catalog.py",
    "## File: pylint_ignore/catalog.txt",
    "- ## File: pylint_ignore/catalog.py",
    "- ### Line 91 - R0902 (too-many-instance-attributes)",
    "- message: Too many instance attributes (10/7)",
    "- author : Manuel Barkhau <mbarkhau@gmail.com>",
    " - date   : 2020-07-17T09:59:24",
    " - ignored: no",
    "- ignored: Yes, really! I know what I'm doing, leave me alone mom!",
]


def test_regex_file_header():
    maybe_matches = [catalog.FILE_HEADER_RE.match(case) for case in LINE_TEST_CASES]
    matches       = [m.groupdict() for m in maybe_matches if m]
    expected      = [
        {'path': "src/pylint_ignore/__main__.py"},
        {'path': "src/pylint_ignore/catalog.py"},
        {'path': "pylint_ignore/catalog.py"},
        {'path': "pylint_ignore/catalog.txt"},
    ]
    assert matches == expected


def test_regex_entry_header():
    maybe_matches = [catalog.ENTRY_HEADER_RE.match(case) for case in LINE_TEST_CASES]
    matches       = [m.groupdict() for m in maybe_matches if m]
    expected      = [{'lineno': "91", 'msg_id': "R0902", 'symbol': "too-many-instance-attributes"}]
    assert matches == expected


def test_regex_list_item():
    maybe_matches = [catalog.LIST_ITEM_RE.match(case) for case in LINE_TEST_CASES]
    matches       = [m.groupdict() for m in maybe_matches if m]
    expected      = [
        {'key': "message", 'value': "Too many instance attributes (10/7)"},
        {'key': "author" , 'value': "Manuel Barkhau <mbarkhau@gmail.com>"},
        {'key': "date"   , 'value': "2020-07-17T09:59:24"},
        {'key': "ignored", 'value': "no"},
        {'key': "ignored", 'value': "Yes, really! I know what I'm doing, leave me alone mom!"},
    ]
    assert matches == expected


def test_regex_source_text_basic():
    source_text = """
    ```
      89:
      90:
    > 91: class PylintIgnoreDecorator:
      92:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
      93:     #   pattern, rather than the typical usage in python which is about function
    ```
    """
    source_text = textwrap.dedent(source_text).strip()
    match       = catalog.SOURCE_TEXT_RE.match(source_text)
    assert match.group("source_lineno") == "91"
    assert match.group("source_line"  ) == "class PylintIgnoreDecorator:"


def test_regex_source_text_def_line():
    source_text = """
    ```
      124:     def _parse_args(self, args: typ.List[str]) -> None:
      ...
      153:             arg_i += 1
      154:
    > 155:         # TODO (mb 2020-07-17): This will bla
      156:         #   bla
      157:         #   bla
    ```
    """
    source_text = textwrap.dedent(source_text).strip()
    match       = catalog.SOURCE_TEXT_RE.match(source_text)
    assert match.group("def_line"     ) == "    def _parse_args(self, args: typ.List[str]) -> None:"
    assert match.group("def_lineno"   ) == "124"
    assert match.group("source_line"  ) == "        # TODO (mb 2020-07-17): This will bla"
    assert match.group("source_lineno") == "155"


def test_read_source_lines():
    lines = catalog.read_source_lines(INIT_FILE_PATH)

    tzero        = time.time()
    lines_cached = catalog.read_source_lines(INIT_FILE_PATH)
    duration_ms  = (time.time() - tzero) * 1000

    assert duration_ms < 1, "access to cached reference should be cheap"
    assert lines is lines_cached

    assert lines[4] == "# SPDX-License-Identifier: MIT\n"


def test_read_source_text():
    srctxt = catalog.read_source_text(INIT_FILE_PATH, 3)
    assert srctxt.def_line_idx is None
    assert srctxt.def_line     is None
    assert srctxt.lineno == 3
    expected_text = """
    # This file is part of the pylint-ignore project
    # https://gitlab.com/mbarkhau/pylint-ignore
    #
    # Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
    # SPDX-License-Identifier: MIT
    """
    expected_text = textwrap.dedent(expected_text).lstrip()
    assert srctxt.text == expected_text


def test_find_source_text_lineno():
    lineno = catalog.find_source_text_lineno(INIT_FILE_PATH, "# SPDX-License-Identifier: MIT\n", 5)
    assert lineno == 5

    lineno = catalog.find_source_text_lineno(INIT_FILE_PATH, "# SPDX-License-Identifier: MIT\n", 1)
    assert lineno == 5

    lineno = catalog.find_source_text_lineno(INIT_FILE_PATH, "# SPDX-License-Identifier: MIT\n", 8)
    assert lineno == 5


TEST_CATALOG_TEXT = """

## File: src/pylint_ignore/__main__.py

### Line 91 - R0902 (too-many-instance-attributes)

- message: Too many instance attributes (10/7)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T09:59:24


```
  89:
  90:
> 91: class PylintIgnoreDecorator:
  92:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
  93:     #   pattern, rather than the typical usage in python which is about function
```


### Line 155 - W0511 (fixme)

- message: TODO (mb 2020-07-17): This will override any configuration, but it is not
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T11:39:54

```
  124:     def _parse_args(self, args: typ.List[str]) -> None:
  ...
  153:             arg_i += 1
  154:
> 155:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  156:         #   ideal. It would be better if we could use the same config parsing logic
  157:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


### Line 293 - C0415 (import-outside-toplevel)

- message: Import outside toplevel (pylint.lint)
- author : Manuel Barkhau <mbarkhau@gmail.com>
- date   : 2020-07-17T10:50:36
- ignored: because intentional

```
  286: def main() -> ExitCode:
  ...
  291:     try:
  292:         # The only line use for search is the one with the ">"
> 293:         import pylint.lint
  294:
  295:         pylint.lint.Run(this is not invalid)
```

"""


@pytest.fixture()
def tmp_ignorefile(tmpdir):
    # NOTE (mb 2020-07-17): Since we use the project files, this might be brittle.
    #       If this becomes an issue, we'll have to create some dedicated fixtures.
    os.chdir(str(tmpdir))

    shutil.copytree(str(PROJECT_DIR / "src"), str(tmpdir / "src"))
    tmpfile = pl.Path(str(tmpdir / "pylint-ignore.md"))
    with tmpfile.open(mode="w", encoding="utf-8") as fobj:
        fobj.write(TEST_CATALOG_TEXT)
    yield tmpfile
    tmpfile.unlink()


def test_iter_entry_values(tmp_ignorefile):
    tmpdir       = tmp_ignorefile.parent
    entry_values = list(catalog._iter_entry_values(tmp_ignorefile))

    expected_values = [
        {
            'path'  : str(tmpdir / "src" / "pylint_ignore" / "__main__.py"),
            'lineno': "91",
            'msg_id': "R0902",
            'symbol': "too-many-instance-attributes",
        },
        {
            'path'  : str(tmpdir / "src" / "pylint_ignore" / "__main__.py"),
            'lineno': "155",
            'msg_id': "W0511",
            'symbol': "fixme",
        },
        {
            'path'   : str(tmpdir / "src" / "pylint_ignore" / "__main__.py"),
            'lineno' : "293",
            'msg_id' : "C0415",
            'symbol' : "import-outside-toplevel",
            'ignored': "because intentional",
        },
    ]

    assert len(entry_values) == len(expected_values)

    expected_keys = {
        'path',
        'lineno',
        'msg_id',
        'symbol',
        'message',
        'author',
        'date',
        'ctx_src_text',
    }
    for actual, expected in zip(entry_values, expected_values):
        actual_items   = set(actual.items())
        expected_items = set(expected.items())
        assert expected_items <= actual_items
        assert expected_keys  <= set(actual.keys())
        assert actual['ctx_src_text'].startswith("```\n")
        assert actual['ctx_src_text'].endswith("```\n")


def test_load(tmp_ignorefile):
    tmpdir = tmp_ignorefile.parent

    _catalog = catalog.load(tmp_ignorefile)
    assert isinstance(_catalog, dict)
    assert len(_catalog) == 3

    keys    = list(_catalog.keys())
    entries = list(_catalog.values())

    assert keys[2].msg_id   == "C0415"
    assert keys[2].path     == str(tmpdir / "src" / "pylint_ignore" / "__main__.py")
    assert keys[2].symbol   == "import-outside-toplevel"
    assert keys[2].msg_text == "Import outside toplevel (pylint.lint)"

    assert entries[2].msg_id   == "C0415"
    assert entries[2].path     == str(tmpdir / "src" / "pylint_ignore" / "__main__.py")
    assert entries[2].symbol   == "import-outside-toplevel"
    assert entries[2].msg_text == "Import outside toplevel (pylint.lint)"

    assert entries[2].srctxt.lineno == 296
    assert entries[2].ignored       == "because intentional"

    # NOTE (mb 2020-07-17): This is different than what's in the ignorefile,
    #       so it must come from the source file.
    expected_ctx_src_text = """
    try:
        # We don't want to load this code before the monkey patching is done.
        import pylint.lint

        pylint.lint.Run(dec.pylint_run_args)
    """
    expected_ctx_src_text = expected_ctx_src_text.lstrip("\n").rstrip(" ")
    assert keys[2].ctx_src_text == expected_ctx_src_text


def test_dump(tmp_ignorefile):
    _in_catalog = catalog.load(tmp_ignorefile)

    # def dump(catalog: Catalog, catalog_path: pl.Path) -> None:
    tmpdir   = tmp_ignorefile.parent
    out_file = pl.Path(str(tmpdir)) / "pylint-ignore-output.md"
    catalog.dump(_in_catalog, out_file)

    with out_file.open() as fobj:
        catalog_text = fobj.read()

    assert catalog_text.startswith(catalog.CATALOG_HEADER)

    _out_catalog = catalog.load(out_file)
    assert _in_catalog == _out_catalog, "serialization round trip failed"
