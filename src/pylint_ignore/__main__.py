#!/usr/bin/env python
# This file is part of the pylint-ignore project
# https://gitlab.com/mbarkhau/pylint-ignore
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import click
import pylint_ignore


# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == "1":
    try:
        import backtrace
        backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)
    except ImportError:
        # don't fail just because of missing dev library
        pass


click.disable_unicode_literals_warning = True


@click.group()
def cli() -> None:
    """pylint_ignore cli."""


@cli.command()
@click.version_option(version="2020.1001-alpha")
def version() -> None:
    """Show version number."""
    print(f"pylint_ignore version: {pylint_ignore.__version__}")
