# stdlib
import json
from typing import Any

# 3rd party
from sphinx.application import Sphinx
from sphinx_toolbox.more_autodoc.variables import VariableDocumenter

# this package
from whey.config.whey import license_lookup


class LicenseLookupDocumenter(VariableDocumenter):

	def add_content(self, more_content: Any, no_docstring: bool = False) -> None:
		super().add_content(more_content, no_docstring)

		if self.object is license_lookup:
			sourcename = self.get_sourcename()

			self.add_line('', sourcename)
			self.add_line(".. code-block:: JSON", sourcename)
			self.add_line('', sourcename)

			for line in json.dumps(license_lookup, indent=2).splitlines():
				self.add_line(f"    {line}", sourcename)

			self.add_line('', sourcename)


def setup(app: Sphinx):
	app.add_autodocumenter(LicenseLookupDocumenter, override=True)
