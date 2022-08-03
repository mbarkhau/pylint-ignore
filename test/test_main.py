# -*- coding: utf-8 -*-
# pylint:disable=redefined-outer-name ; pytest.fixture ignore_file
# pylint:disable=protected-access ; ok for testing

import os
import sys
import shutil
import pathlib as pl

import pytest

import pylint_ignore.__main__ as main

PROJECT_DIR = pl.Path(__file__).parent.parent

FIXTURES_DIR = PROJECT_DIR / "fixtures"


main.TESTDEBUG = True


def test_get_author_name():
    author_name = main.get_author_name()
    assert len(author_name) > 0

    # NOTE (mb 2020-07-28): provoke error
    main._HG_USERNAME_CMD = "invalid-command --help"

    author_name = main.get_author_name()
    assert len(author_name) > 0

    # NOTE (mb 2020-07-28): provoke error
    main._HG_USERNAME_CMD = "exit 1"

    author_name = main.get_author_name()
    assert len(author_name) > 0


@pytest.fixture()
def ignore_file():
    ignore_file = FIXTURES_DIR / "pylint-ignore.md"
    stat_before = ignore_file.stat()

    backup_file = FIXTURES_DIR / "pylint-ignore.md.backup"
    shutil.copyfile(str(ignore_file), str(backup_file))
    yield ignore_file

    if stat_before != ignore_file.stat():
        shutil.copyfile(str(backup_file), str(ignore_file))
    backup_file.unlink()


# NOTE (mb 2020-08-09): We skip the assertions on python 2.7
#   because the output differs for older versions of the library
#   We still run the code itself as a smoketest though
HAS_INVALID_OUTPUT_FOR_FIXTURE = sys.version < "3.7"


def test_selftest_no_ignore_update(ignore_file, capsys):
    os.chdir(str(PROJECT_DIR))

    stat_before = ignore_file.stat()

    args = [
        "--rcfile=setup.cfg",
        "--score=no",
        "fixtures/",
        "--ignorefile",
        "fixtures/pylint-ignore.md",
    ]
    exitcode = main.main(args)

    if HAS_INVALID_OUTPUT_FOR_FIXTURE:
        return

    captured = capsys.readouterr()

    if captured.out or captured.out:
        print()
        print("out:", repr(captured.out))
        print("err:", repr(captured.err))

    assert exitcode == 0

    stat_after = ignore_file.stat()
    assert stat_before.st_mtime == stat_after.st_mtime

    assert captured.out == ""
    assert captured.err == ""


def test_selftest_ignore_update_noop(ignore_file, capsys):
    os.chdir(str(PROJECT_DIR))

    stat_before = ignore_file.stat()

    args = [
        "--rcfile=setup.cfg",
        "--score=no",
        "fixtures/",
        "--ignorefile=fixtures/pylint-ignore.md",
        "--update-ignorefile",
    ]
    exitcode = main.main(args)

    if HAS_INVALID_OUTPUT_FOR_FIXTURE:
        return

    assert exitcode == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    stat_after = ignore_file.stat()
    assert stat_before.st_mtime == stat_after.st_mtime


# TODO (mb 2020-08-09): At least pretend to be on windows and check
#   the not IS_FORK_METHOD_AVAILABLE codepaths
