# -*- coding: utf-8 -*-
# pylint:disable=redefined-outer-name ; pytest.fixture tmp_ignorefile
# pylint:disable=protected-access ; ok for testing

import os
import time
import shutil
import pathlib as pl
import textwrap

import pytest

from pylint_ignore import ignorefile

PROJECT_DIR = pl.Path(__file__).parent.parent

FIXTURES_DIR = PROJECT_DIR / "fixtures"

FIXTURE_FILE_PATH = str(FIXTURES_DIR / "fixture_1.py")


LINE_TEST_CASES = [
    "## File src/pylint_ignore/ignorefile.py - R0801 (duplicate-code)",
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
            'path'  : "src/pylint_ignore/ignorefile.py",
            'lineno': None,
            'msgid' : "R0801",
            'symbol': "duplicate-code",
        },
        {
            'path'  : "src/pylint_ignore/__main__.py",
            'lineno': "91",
            'msgid' : "R0902",
            'symbol': "too-many-instance-attributes",
        },
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
    lines = ignorefile.read_source_lines(FIXTURE_FILE_PATH)

    tzero        = time.time()
    lines_cached = ignorefile.read_source_lines(FIXTURE_FILE_PATH)
    duration_ms  = (time.time() - tzero) * 1000

    assert duration_ms < 1, "access to cached reference should be cheap"
    assert lines is lines_cached

    assert lines[3] == "def function_redefined():\n"
    assert lines[6] == "def code_duplication():\n"


def test_read_source_text():
    srctxt = ignorefile.read_source_text(FIXTURE_FILE_PATH, 4, 7)
    assert srctxt.def_line_idx is None
    assert srctxt.def_line     is None
    assert srctxt.new_lineno == 4
    assert srctxt.old_lineno == 7
    expected_text = """
        return 1

    def function_redefined():
        return 1

    """
    expected_text = textwrap.dedent(expected_text).lstrip("\n")
    assert srctxt.text.startswith(expected_text)


def test_find_source_text_lineno():
    lineno = ignorefile.find_source_text_lineno(FIXTURE_FILE_PATH, "def code_duplication():\n", 1)
    assert lineno == 7

    lineno = ignorefile.find_source_text_lineno(FIXTURE_FILE_PATH, "def code_duplication():\n", 7)
    assert lineno == 7

    lineno = ignorefile.find_source_text_lineno(FIXTURE_FILE_PATH, "def code_duplication():\n", 20)
    assert lineno == 7


TEST_IGNOREFILE_TEXT = """

# E0102: function-redefined

## File fixtures/fixture_1.py - Line 7 - E0102 (function-redefined)

- `message: function already defined line 1`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-25T18:38:31`

```
  5:     return 1
  6:
> 7: def function_redefined():
  8:     return 1
  9:
```

# E0666: invalid-obsolete

## File fixtures/fixture_1.py - Line 10 - E0666 (invalid-obsolete)

- `message: Undefined variable 'Entry'`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-25T18:38:32`

```
   7: def code_duplication():
  ...
   8:     msg_id_count = {}
   9:
> 10:     def _obsolete_code(e: Obsolete):
  11:         frequency = -msg_id_count[e.msg_id]
  12:         return frequency, e.msg_id
```

# R0801: duplicate-code

## File fixtures/fixture_2.py - R0801 (duplicate-code)

- `message: Similar lines in 2 files`
- `author : Manuel Barkhau <mbarkhau@gmail.com>`
- `date   : 2020-07-25T18:38:33`

```
==fixture_1:0
==fixture_2:0
def function_redefined():
    return 1

def function_redefined():
    return 1

def code_duplication():
    msg_id_count = {}

    def _entry_sort_key(e: Entry):
        frequency = -msg_id_count[e.msg_id]
        return frequency, e.msg_id

    return sorted(entries, key=_entry_sort_key)
```

"""


@pytest.fixture()
def tmp_ignorefile(tmpdir):
    # NOTE (mb 2020-07-17): Since we use the project files, this might be brittle.
    #       If this becomes an issue, we'll have to create some dedicated fixtures.
    os.chdir(str(tmpdir))

    shutil.copytree(str(FIXTURES_DIR), str(tmpdir / "fixtures"))
    tmpfile = pl.Path(str(tmpdir / "pylint-ignore.md"))
    with tmpfile.open(mode="w", encoding="utf-8") as fobj:
        fobj.write(TEST_IGNOREFILE_TEXT)
    yield tmpfile
    tmpfile.unlink()


def test_iter_entry_values(tmp_ignorefile):
    entry_values = list(ignorefile._iter_entry_values(tmp_ignorefile))

    expected_values = [
        {
            'path'  : "fixtures/fixture_1.py",
            'lineno': "7",
            'msgid' : "E0102",
            'symbol': "function-redefined",
            'author': "Manuel Barkhau <mbarkhau@gmail.com>",
            'date'  : "2020-07-25T18:38:31",
        },
        {
            'path'  : "fixtures/fixture_1.py",
            'lineno': "10",
            'msgid' : "E0666",
            'symbol': "invalid-obsolete",
            'author': "Manuel Barkhau <mbarkhau@gmail.com>",
            'date'  : "2020-07-25T18:38:32",
        },
        {
            'path'  : "fixtures/fixture_2.py",
            'lineno': None,
            'msgid' : "R0801",
            'symbol': "duplicate-code",
            'author': "Manuel Barkhau <mbarkhau@gmail.com>",
            'date'  : "2020-07-25T18:38:33",
        },
    ]

    assert len(entry_values) == len(expected_values)

    expected_keys = {
        'path',
        'lineno',
        'msgid',
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

    assert keys[0].msgid       == "E0102"
    assert keys[0].path        == "fixtures/fixture_1.py"
    assert keys[0].symbol      == "function-redefined"
    assert keys[0].msg_text    == "function already defined line 1"
    assert keys[0].source_line == "def function_redefined():\n"

    assert entries[0].msgid    == "E0102"
    assert entries[0].path     == "fixtures/fixture_1.py"
    assert entries[0].symbol   == "function-redefined"
    assert entries[0].msg_text == "function already defined line 1"

    assert entries[0].srctxt.old_lineno == 7
    assert entries[0].srctxt.new_lineno == 4

    assert entries[1].srctxt is None


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
    assert len(out_catalog) == 3

    in_entries  = list(in_catalog.values())[:2]
    out_entries = list(out_catalog.values())[:2]
    for in_entry, out_entry in zip(in_entries, out_entries):
        assert in_entry.msgid    == out_entry.msgid
        assert in_entry.path     == out_entry.path
        assert in_entry.symbol   == out_entry.symbol
        assert in_entry.msg_text == out_entry.msg_text

        assert in_entry.author == out_entry.author
        assert in_entry.date   == out_entry.date

        if in_entry.srctxt is None and out_entry.srctxt is None:
            continue

        assert in_entry.srctxt.new_lineno == out_entry.srctxt.new_lineno
        # assert in_entry.srctxt.old_lineno   == out_entry.srctxt.old_lineno
        assert in_entry.srctxt.source_line  == out_entry.srctxt.source_line
        assert in_entry.srctxt.text         == out_entry.srctxt.text
        assert in_entry.srctxt.start_idx    == out_entry.srctxt.start_idx
        assert in_entry.srctxt.end_idx      == out_entry.srctxt.end_idx
        assert in_entry.srctxt.def_line_idx == out_entry.srctxt.def_line_idx
        assert in_entry.srctxt.def_line     == out_entry.srctxt.def_line


def test_find_entry(tmp_ignorefile):
    _catalog = ignorefile.load(tmp_ignorefile)
    for key, entry in _catalog.items():
        assert ignorefile.find_entry(_catalog, key) is entry

        fuzzy_key = ignorefile.Key(
            key.msgid,
            key.path,
            key.symbol,
            key.msg_text,
            "    " + key.source_line,
        )

        assert ignorefile.find_entry(_catalog, fuzzy_key) is entry
