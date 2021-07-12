#!/usr/bin/env python
# This file is managed by 'repo_helper'. Don't edit it directly.

# stdlib
import pathlib
import shutil
import sys

# 3rd party
from setuptools import setup

sys.path.append('.')

# this package
from __pkginfo__ import *  # pylint: disable=wildcard-import

repo_root = pathlib.Path(__file__).parent
install_requires = (repo_root / "requirements.txt").read_text(encoding="UTF-8").split('\n')

setup(
		description="A simple Python wheel builder for simple projects.",
		extras_require=extras_require,
		install_requires=install_requires,
		name="whey",
		py_modules=[],
		)

shutil.rmtree("whey.egg-info", ignore_errors=True)
