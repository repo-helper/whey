#!/usr/bin/env python3
#
#  _traceback_handler.py
"""
Handles exceptions.
"""
#
#  Copyright © 2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#

# 3rd party
from consolekit.tracebacks import TracebackHandler
from consolekit.utils import abort
from dom_toml.parser import BadConfigError

__all__ = ["ConfigTracebackHandler"]


class ConfigTracebackHandler(TracebackHandler):
	"""
	:class:`consolekit.tracebacks.TracebackHandler` which handles :exc:`~.BadConfigError`.
	"""

	def handle_BadConfigError(self, e: "BadConfigError") -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)

	def handle_KeyError(self, e: KeyError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)

	def handle_TypeError(self, e: TypeError) -> bool:  # noqa: D102
		raise abort(f"{e.__class__.__name__}: {e}", colour=False)
