# 3rd party
import dom_toml
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from domdf_python_tools import stringlist
from domdf_python_tools.paths import PathPlus
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx_toolbox.utils import Purger

purger = Purger("all_comparison_nodes")


class ComparisonDirective(SphinxDirective):

	option_spec = {"widths": directives.unchanged_required}

	def run(self):
		config = dom_toml.load(PathPlus(self.env.srcdir) / "comparison.toml")

		table_source = stringlist.StringList()
		table_source.append(".. list-table:: Comparison of Tools")

		widths = self.options.get("widths", "15 10 10 10 10 15 10 12 12")

		with table_source.with_indent("    ", 1):
			table_source.extend([
					f":widths: {widths}",
					":header-rows: 1",
					":stub-columns: 1",
					'',
					"* - Tool",
					"  - :pep:`517` support",
					"  - :pep:`621` support",
					"  - ``src`` layout support",
					"  - Builds C Extensions",
					"  - Can Install Project",
					"  - Upload to PyPI",
					"  - First Release",
					"  - Python Versions",
					])

			for name, tool in config.items():
				if "link" in tool:
					table_source.append(f"* - `{name} <{tool['link']}>`_")
				else:
					table_source.append(f"* - {name}")

				for key in [
						"supports_517",
						"supports_621",
						"src_layout",
						"build_extensions",
						"install",
						"upload",
						]:

					value = tool.get(key, False)

					if value is True:
						table_source.append("  - Yes")
					elif value is False:
						table_source.append("  - No")
					else:
						table_source.append(f"  - {value}")

				table_source.append(f"  - {tool.get('released', '')}")
				table_source.append(f"  - {tool.get('python_versions', '')}")

		node = nodes.paragraph()
		self.state.nested_parse(StringList(table_source), self.content_offset, node)
		purger.add_node(self.env, node, node, self.lineno)

		return [node]


def setup(app: Sphinx):
	app.add_directive("project-comparison", ComparisonDirective)
	app.connect("env-purge-doc", purger.purge_nodes)
