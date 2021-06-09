# 3rd party
from sphinx import addnodes
from sphinx.writers.latex import LaTeXTranslator


def visit_desc(translator: LaTeXTranslator, node: addnodes.desc) -> None:
	"""
	Visit an :class:`addnodes.desc` node and add a custom table of contents label for the item, if required.

	:param translator:
	:param node:
	"""

	translator.body.append(r"\needspace{4\baselineskip}")

	if "sphinxcontrib.toctree_plus" in translator.config.extensions:
		# 3rd party
		from sphinxcontrib import toctree_plus  # nodep

		toctree_plus.visit_desc(translator, node)
	else:
		LaTeXTranslator.visit_desc(translator, node)


def setup(app):
	app.add_node(addnodes.desc, latex=(visit_desc, LaTeXTranslator.depart_desc), override=True)

	return {"parallel_read_safe": True}
