#!/usr/bin/env python
# This file is part of the pylint-ignore project
# https://github.com/mbarkhau/pylint-ignore
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
"""CLI for pylint-ignore.

This module wraps the pylint runner and supresses individual
messages if configured via a pylint-ignore.md file.
"""

import os
import re
import sys
import shutil
import typing as typ
import getpass
import hashlib
import logging
import datetime as dt
import tempfile
import functools as ft
import subprocess as sp
import multiprocessing as mp

import pathlib2 as pl
import pylint.lint

from . import ignorefile

try:
    import pretty_traceback

    pretty_traceback.install(envvar='ENABLE_PRETTY_TRACEBACK')
except ImportError:
    pass  # no need to fail because of missing dev dependency


try:
    from pylint.message.message_handler_mix_in import MessagesHandlerMixIn
except ImportError:
    # pylint<2.4>=2.0
    from pylint.utils import MessagesHandlerMixIn


class MessageDef(typ.NamedTuple):

    msg   : str
    msgid : str
    symbol: str
    scope : str
    descr : str

    old_names: typ.List[str]


TESTDEBUG = False


def _pylint_msg_defs(linter, msgid: str) -> typ.List[MessageDef]:
    if hasattr(linter.msgs_store, 'get_message_definitions'):
        msg_defs = linter.msgs_store.get_message_definitions(msgid)
        if TESTDEBUG:
            assert isinstance(msg_defs, list)
            assert all(hasattr(m, 'msg'   ) for m in msg_defs)
            assert all(hasattr(m, 'symbol') for m in msg_defs)
        return typ.cast(typ.List[MessageDef], msg_defs)
    elif hasattr(linter.msgs_store, 'get_message_definition'):
        # compat for older pylint versions
        return [linter.msgs_store.get_message_definition(msgid)]
    else:
        # compat for even older pylint versions
        return [linter.msgs_store.check_message_id(msgid)]


logger = logging.getLogger('pylint_ignore')

ExitCode = int

USAGE_ERROR = 32

MaybeLineNo = typ.Optional[int]


DEFAULT_IGNOREFILE_PATH = pl.Path(".") / "pylint-ignore.md"


def _run(cmd: str) -> str:
    cmd_parts = cmd.split()
    try:
        output = sp.check_output(cmd_parts)
    except OSError:
        return ""
    except sp.CalledProcessError:
        return ""

    return output.strip().decode("utf-8")


_HG_USERNAME_CMD = "hg config ui.username"


def get_author_name() -> str:
    """Do a best effort to get a meaningful author name."""
    hg_username = _run(_HG_USERNAME_CMD)
    git_email   = _run("git config user.email")
    git_name    = _run("git config user.name")

    if git_email and "<" in git_email and ">" in git_email:
        git_username = git_email
    elif git_name and git_email:
        git_username = git_name + " <" + git_email + ">"
    elif git_name:
        git_username = git_name
    elif git_email:
        git_username = git_email
    else:
        git_username = ""

    is_hg_repo  = pl.Path(".hg" ).exists()
    is_git_repo = pl.Path(".git").exists()

    # prefer name associated with the type of the repo
    if is_hg_repo and hg_username:
        return hg_username
    if is_git_repo and git_username:
        return git_username

    # fallback to global config
    if hg_username:
        return hg_username
    if git_username:
        return git_username

    return getpass.getuser()


IS_FORK_METHOD_AVAILABLE = sys.platform != 'win32'


class PylintIgnoreDecorator:
    # NOTE (mb 2020-07-17): The term "Decorator" refers to the gang of four
    #   pattern, rather than the typical usage in python which is about function
    #   decorators.
    # NOTE (mb 2020-07-18): atm. I think splitting this up would only make
    #   things more complicated.
    # pylint:disable=too-many-instance-attributes

    ignorefile_path: pl.Path
    is_update_mode : bool
    pylint_run_args: typ.List[str]

    default_author: str
    default_date  : str

    old_catalog: ignorefile.Catalog
    # New catalog entries are first written to a temporary
    # directory, which allows us to support the --jobs argument.
    new_catalog_dir: pl.Path

    # the original/non-monkey-patched methods of the linter
    _pylint_is_message_enabled: typ.Any
    _pylint_add_message       : typ.Any

    # This is pylint internal state that we capture in add_message
    # and later use in is_message_enabled
    _last_added_msgid: typ.Optional[str]
    _cur_msg_args    : typ.List[typ.Any]

    def __init__(self, args: typ.Sequence[str]) -> None:
        self.ignorefile_path = DEFAULT_IGNOREFILE_PATH
        self.is_update_mode  = False
        self.pylint_run_args = []
        self._init_from_args(args)

        self.old_catalog = ignorefile.load(self.ignorefile_path)
        if self.is_update_mode:
            self.new_catalog_dir = pl.Path(tempfile.mkdtemp())
        else:
            self.new_catalog_dir = pl.Path(tempfile.gettempdir())

        self.default_author = get_author_name()
        self.default_date   = dt.datetime.now().isoformat().split(".")[0]

        self._last_added_msgid = None
        self._cur_msg_args: typ.List[typ.Any] = []

    def _init_from_args(self, args: typ.Sequence[str]) -> None:
        arg_i = 0
        while arg_i < len(args):
            arg = args[arg_i]
            if arg == '--update-ignorefile':
                self.is_update_mode = True
            elif arg == '--ignorefile':
                self.ignorefile_path = pl.Path(args[arg_i + 1])
                arg_i += 1
            elif arg.startswith("--ignorefile="):
                self.ignorefile_path = pl.Path(arg.split("=", 1)[-1])
            else:
                is_jobs_arg = arg.startswith("--jobs") or arg.startswith("-j")
                if is_jobs_arg and not IS_FORK_METHOD_AVAILABLE:
                    # ommit --jobs=1 on windows
                    if "=" not in arg:
                        # also skip next arg
                        arg_i += 1
                else:
                    self.pylint_run_args.append(arg)

            arg_i += 1

        # NOTE (mb 2020-08-09): Override any other config that pylint might use,
        #   we inject an explicit --jobs=1 argument. This only affects windows,
        #   which doesn't support 'fork'
        if not IS_FORK_METHOD_AVAILABLE:
            self.pylint_run_args.insert(0, "--jobs=1")

        if not self.ignorefile_path.exists() and not self.is_update_mode:
            sys.stderr.write(f"Invalid path, does not exist: {self.ignorefile_path}\n")
            raise SystemExit(USAGE_ERROR)

    def _new_entry(
        self,
        key      : ignorefile.Key,
        old_entry: typ.Optional[ignorefile.Entry],
        msg_text : str,
        msg_extra: str,
        srctxt   : ignorefile.MaybeSourceText,
    ) -> ignorefile.Entry:
        if old_entry:
            # NOTE (mb 2020-07-02): We don't use the lineno from
            #       the old_entry because it may have changed.
            author = old_entry.author
            date   = old_entry.date
        else:
            author = self.default_author
            date   = self.default_date

        return ignorefile.Entry(
            key.msgid, key.path, key.symbol, msg_text, msg_extra, author, date, srctxt
        )

    def _dump_entry(self, entry: ignorefile.Entry) -> None:
        if not self.is_update_mode:
            return

        entry_text = ignorefile.dumps_entry(entry)

        catalog_file = self.new_catalog_dir / f"{os.getpid()}.md"
        with catalog_file.open(mode="a", encoding="utf-8") as fobj:
            fobj.write(entry_text)

    def cleanup(self) -> None:
        assert self.new_catalog_dir != pl.Path(tempfile.gettempdir())
        shutil.rmtree(str(self.new_catalog_dir))

    def is_enabled_entry(
        self,
        msgid    : str,
        path     : str,
        symbol   : str,
        msg_text : str,
        msg_extra: str,
        srctxt   : ignorefile.MaybeSourceText,
    ) -> bool:
        """Return false if message is in the serialized catalog.

        Side effect: Track new entries for serialization.
        """

        pwd      = pl.Path(".").absolute()
        rel_path = str(pl.Path(path).absolute().relative_to(pwd))
        if srctxt:
            source_line = srctxt.source_line
        else:
            source_line = hashlib.sha1(msg_extra.strip().encode("utf-8")).hexdigest()

        key       = ignorefile.Key(msgid, rel_path, symbol, msg_text, source_line)
        old_entry = ignorefile.find_entry(self.old_catalog, key)
        new_entry = self._new_entry(key, old_entry, msg_text, msg_extra, srctxt)
        self._dump_entry(new_entry)
        is_ignored = old_entry is not None or self.is_update_mode
        return not is_ignored

    def _fmt_msg(self, msg_def: MessageDef) -> typ.Tuple[str, str]:
        if len(self._cur_msg_args) >= msg_def.msg.count("%"):
            msg_text = msg_def.msg % tuple(self._cur_msg_args)
        else:
            msg_text = msg_def.msg

        if "\n" in msg_text:
            msg_text_parts = msg_text.split("\n", 1)
            msg_text       = msg_text_parts[0]
            msg_extra      = msg_text_parts[1].strip()
        else:
            msg_extra = ""
        return msg_text, msg_extra

    def _add_message_wrapper(self) -> typ.Callable:
        @ft.wraps(self._pylint_add_message)
        def add_message(
            linter,
            msgid     : str,
            line      : MaybeLineNo = None,
            node      : typ.Any     = None,
            args      : typ.Union[typ.Tuple[typ.Any], str, bytes, None] = None,
            confidence: typ.Optional[str] = None,
            col_offset: typ.Optional[int] = None,
        ) -> None:
            self._last_added_msgid = msgid
            del self._cur_msg_args[:]

            if isinstance(args, tuple):
                self._cur_msg_args.extend(args)
            elif isinstance(args, (bytes, str)):
                self._cur_msg_args.append(args)
            if col_offset is None:
                self._pylint_add_message(linter, msgid, line, node, args, confidence)
            else:
                # compat for pylint 1.9.5
                self._pylint_add_message(linter, msgid, line, node, args, confidence, col_offset)

        return add_message

    def _is_message_enabled_wrapper(self) -> typ.Callable:
        def is_any_message_def_enabled(linter, msgid: str, line: MaybeLineNo) -> bool:
            srctxt = ignorefile.read_source_text(linter.current_file, line, line) if line else None
            for msg_def in _pylint_msg_defs(linter, msgid):
                msg_text, msg_extra = self._fmt_msg(msg_def)

                assert not (msg_extra and srctxt)

                _is_enabled = self.is_enabled_entry(
                    msgid, linter.current_file, msg_def.symbol, msg_text, msg_extra, srctxt
                )
                if not _is_enabled:
                    return False

            return True

        @ft.wraps(self._pylint_is_message_enabled)
        def is_message_enabled(
            linter,
            msg_descr : str,
            line      : MaybeLineNo = None,
            confidence: typ.Any     = None,
        ) -> bool:
            try:
                is_enabled = self._pylint_is_message_enabled(linter, msg_descr, line, confidence)
                # NOTE (mb 2020-07-24): is_message_enabled is called in two modes
                #   1. during initilization, to check if a message type is enabled in general
                #   2. during linting, to check if a particular message is enabled
                last_msgid = self._last_added_msgid
                if last_msgid is None:
                    # called during initialization
                    return bool(is_enabled)

                if not is_enabled:
                    return False

                is_always_enabled = re.match(r"\w\d{1,5}", msg_descr) is None
                if is_always_enabled:
                    return True

                return is_any_message_def_enabled(linter, msg_descr, line)
            finally:
                # make sure we don't use args for the next message
                self._last_added_msgid = None
                del self._cur_msg_args[:]

        return is_message_enabled

    def monkey_patch_pylint(self) -> None:
        # NOTE (mb 2020-06-29): This is the easiest place to hook into that I've
        #   found. Though I'm not quite sure why msg_descr that is a code would
        #   imply that it's a candidate to generate output and otherwise not.
        self._pylint_is_message_enabled = MessagesHandlerMixIn.is_message_enabled
        self._pylint_add_message        = MessagesHandlerMixIn.add_message

        MessagesHandlerMixIn.is_message_enabled = self._is_message_enabled_wrapper()
        MessagesHandlerMixIn.add_message        = self._add_message_wrapper()

    def monkey_unpatch_pylint(self) -> None:
        if MessagesHandlerMixIn is None:
            # NOTE (mb 2020-09-26): This appears to happen when pylint is called
            #   with a non python module and with jobs>1
            return

        MessagesHandlerMixIn.is_message_enabled = self._pylint_is_message_enabled
        MessagesHandlerMixIn.add_message        = self._pylint_add_message


def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
    # pylint:disable=dangerous-default-value; We don't mutate args, mypy would fail if we did.

    is_fork_method_setable = (
        IS_FORK_METHOD_AVAILABLE
        and hasattr(mp, 'get_start_method')
        and mp.get_start_method(allow_none=True) is None
    )
    # Method 'fork' is the only thing that works for us,
    #   since we're monkey patching, we need the memory
    #   state to be preserved.
    if is_fork_method_setable:
        # NOTE (mb 2020-08-09): This is actually requred on MacOS,
        #   on Linux this appears to be the default anyway.
        #   https://bugs.python.org/issue33725
        mp.set_start_method('fork')

    exit_code = 1
    dec       = PylintIgnoreDecorator(args)
    try:
        dec.monkey_patch_pylint()
        try:
            pylint.lint.Run(dec.pylint_run_args)
            exit_code = 0
        except SystemExit as sysexit:
            exit_code = sysexit.code
        except KeyboardInterrupt:
            return 1
    finally:
        dec.monkey_unpatch_pylint()

    if dec.is_update_mode:
        try:
            new_catalog      = ignorefile.load_dir(dec.new_catalog_dir)
            is_catalog_dirty = dec.old_catalog != new_catalog
            if is_catalog_dirty:
                ignorefile.dump(new_catalog, dec.ignorefile_path)
        finally:
            dec.cleanup()

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
