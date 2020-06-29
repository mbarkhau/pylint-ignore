#!/usr/bin/env python
# This file is part of the pylint-ignore project
# https://gitlab.com/mbarkhau/pylint-ignore
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import io
import re
import sys
import time
import typing as typ
import threading

from . import parsing


# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == "1":
    try:
        import backtrace
        backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)
    except ImportError:
        # don't fail just because of missing dev library
        pass


class MessageListner(threading.Thread):

    def __init__(self) -> None:
        threading.Thread.__init__(self)
        # daemon means the thread is killed if user hits Ctrl-C
        self.daemon = True
        self.done = False
        self.iters = 0
        self.visible_messages = 0

    def __enter__(self) -> 'MessageListner':
        self.faux_stdout = io.StringIO()
        # self.faux_stderr = io.StringIO()

        self.original_stdout = sys.stdout
        # self.original_stderr = sys.stderr

        sys.stdout = self.faux_stdout
        # sys.stderr = self.faux_stderr

        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.done = True
        self.join()

        self.faux_stdout.close()
        # self.faux_stderr.close()

        sys.stdout = self.original_stdout
        # sys.stderr = self.original_stderr

        if not isinstance(exc_value, SystemExit):
            return False    # propagate exception

        code = exc_value.code
        has_propagation_code = all([
            code > 0,
            code & USAGE_MSG == 0,
            code & FATAL_MSG == 0,
        ])
        if has_propagation_code:
            return False
        elif self.visible_messages > 0:
            return False
        else:
            # swallow exception (return 0 later)
            return True

    def _process_message(self, msg: parsing.Message) -> None:
        self.original_stdout.write(msg.text)

    def run(self) -> None:
        # NOTE (mb 2020-06-27): This is quite inefficient, in that
        #   there is much buffering and many copies. We can however
        #   switch to a streaming api because most of the actual
        #   logic is part of _process_message.
        prev_pos = 0
        msg_buffer = ""
        while not self.done:
            time.sleep(0.1)
            self.iters += 1
            new_pos = self.faux_stdout.tell()
            if new_pos > prev_pos:
                msg_buffer += self.faux_stdout.getvalue()[prev_pos:new_pos]
                prev_pos = new_pos

            while True:
                msg = parsing.next_message(msg_buffer)
                if msg is None:
                    break
                else:
                    msg_buffer = msg_buffer[len(msg.text):]
                    self._process_message(msg)


# http://pylint.pycqa.org/en/latest/user_guide/run.html#exit-codes
#
# exit code     meaning
# 0             no error
# 1             fatal message issued
# 2             error message issued
# 4             warning message issued
# 8             refactor message issued
# 16            convention message issued
# 32            usage error *
#
# * Internal error while receiving resultsfrom child linter
#   Error occurred, stopping the linter.
# * <return of linter.help()>
# * Jobs number <#> should be greater than 0

FATAL_MSG = 1
ERROR_MSG = 2
USAGE_MSG = 32


ExitCode = int


def old_main() -> ExitCode:
    """Pylint Ignore Entry Point.

    Wrapper around the pylint command, which hijacks stdout and stderr
    and does postprocessing on the output.
    """
    try:
        with MessageListner() as listner:
            import pylint.lint

            pylint.lint.Run(sys.argv[1:])
    except KeyboardInterrupt:
        return 1

    return 0


MaybeLineNo = typ.Optional[int]


def main() -> ExitCode:
    # NOTE (mb 2020-06-28): I've tried to correlate these method calls with
    #   the output, but there appears to be too much going on to easilly
    #   hook into. Invocations of these methods may or may not lead to a
    #   message ultimately being displayed, so they are not a good basis.
    #   At the end of the day, we only care about what we can actually
    #   see in the output, so the output is what we parse.
    from pylint.message.message_handler_mix_in import MessagesHandlerMixIn
    orig_is_message_enabled = MessagesHandlerMixIn.is_message_enabled

    # assert False, "find the place where the output is actually written to stdout stream"

    def is_message_enabled(self, msg_descr, line=None, confidence=None) -> bool:
        is_enabled = orig_is_message_enabled(self, msg_descr, line, confidence)
        if line is None or not is_enabled:
            return is_enabled

        if re.match(r"\w\d{1,4}", msg_descr) is None:
            return is_enabled

        print(f"    xxx {msg_descr:>5} {line:>5} {self.current_file}")
        return is_enabled

    MessagesHandlerMixIn.is_message_enabled = is_message_enabled

    try:
        import pylint.lint

        pylint.lint.Run(sys.argv[1:])
    except KeyboardInterrupt:
        return 1


if __name__ == '__main__':
    sys.exit(main())
