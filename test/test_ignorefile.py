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

from pylint_ignore import ignorefile

PROJECT_DIR = pl.Path(__file__).parent.parent

INIT_FILE_PATH = str(PROJECT_DIR / "src" / "pylint_ignore" / "__init__.py")


LINE_TEST_CASES = [
    "## File src/pylint_ignore/__main__.py - Line 91 - R0902 (too-many-instance-attributes)",
    "- ## File src/pylint_ignore/__main__.py - Line 91 - R0902 (too-many-instance-attributes)",
    "- `message: Too many instance attributes (10/7)`",
    "- `author : Manuel Barkhau <mbarkhau@gmail.com>`",
    " - `date   : 2020-07-17T09:59:24`",
]


def test_regex_entry_header():
    maybe_matches = [ignorefile.ENTRY_HEADER_RE.match(case) for case in LINE_TEST_CASES]
    matches       = [m.groupdict() for m in maybe_matches if m]
    expected      = [
        {
            'path'  : "src/pylint_ignore/__main__.py",
            'lineno': "91",
            'msg_id': "R0902",
            'symbol': "too-many-instance-attributes",
        }
    ]
    assert matches == expected


def test_regex_list_item():
    maybe_matches = [ignorefile.LIST_ITEM_RE.match(case) for case in LINE_TEST_CASES]
    matches       = [m.groupdict() for m in maybe_matches if m]
    expected      = [
        {'key': "message", 'value': "Too many instance attributes (10/7)"},
        {'key': "author" , 'value': "Manuel Barkhau <mbarkhau@gmail.com>"},
        {'key': "date"   , 'value': "2020-07-17T09:59:24"},
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
    match       = ignorefile.SOURCE_TEXT_RE.match(source_text)
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
    match       = ignorefile.SOURCE_TEXT_RE.match(source_text)
    assert match.group("def_line"     ) == "    def _parse_args(self, args: typ.List[str]) -> None:"
    assert match.group("def_lineno"   ) == "124"
    assert match.group("source_line"  ) == "        # TODO (mb 2020-07-17): This will bla"
    assert match.group("source_lineno") == "155"


def test_regex_source_text_edgecase():
    source_text = '''
    ```
       96:
       97:
    >  98: class PylintIgnoreDecorator:
       99:     # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
      100:     #   pattern, rather than the typical usage in python which is about function
    ```
    '''
    source_text = textwrap.dedent(source_text.lstrip("\n").rstrip(" "))
    match       = ignorefile.SOURCE_TEXT_RE.match(source_text)
    assert match.group("source_line"  ) == "class PylintIgnoreDecorator:"
    assert match.group("source_lineno") == "98"


def test_read_source_lines():
    lines = ignorefile.read_source_lines(INIT_FILE_PATH)

    tzero        = time.time()
    lines_cached = ignorefile.read_source_lines(INIT_FILE_PATH)
    duration_ms  = (time.time() - tzero) * 1000

    assert duration_ms < 1, "access to cached reference should be cheap"
    assert lines is lines_cached

    assert lines[4] == "# SPDX-License-Identifier: MIT\n"


def test_read_source_text():
    srctxt = ignorefile.read_source_text(INIT_FILE_PATH, 3, 5)
    assert srctxt.def_line_idx is None
    assert srctxt.def_line     is None
    assert srctxt.new_lineno == 3
    assert srctxt.old_lineno == 5
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
    lineno = ignorefile.find_source_text_lineno(
        INIT_FILE_PATH, "# SPDX-License-Identifier: MIT\n", 5
    )
    assert lineno == 5

    lineno = ignorefile.find_source_text_lineno(
        INIT_FILE_PATH, "# SPDX-License-Identifier: MIT\n", 1
    )
    assert lineno == 5

    lineno = ignorefile.find_source_text_lineno(
        INIT_FILE_PATH, "# SPDX-License-Identifier: MIT\n", 8
    )
    assert lineno == 5


TEST_IGNOREFILE_TEXT = """

## File src/pylint_ignore/__main__.py - Line 100 - R0902 (too-many-instance-attributes)

- `message: Too many instance attributes (10/7)`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-17T09:59:24`


```
  100:     # prefer name associated with the type of the repo
  109:     if is_hg_repo and hg_username:
> 100:         return hg_username
  111:     if is_git_repo and git_username:
  112:         return git_username
```


## File src/pylint_ignore/__main__.py - Line 190 - W0511 (fixme)

- `message: TODO (mb 2020-07-17): This will override any configuration, but it is not`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-17T11:39:54`


```
  153:     def _init_from_args(self, args: typ.Sequence[str]) -> None:
  ...
  188:             raise SystemExit(USAGE_ERROR)
  189:
> 190:         # TODO (mb 2020-07-17): This will override any configuration, but it is not
  191:         #   ideal. It would be better if we could use the same config parsing logic
  192:         #   as pylint and raise an error if anything other than jobs=1 is configured
```


## File src/pylint_ignore/__main__.py - Line 303 - C0415 (import-outside-toplevel)

- `message: Import outside toplevel (pylint.lint)`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-17T10:50:36`

```
  295: def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
  ...
  301:         try:
  302:             # We don't want to load this code before the monkey patching is done.
> 303:             import pylint.lint
  304:
  305:             pylint.lint.Run(dec.pylint_run_args)
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
        fobj.write(TEST_IGNOREFILE_TEXT)
    yield tmpfile
    tmpfile.unlink()


def test_iter_entry_values(tmp_ignorefile):
    entry_values = list(ignorefile._iter_entry_values(tmp_ignorefile))

    expected_values = [
        {
            'path'  : "src/pylint_ignore/__main__.py",
            'lineno': "100",
            'msg_id': "R0902",
            'symbol': "too-many-instance-attributes",
            'author': "Manuel Barkhau <mbarkhau@gmail.com>",
            'date'  : "2020-07-17T09:59:24",
        },
        {
            'path'  : "src/pylint_ignore/__main__.py",
            'lineno': "190",
            'msg_id': "W0511",
            'symbol': "fixme",
            'author': "Manuel Barkhau <mbarkhau@gmail.com>",
            'date'  : "2020-07-17T11:39:54",
        },
        {
            'path'  : "src/pylint_ignore/__main__.py",
            'lineno': "303",
            'msg_id': "C0415",
            'symbol': "import-outside-toplevel",
            'author': "Manuel Barkhau <mbarkhau@gmail.com>",
            'date'  : "2020-07-17T10:50:36",
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
        missing_keys = expected_keys - set(actual.keys())
        assert not missing_keys

        actual_items   = set(actual.items())
        expected_items = set(expected.items())
        missing_items  = expected_items - actual_items
        assert not missing_items

        assert actual['ctx_src_text'].startswith("```\n")
        assert actual['ctx_src_text'].endswith("```\n")


def test_load(tmp_ignorefile):
    _catalog = ignorefile.load(tmp_ignorefile)
    assert isinstance(_catalog, dict)
    # NOTE (mb 2020-07-17): one message was removed because it's obsolete
    assert len(_catalog) == 3

    keys    = list(_catalog.keys())
    entries = list(_catalog.values())

    _todo_text = "TODO (mb 2020-07-17): This will override any configuration, but it is not"

    assert keys[1].msg_id == "W0511"
    assert keys[1].path   == "src/pylint_ignore/__main__.py"
    assert keys[1].symbol == "fixme"

    assert entries[1].msg_id   == "W0511"
    assert entries[1].path     == "src/pylint_ignore/__main__.py"
    assert entries[1].symbol   == "fixme"
    assert entries[1].msg_text == _todo_text

    assert entries[1].srctxt.old_lineno == 190
    assert entries[1].srctxt.new_lineno == 190

    # NOTE (mb 2020-07-17): This is different than what's in the ignorefile,
    #       so it must come from the source file.
    expected_source_line = """
        # TODO (mb 2020-07-17): This will override any configuration, but it is not
    """
    expected_source_line = expected_source_line.lstrip("\n").rstrip(" ")
    assert keys[1].source_line == expected_source_line


def test_dump(tmp_ignorefile):
    in_catalog = ignorefile.load(tmp_ignorefile)
    assert len(in_catalog) == 3

    tmpdir   = tmp_ignorefile.parent
    out_file = pl.Path(str(tmpdir)) / "pylint-ignore-output.md"

    ignorefile.dump(in_catalog, out_file)

    with out_file.open() as fobj:
        catalog_text = fobj.read()

    assert catalog_text.startswith(ignorefile.IGNOREFILE_HEADER)

    out_catalog = ignorefile.load(out_file)
    # NOTE (mb 2020-07-18): The C0415 entry was removed
    assert len(out_catalog) == 2

    in_entries  = list(in_catalog.values())[:2]
    out_entries = list(out_catalog.values())[:2]
    for in_entry, out_entry in zip(in_entries, out_entries):
        assert in_entry.msg_id   == out_entry.msg_id
        assert in_entry.path     == out_entry.path
        assert in_entry.symbol   == out_entry.symbol
        assert in_entry.msg_text == out_entry.msg_text

        assert in_entry.author == out_entry.author
        assert in_entry.date   == out_entry.date

        if in_entry.srctxt is None and out_entry.srctxt is None:
            continue

        assert in_entry.srctxt.new_lineno   == out_entry.srctxt.new_lineno
        assert in_entry.srctxt.old_lineno   == out_entry.srctxt.old_lineno
        assert in_entry.srctxt.source_line  == out_entry.srctxt.source_line
        assert in_entry.srctxt.text         == out_entry.srctxt.text
        assert in_entry.srctxt.start_idx    == out_entry.srctxt.start_idx
        assert in_entry.srctxt.end_idx      == out_entry.srctxt.end_idx
        assert in_entry.srctxt.def_line_idx == out_entry.srctxt.def_line_idx
        assert in_entry.srctxt.def_line     == out_entry.srctxt.def_line
