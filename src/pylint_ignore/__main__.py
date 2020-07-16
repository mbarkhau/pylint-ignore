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
import shutil
import typing as typ
import logging
import getpass
import pathlib as pl
import datetime as dt
import subprocess as sp

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

MaybeLineNo = typ.Optional[int]


CONTEXT_LINES = 2


class SourceText(typ.NamedTuple):

    lineno      : int
    text        : str
    start_idx   : int
    end_idx     : int
    def_line_idx: typ.Optional[int]
    def_line    : typ.Optional[str]


class CatalogKey(typ.NamedTuple):
    """Stable (relatively) key to reference CatalogEntry values.

    The catalog key is relatively stable, even between edits
    to a file. In particular, it doesn't have the lineno.
    """

    msg_id      : str
    path        : str
    symbol      : str
    msg_text    : str
    ctx_src_text: str


class CatalogEntry(typ.NamedTuple):

    msg_id  : str
    path    : str
    symbol  : str
    msg_text: str

    author: str
    date  : str

    srctxt: typ.Optional[SourceText]


Catalog = typ.Dict[CatalogKey, CatalogEntry]


_SRC_CACHE: typ.Dict[str, typ.List[str]] = {}


def _read_source_lines(path: str) -> typ.List[str]:
    if path not in _SRC_CACHE:
        if len(_SRC_CACHE) > 2:
            _SRC_CACHE.popitem()

        with pl.Path(path).open(mode="r", encoding="utf-8") as fobj:
            full_src_text = fobj.read()

        lines = full_src_text.splitlines(keepends=True)
        _SRC_CACHE[path] = lines

    return _SRC_CACHE[path]


def read_context_source_text(path: str, lineno: int) -> SourceText:
    lines = _read_source_lines(path)
    line_idx        = lineno - 1  # lineno starts at 1
    line_indent_lvl = len(lines[line_idx]) - len(lines[line_idx].lstrip())

    start_idx = max(0, line_idx - CONTEXT_LINES)
    end_idx   = min(len(lines), line_idx + CONTEXT_LINES + 1)
    src_lines = lines[start_idx:end_idx]
    src_text  = "".join(src_lines)

    def_line_idx: typ.Optional[int] = None
    def_line    : typ.Optional[str] = None

    maybe_def_idx = line_idx

    while maybe_def_idx > 0:
        line_text  = lines[maybe_def_idx]
        indent_lvl = len(line_text) - len(line_text.lstrip())
        if line_text.strip() and indent_lvl < line_indent_lvl:
            first_token = line_text.lstrip().split()[0]
            if first_token in ('def', 'class'):
                is_defline_before_ctx_src = 0 <= maybe_def_idx < start_idx
                if is_defline_before_ctx_src:
                    def_line_idx = maybe_def_idx
                    def_line     = lines[maybe_def_idx]
                break

        maybe_def_idx -= 1

    return SourceText(lineno, src_text, start_idx, end_idx, def_line_idx, def_line)


CATALOG_HEADER = """# Catalog file for `pylint-ignore`

This file is parsed by `pylint-ignore` to determine which `pylint` messages are ignored.

The reccomended approach to using `pylint-ignore` is:

- If a message is valid, update your code rather than ignoring the message.
- If a message should always be ignored, to do so via the usual
  `pylintrc` file or `setup.cfg` file rather than this `pylint-ignore.md`
  file.
- If a message should be ignored, write a short comment why it is ok.
- If a message should not be ignored, remove the section.


"""


ENTRY_TEMPLATE = """
### Line {entry.srctxt.lineno} - {entry.msg_id} ({entry.symbol})

- message: {entry.msg_text}
- author : {entry.author}
- date   : {entry.date}

```json
{ctx_src_text}
```


"""

_FILE_HEADER_PATTERN = r"""
^
    \#\#\s
    File:\s(?P<path>.+)
$
"""

FILE_HEADER_RE = re.compile(_FILE_HEADER_PATTERN, flags=re.VERBOSE)


# https://regex101.com/r/ogknXY/2
_ENTRY_HEADER_PATTERN = r"""
^
    \#\#\#\s
    Line\s(?P<lineno>\d+)
    \s-\s
    (?P<msg_id>\w\d+)
    \s
    \((?P<symbol>.*)\)
$
"""

ENTRY_HEADER_RE = re.compile(_ENTRY_HEADER_PATTERN, flags=re.VERBOSE)


# https://regex101.com/r/6JViif/1
_LIST_ITEM_PATTERN = r"""
^
-\s(?P<key>message|author|date)
\s*:\s
(?P<value>.*)
$
"""

LIST_ITEM_RE = re.compile(_LIST_ITEM_PATTERN, flags=re.VERBOSE)


# https://regex101.com/r/Cc8w4v/4
_SOURCE_TEXT_PATTERN = r"""
(```|~~~)(?P<language>\w+)?
    (
        (?:\s+\d+:\s(?P<defline>.*))?
        \s+\.\.\.
    )?
    (?:\s+\d+:\s.*)?
    (?:\s+\d+:\s(?P<line0>.*))?
    \s*\>\s\d+:\s(?P<line1>.*)
    (?:\s+\d+:\s(?P<line2>.*))?
    (?:\s+\d+:\s.*)?
    \s*
(```|~~~)
"""

SOURCE_TEXT_RE = re.compile(_SOURCE_TEXT_PATTERN, flags=re.VERBOSE)


EntryValues = typ.Dict[str, str]


def _parse_entry(entry_vals: EntryValues) -> typ.Tuple[CatalogKey, CatalogEntry]:
    ctx_src_text = entry_vals['ctx_src_text']
    src_text_match = SOURCE_TEXT_RE.match(ctx_src_text)
    if src_text_match is None:
        raise ValueError("Invalid source text")

    src_text_lines = [
        src_text_match.group(groupname)
        for groupname in ['line0', 'line1', 'line2']
        if src_text_match.group(groupname)
    ]
    src_text = "\n".join(src_text_lines)

    # NOTE (mb 2020-07-16): The file may have changed in the meantime,
    #    so we search for the original source text (which may be on a
    #    different line).
    path   = entry_vals['path']
    lineno = int(entry_vals['lineno'])

    srctxt = read_context_source_text(path, lineno)

    catalog_entry = CatalogEntry(
        entry_vals['msg_id'],
        path,
        entry_vals['symbol'],
        entry_vals['message'],
        entry_vals['author'],
        entry_vals['date'],
        srctxt,
    )
    catalog_key   = CatalogKey(
        catalog_entry.msg_id,
        catalog_entry.path,
        catalog_entry.symbol,
        catalog_entry.msg_text,
        catalog_entry.srctxt.text,
    )
    return (catalog_key, catalog_entry)


def _dumps_entry(entry: CatalogEntry) -> str:
    last_ctx_lineno = entry.srctxt.end_idx + 1
    padding_size    = len(str(last_ctx_lineno))

    src_lines: typ.List[str] = []

    if entry.srctxt and entry.srctxt.def_line:
        def_lineno = entry.srctxt.def_line_idx + 1
        line       = entry.srctxt.def_line.rstrip()
        src_lines.append(f"  {def_lineno:>{padding_size}}: {line}")
        if def_lineno + CONTEXT_LINES < entry.srctxt.lineno:
            src_lines.append("  ...")

    for offset, line in enumerate(entry.srctxt.text.splitlines()):
        src_lineno = entry.srctxt.start_idx + offset + 1
        if entry.srctxt.lineno == src_lineno:
            dumps_line = f"> {src_lineno:>{padding_size}}: {line}"
        else:
            dumps_line = f"  {src_lineno:>{padding_size}}: {line}"
        src_lines.append(dumps_line)
    ctx_src_text = "\n".join(src_lines)
    entry_text   = ENTRY_TEMPLATE.format(entry=entry, ctx_src_text=ctx_src_text)
    return entry_text.lstrip("\n")


IsEnabledCallback = typ.Callable[
    [str, str, str, str, str, int, int, int], bool,
]


def _run(cmd: str) -> str:
    cmd_parts = cmd.split()
    try:
        output = sp.check_output(cmd_parts)
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


def _monkey_patch_pylint(is_enabled_cb: IsEnabledCallback) -> None:
    # NOTE (mb 2020-06-29): This is the easiest place to hook into that I've
    #   found. Though I'm not quite sure why msg_descr that is a code would
    #   imply that it's a candidate to generate output and otherwise not.
    from pylint.message.message_handler_mix_in import MessagesHandlerMixIn

    orig_is_message_enabled = MessagesHandlerMixIn.is_message_enabled
    orig_add_message        = MessagesHandlerMixIn.add_message

    cur_msg_args: typ.List[typ.Any] = []

    def add_message(
        self,
        msgid     : str,
        line      : MaybeLineNo = None,
        node      : typ.Any     = None,
        args      : typ.Optional[typ.Tuple[typ.Any]] = None,
        confidence: typ.Optional[str] = None,
        col_offset: typ.Optional[int] = None,
    ) -> None:
        del cur_msg_args[:]
        if isinstance(args, tuple):
            cur_msg_args.extend(args)
        elif isinstance(args, (bytes, str)):
            cur_msg_args.append(args)
        orig_add_message(self, msgid, line, node, args, confidence, col_offset)

    def is_message_enabled(
        self, msg_descr: str, line: MaybeLineNo = None, confidence: typ.Any = None,
    ) -> bool:
        is_enabled = orig_is_message_enabled(self, msg_descr, line, confidence)
        if not is_enabled:
            return False

        if re.match(r"\w\d{1,5}", msg_descr) is None:
            return True

        if self.current_file is None:
            return True

        _is_enabled = True

        msgid = msg_descr

        ctx_src: typ.Optional[SourceText]

        for msg_def in self.msgs_store.get_message_definitions(msgid):
            if line is None:
                ctx_src = None
            else:
                ctx_src = read_context_source_text(self.current_file, line)

            if len(cur_msg_args) >= msg_def.msg.count("%"):
                msg_text = msg_def.msg % tuple(cur_msg_args)
            else:
                msg_text = msg_def.msg

            _is_enabled = _is_enabled and is_enabled_cb(
                msgid, self.current_file, msg_def.symbol, msg_text, line or -1, ctx_src,
            )

        del cur_msg_args[:]

        return _is_enabled

    MessagesHandlerMixIn.is_message_enabled = is_message_enabled
    MessagesHandlerMixIn.add_message        = add_message


DEFAULT_CATALOG_PATH = (pl.Path(".") / "pylint-ignore.md").absolute()


def _iter_entry_values(catalog_path: pl.Path) -> typ.Iterable[EntryValues]:
    entry_vals: EntryValues = {}

    with catalog_path.open(mode="r", encoding="utf-8") as fobj:
        lines = iter(enumerate(fobj))
        try:
            while True:
                i, line = next(lines)
                if line.startswith("```"):
                    open_fence = line[:3]
                    ctx_src_text_lines = [line]
                    while True:
                        # consume lines to next fence
                        _, next_line = next(lines)
                        ctx_src_text_lines.append(next_line)
                        is_close_fence = next_line.strip() == open_fence
                        if is_close_fence:
                            break

                    entry_vals['ctx_src_text'] = "".join(ctx_src_text_lines)
                    continue

                catalog_lineno = i + 1
                file_header    = FILE_HEADER_RE.match(line)
                entry_header   = ENTRY_HEADER_RE.match(line)
                if (file_header or entry_header) and 'msg_id' in entry_vals:
                    # new header -> any existing entry is done
                    yield entry_vals

                    # Reuse path from previous entry (will be replaced if a new file
                    # header is encountered)
                    entry_vals = {'path': entry_vals['path']}

                if file_header:
                    rel_path = file_header.group('path')
                    abspath = (catalog_path.parent / rel_path).absolute()
                    entry_vals = {'path': str(abspath)}
                    continue

                if entry_header:
                    entry_vals['catalog_lineno'] = catalog_lineno
                    entry_vals.update(entry_header.groupdict())
                    assert 'msg_id' in entry_vals
                    continue

                list_item = LIST_ITEM_RE.match(line)
                if list_item:
                    entry_vals[list_item.group('key')] = list_item.group('value')
        except StopIteration:
            pass

    # yield last entry (not followed by a header that would otherwise trigger the yield)
    if 'msg_id' in entry_vals:
        yield entry_vals


def _load_catalog(catalog_path: pl.Path = DEFAULT_CATALOG_PATH) -> Catalog:
    if not catalog_path.exists():
        return {}

    catalog: Catalog = {}
    for entry_vals in _iter_entry_values(catalog_path):
        try:
            catalog_key, catalog_entry = _parse_entry(entry_vals)
            catalog[catalog_key] = catalog_entry
        except (KeyError, ValueError):
            lineno = entry_vals['catalog_lineno']
            path = entry_vals['path']
            logmsg = f"Error parsing entry on line {lineno} of {path}"
            logger.error(logmsg, exc_info=True)

    return catalog


def _dumps_catalog(catalog: Catalog) -> str:
    # catalog_entries.sort(key=lambda e: (e['path'], e['lineno'], e['msg_id']))
    # catalog_data    = catalog.dumps(catalog_entries, indent=4)
    seen_paths: typ.Set[str] = set()
    catalog_chunks = [CATALOG_HEADER]
    entries        = list(catalog.values())
    entries.sort(key=lambda e: (e.path, e.srctxt and e.srctxt.lineno))
    pwd = pl.Path(".").absolute()

    for entry in entries:
        if entry.path not in seen_paths:
            rel_path = pl.Path(entry.path).absolute().relative_to(pwd)
            catalog_chunks.append(f"## File: {rel_path}\n\n")
            seen_paths.add(entry.path)

        catalog_chunks.append(_dumps_entry(entry))

    return "".join(catalog_chunks)


def _dump_catalog(catalog: Catalog, catalog_path: pl.Path = DEFAULT_CATALOG_PATH) -> None:
    catalog_text = _dumps_catalog(catalog)
    tmp_path     = catalog_path.parent / (catalog_path.name + ".tmp")
    with tmp_path.open(mode="w", encoding="utf-8") as fobj:
        fobj.write(catalog_text)
    shutil.move(str(tmp_path), str(catalog_path))


def main() -> ExitCode:
    # TODO (mb 2020-07-05): test that everything works if we crank up the jobs/concurrency
    # TODO (mb 2020-07-05): options
    #
    # --non-interactive   # Check with existing catalog. Fail for any new entries.
    # --ignore-all        # add entries to .pylint-ignore for all
    #                     #   all messages
    # --ignore-clean      # clean messages fom .pylint-ignore for
    #                     #   which no message is reported anymore.
    #                     #   update line numbers of existing entries.

    args = sys.argv[1:]

    # if "--non-interactive" in args:
    #     args.remove("--non-interactive")
    #     is_interactive_mode = False
    # elif not sys.stdout.isatty():
    #     is_interactive_mode = False
    # else:
    #     is_interactive_mode = True

    old_ignore_catalog: Catalog = _load_catalog()
    new_ignore_catalog: Catalog = {}

    default_author = get_author_name()
    default_date   = dt.datetime.now().isoformat().split(".")[0]

    def is_enabled_entry(
        msg_id  : str,
        path    : str,
        symbol  : str,
        msg_text: str,
        lineno  : int,
        src_txt : typ.Optional[SourceText],
    ) -> bool:
        """Return false if message is in the serialized catalog.

        Side effect: Track new entries for serialization.
        """

        ctx_src_text = src_txt.text if src_txt else ""
        catalog_key  = CatalogKey(msg_id, path, symbol, msg_text, ctx_src_text)
        old_entry    = old_ignore_catalog.get(catalog_key)
        if old_entry:
            # NOTE (mb 2020-07-02): We don't use the lineno from
            #       the old_entry because it may have changed.
            author = old_entry.author
            date   = old_entry.date
        else:
            author = default_author
            date   = default_date

        new_entry = CatalogEntry(msg_id, path, symbol, msg_text, author, date, src_txt,)
        new_ignore_catalog[catalog_key] = new_entry

        if old_entry and old_entry == new_entry:
            return False

        return True

    _monkey_patch_pylint(is_enabled_cb=is_enabled_entry)

    exit_code = 0
    try:
        # We don't want to load this code before the monkey patching is done.
        import pylint.lint

        pylint.lint.Run(args)
    except SystemExit as sysexit:
        exit_code = sysexit.code
    except KeyboardInterrupt:
        return 1

    _dump_catalog(new_ignore_catalog)
    # if old_ignore_catalog != new_ignore_catalog:
    #     _dump_catalog(new_ignore_catalog)
    #
    # assert _load_catalog() == new_ignore_catalog

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
