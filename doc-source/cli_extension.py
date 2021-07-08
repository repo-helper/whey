#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#  Based on https://github.com/click-contrib/sphinx-click
#  Copyright (c) 2017 Stephen Finucane http://that.guru/
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

# stdlib
from typing import Optional

# 3rd party
import click
import sphinx_click
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import ViewList
from sphinx.application import Sphinx
from sphinx.writers.latex import LaTeXTranslator

_columnbreak = [
		'',
		".. raw:: latex",
		'',
		r"    \columnbreak",
		'',
		]


def _format_command(ctx: click.Context, nested: sphinx_click.NestedOption, commands=None):
	"""
	Format the output of :class:`click.Command`.
	"""

	if ctx.command.hidden:
		return

	# description
	yield from sphinx_click._format_description(ctx)

	yield f".. program:: {ctx.command_path}"

	# usage
	yield from sphinx_click._format_usage(ctx)

	yield ''
	yield ".. raw:: latex"
	yield ''
	yield r"    \begin{multicols}{2}"
	yield ''

	# options
	lines = list(sphinx_click._format_options(ctx))
	if lines:
		# we use rubric to provide some separation without exploding the table of contents
		yield ".. rubric:: Options"
		yield ''

	yield from lines

	# arguments
	lines = list(sphinx_click._format_arguments(ctx))

	if lines:
		yield from _columnbreak
		yield ".. rubric:: Arguments"
		yield ''
		yield from lines

	# environment variables
	lines = list(sphinx_click._format_envvars(ctx))

	if lines:
		yield from _columnbreak
		yield ".. rubric:: Environment variables"
		yield ''
		yield from lines

	yield ''
	yield ".. raw:: latex"
	yield ''
	yield r"    \end{multicols}"
	yield ''

	# description
	yield from sphinx_click._format_epilog(ctx)

	# if we're nesting commands, we need to do this slightly differently
	if nested in (sphinx_click.NestedOption.NESTED_FULL, sphinx_click.NestedOption.NESTED_NONE):
		return

	commands = sphinx_click._filter_commands(ctx, commands)

	if commands:
		yield ".. rubric:: Commands"
		yield ''

	for command in commands:
		# Don't show hidden subcommands
		if not command.hidden:
			yield from sphinx_click._format_subcommand(command)
			yield ''


class ClickDirective(sphinx_click.ClickDirective):
	"""
	Sphinx directive for documenting Click commands.
	"""

	has_content = False
	required_arguments = 1
	option_spec = {
			"prog": directives.unchanged_required,
			"nested": sphinx_click.nested_option,
			"commands": directives.unchanged,
			"show-nested": directives.flag,
			}

	def _generate_nodes(
			self,
			name: str,
			command: click.Command,
			parent: Optional[click.Context],
			nested: sphinx_click.NestedOption,
			commands=None,
			):
		"""
		Generate the relevant Sphinx nodes.

		Format a :class:`click.Group` or :class:`click.Command`.

		:param name: Name of command, as used on the command line
		:param command: Instance of `click.Group` or `click.Command`
		:param parent: Instance of `click.Context`, or None
		:param nested: The granularity of subcommand details.
		:param commands: Display only listed commands or skip the section if empty

		:returns: A list of nested docutils nodes
		"""

		if command.hidden:
			return []

		targetid = f"click-{self.env.new_serialno('click'):d}"
		targetnode = nodes.target('', '', ids=[targetid])

		# Summary
		ctx = click.Context(command, info_name=name, parent=parent)
		content = list(_format_command(ctx, nested, commands))

		view = ViewList(content)
		click_node = nodes.paragraph(rawsource='\n'.join(content))
		self.state.nested_parse(view, self.content_offset, click_node)

		sphinx_click.click_purger.add_node(self.env, click_node, targetnode, self.lineno)

		return [targetnode, click_node]


def setup(app: Sphinx) -> None:
	"""
	Setup Sphinx extension.
	"""

	app.add_directive("click", ClickDirective)
	app.connect("env-purge-doc", sphinx_click.click_purger.purge_nodes)
	app.connect("env-get-outdated", sphinx_click.env_get_outdated)
	app.add_directive("cli-option", sphinx_click.Cmdoption)
	app.add_node(
			sphinx_click.OptionDesc,
			latex=(LaTeXTranslator.visit_desc, LaTeXTranslator.depart_desc),
			override=True
			)
