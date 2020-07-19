#!/usr/bin/env python
# This file is part of the pylint-ignore project
# https://gitlab.com/mbarkhau/pylint-ignore
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
import typing as typ
import getpass
import logging
import datetime as dt
import subprocess as sp

import pathlib2 as pl
import pylint.lint

from . import ignorefile

try:
    from pylint.message.message_handler_mix_in import MessagesHandlerMixIn
except ImportError:
    # pylint<2.4>=2.0
    from pylint.utils import MessagesHandlerMixIn


def _pylint_msg_defs(linter, msgid: str) -> typ.List:
    if hasattr(linter.msgs_store, 'get_message_definitions'):
        return linter.msgs_store.get_message_definitions(msgid)
    else:
        # compat for older pylint versions
        return [linter.msgs_store.get_message_definition(msgid)]


# To enable pretty tracebacks:
#   echo "export ENABLE_RICH_TB=1;" >> ~/.bashrc
if os.environ.get('ENABLE_RICH_TB') == '1':
    try:
        import rich.traceback

        rich.traceback.install()
    except ImportError:
        # don't fail just because of missing dev library
        pass


logger = logging.getLogger('pylint_ignore')

ExitCode = int

USAGE_ERROR = 32

MaybeLineNo = typ.Optional[int]


DEFAULT_IGNOREFILE_PATH = pl.Path(".") / "pylint-ignore.md"


def _run(cmd: str) -> str:
    cmd_parts = cmd.split()
    try:
        output = sp.check_output(cmd_parts)
    except FileNotFoundError:
        return ""
    except sp.SubprocessError:
        return ""

    return output.strip().decode("utf-8")


def get_author_name() -> str:
    """Do a best effort to get a meaningful author name."""
    hg_username = _run("hg config ui.username")
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
    new_catalog: ignorefile.Catalog

    # the original/non-monkey-patched methods of the linter
    _pylint_is_message_enabled: typ.Any
    _pylint_add_message       : typ.Any

    # This is pylint internal state that we capture in add_message
    # and later use in is_message_enabled
    _cur_msg_args: typ.List[typ.Any]

    def __init__(self, args: typ.Sequence[str]) -> None:
        self.ignorefile_path = DEFAULT_IGNOREFILE_PATH
        self.is_update_mode  = False
        self.pylint_run_args = []
        self._init_from_args(args)

        self.old_catalog: ignorefile.Catalog = ignorefile.load(self.ignorefile_path)
        self.new_catalog: ignorefile.Catalog = {}

        self.default_author = get_author_name()
        self.default_date   = dt.datetime.now().isoformat().split(".")[0]

        self._cur_msg_args: typ.List[typ.Any] = []

    def _init_from_args(self, args: typ.Sequence[str]) -> None:
        arg_i = 0
        while arg_i < len(args):
            arg = args[arg_i]
            if arg == '--update-ignorefile':
                self.is_update_mode = True
            elif arg == '--ignorefile':
                self.ignorefile_path = pl.Path(args[arg_i + 1])
            elif arg.startswith("--ignorefile="):
                self.ignorefile_path = pl.Path(arg.split("=", 1)[-1])
            elif arg.startswith("--jobs") or arg.startswith("-j"):
                # NOTE (mb 2020-07-17): Use of the --jobs parameter is prohibited
                #   because we capture and process the messages in the same
                #   proccess. There would need to be some kind of synchronisation to
                #   merge the catalogs of multiple processes if this were to work.

                if "=" in arg:
                    num_jobs = arg.split("=", 1)[-1]
                else:
                    num_jobs = args[arg_i + 1]

                if num_jobs != '1':
                    if "=" in arg:
                        sys.stderr.write(f"Invalid argument {arg}\n")
                    else:
                        sys.stderr.write(f"Invalid argument {arg} {num_jobs}\n")
                    sys.stderr.write("    pylint-ignore only works with --jobs=1\n")
                    raise SystemExit(USAGE_ERROR)
            else:
                self.pylint_run_args.append(arg)

            arg_i += 1

        if not self.ignorefile_path.exists() and not self.is_update_mode:
            sys.stderr.write(f"Invalid path, does not exist: {self.ignorefile_path}\n")
            raise SystemExit(USAGE_ERROR)

        # TODO (mb 2020-07-17): This will override any configuration, but it is not
        #   ideal. It would be better if we could use the same config parsing logic
        #   as pylint and raise an error if anything other than jobs=1 is configured
        #   there.
        self.pylint_run_args.insert(0, "--jobs=1")

    def _new_entry(
        self,
        key      : ignorefile.Key,
        old_entry: typ.Optional[ignorefile.Entry],
        msg_text : str,
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

        return ignorefile.Entry(key.msg_id, key.path, key.symbol, msg_text, author, date, srctxt,)

    def is_enabled_entry(
        self,
        msg_id  : str,
        path    : str,
        symbol  : str,
        msg_text: str,
        srctxt  : ignorefile.MaybeSourceText,
    ) -> bool:
        """Return false if message is in the serialized catalog.

        Side effect: Track new entries for serialization.
        """

        pwd         = pl.Path(".").absolute()
        rel_path    = str(pl.Path(path).absolute().relative_to(pwd))
        source_line = srctxt.source_line if srctxt else ""
        key         = ignorefile.Key(msg_id, rel_path, symbol, msg_text, source_line)
        old_entry   = ignorefile.find_entry(self.old_catalog, key)
        new_entry   = self._new_entry(key, old_entry, msg_text, srctxt)

        self.new_catalog[key] = new_entry
        is_ignored = old_entry is not None or self.is_update_mode
        return not is_ignored

    def _is_message_enabled_wrapper(self) -> typ.Callable:
        def is_any_message_def_enabled(linter, msgid: str, line: MaybeLineNo) -> bool:
            srctxt = ignorefile.read_source_text(linter.current_file, line, line) if line else None

            for msg_def in _pylint_msg_defs(linter, msgid):
                if len(self._cur_msg_args) >= msg_def.msg.count("%"):
                    msg_text = msg_def.msg % tuple(self._cur_msg_args)
                else:
                    msg_text = msg_def.msg

                _is_enabled = self.is_enabled_entry(
                    msgid, linter.current_file, msg_def.symbol, msg_text, srctxt,
                )
                if not _is_enabled:
                    return False

            return True

        def is_message_enabled(
            linter, msg_descr: str, line: MaybeLineNo = None, confidence: typ.Any = None,
        ) -> bool:
            is_enabled = self._pylint_is_message_enabled(linter, msg_descr, line, confidence)
            if not is_enabled:
                return False

            if re.match(r"\w\d{1,5}", msg_descr) is None:
                return True

            if linter.current_file is None:
                return True

            try:
                return is_any_message_def_enabled(linter, msg_descr, line)
            finally:
                del self._cur_msg_args[:]

        return is_message_enabled

    def _add_message_wrapper(self) -> typ.Callable:
        def add_message(
            linter,
            msgid     : str,
            line      : MaybeLineNo = None,
            node      : typ.Any     = None,
            args      : typ.Optional[typ.Tuple[typ.Any]] = None,
            confidence: typ.Optional[str] = None,
            col_offset: typ.Optional[int] = None,
        ) -> None:
            del self._cur_msg_args[:]
            if isinstance(args, tuple):
                self._cur_msg_args.extend(args)
            elif isinstance(args, (bytes, str)):
                self._cur_msg_args.append(args)
            self._pylint_add_message(linter, msgid, line, node, args, confidence, col_offset)

        return add_message

    def monkey_patch_pylint(self) -> None:
        # NOTE (mb 2020-06-29): This is the easiest place to hook into that I've
        #   found. Though I'm not quite sure why msg_descr that is a code would
        #   imply that it's a candidate to generate output and otherwise not.
        self._pylint_is_message_enabled = MessagesHandlerMixIn.is_message_enabled
        self._pylint_add_message        = MessagesHandlerMixIn.add_message

        MessagesHandlerMixIn.is_message_enabled = self._is_message_enabled_wrapper()
        MessagesHandlerMixIn.add_message        = self._add_message_wrapper()

    def monkey_unpatch_pylint(self) -> None:
        MessagesHandlerMixIn.is_message_enabled = self._pylint_is_message_enabled
        MessagesHandlerMixIn.add_message        = self._pylint_add_message


def main(args: typ.Sequence[str] = sys.argv[1:]) -> ExitCode:
    # NOTE (mb 2020-07-18): We don't mutate args, mypy would fail if we did.
    # pylint:disable=dangerous-default-value
    dec = PylintIgnoreDecorator(args)
    try:
        dec.monkey_patch_pylint()

        exit_code = 0
        try:
            pylint.lint.Run(dec.pylint_run_args)
        except SystemExit as sysexit:
            exit_code = sysexit.code
        except KeyboardInterrupt:
            return 1

        is_catalog_dirty = dec.old_catalog != dec.new_catalog
        if is_catalog_dirty and dec.is_update_mode:
            ignorefile.dump(dec.new_catalog, dec.ignorefile_path)
    finally:
        dec.monkey_unpatch_pylint()

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
