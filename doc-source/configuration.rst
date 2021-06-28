=====================
Configuration
=====================

``whey`` is configured in the ``pyproject.toml`` file defined in :pep:`517` and :pep:`518`.

.. note::

	``whey`` only supports `TOML v0.5.0 <https://toml.io/en/v0.5.0>`_.
	``pyproject.toml`` files using features of newer TOML versions may not parse correctly.


``[build-system]``
-------------------

``whey`` must be set as the ``build-backend`` in the ``[build-system]`` table.

:bold-title:`Example`:

.. code-block:: TOML

	[build-system]
	requires = ["whey"]
	build-backend = "whey"


``[project]``
-------------------

The metadata used by ``whey`` is defined in the ``[project]`` table, per :pep:`621`.

As a minimum, the table MUST contain the keys ``name`` and ``version``.


.. conf:: name

	**Type**: :toml:`String`

	The name of the project.

	Ideally, the name should be normalised to lowercase, with underscores replaced by hyphens.

	This key is required, and MUST be defined statically.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		name = "spam"


.. conf:: version

	**Type**: :toml:`String`

	The version of the project as supported by :pep:`440`.

	This key is required, and MUST be defined statically.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		version = "2020.0.0"


.. conf:: description

	**Type**: :toml:`String`

	A summary description of the project.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		description = "Lovely Spam! Wonderful Spam!"


.. conf:: readme

	**Type**: :toml:`String` or :toml:`table <Table>`

	The full description of the project (i.e. the README).

	The field accepts either a string or a table.
	If it is a string then it is the relative path to a text file containing the full description.
	The file's encoding MUST be UTF-8, and have one of the following content types:

	* ``text/markdown``, with a a case-insensitive ``.md`` suffix.
	* ``text/x-rst``, with a a case-insensitive ``.rst`` suffix.
	* ``text/plain``, with a a case-insensitive ``.txt`` suffix.

	The readme field may instead be a table with the following keys:

	* ``file`` -- a string value representing a relative path to a file containing the full description.
	* ``text`` -- a string value which is the full description.
	* ``content-type`` -- (required) a string specifying the content-type of the full description.
	* ``charset`` -- (optional, default UTF-8) the encoding of the ``file``.

	The ``file`` and ``text`` keys are mutually exclusive, but one must be provided in the table.

	:bold-title:`Examples:`

	.. code-block:: TOML

		[project]
		readme = "README.rst"

		[project.readme]
		file = "README.rst"
		content-type = "text/x-rst"
		encoding = "UTF-8"

		[project.readme]
		text = "Spam is a brand of canned cooked pork made by Hormel Foods Corporation."
		content-type = "text/x-rst"


.. latex:clearpage::


.. conf:: requires-python

	**Type**: :toml:`String`

	The Python version requirements of the project, as a :pep:`508` marker.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		requires-python = ">=3.6"


.. conf:: license

	**Type**: :toml:`Table`


	The table may have one of two keys:

	* ``file`` -- a string value that is a relative file path to the file which contains
	  the license for the project. The file's encoding MUST be UTF-8.
	* ``text`` -- string value which is the license of the project.

	These keys are mutually exclusive.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.license]
		file = "LICENSE.rst"

		[project.license]
		file = "COPYING"

		[project.license]
		text = """
		This software may only be obtained by sending the author a postcard,
		and then the user promises not to redistribute it.
		"""


.. conf:: authors

	**Type**: :toml:`Array` of :toml:`inline tables <Inline Table>` with string keys and values

	The tables list the people or organizations considered to be the "authors" of the project.

	Each table has 2 keys: ``name`` and ``email``.
	Both values must be strings.

	* The ``name`` value MUST be a valid email name (i.e. whatever can be put as a name,
	  before an email, in :rfc:`822`) and not contain commas.
	* The ``email`` value MUST be a valid email address.

	Both keys are optional.

	:bold-title:`Examples:`

	.. code-block:: TOML

		[project]
		authors = [
			{email = "hi@pradyunsg.me"},
			{name = "Tzu-Ping Chung"}
		]

		[[project.authors]]
		name = "Tzu-Ping Chung"


.. conf:: maintainers

	**Type**: :toml:`Array` of :toml:`inline tables <Inline Table>` with string keys and values

	The tables list the people or organizations considered to be the "maintainers" of the project.

	This field otherwise functions the same as :conf:`authors`.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		authors = [
		  {email = "hi@pradyunsg.me"},
		  {name = "Tzu-Ping Chung"}
		]
		maintainers = [
		  {name = "Brett Cannon", email = "brett@python.org"}
		]


.. conf:: keywords

	**Type**: :toml:`Array` of :toml:`strings <String>`

	The keywords for the project.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		keywords = [ "egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor",]


.. conf:: classifiers

	**Type**: :toml:`Array` of :toml:`strings <String>`

	The `trove classifiers`_ which apply to the project.

	.. _trove classifiers: https://pypi.org/classifiers/

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		classifiers = [
			"Development Status :: 4 - Beta",
			"Programming Language :: Python"
		]


.. conf:: urls

	**Type**: :toml:`Table`, with keys and values of :toml:`strings <String>`

	A table of URLs where the key is the URL label and the value is the URL itself.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.urls]
		homepage = "https://example.com"
		documentation = "https://readthedocs.org"
		repository = "https://github.com"
		changelog = "https://github.com/me/spam/blob/master/CHANGELOG.md"


.. conf:: scripts

	**Type**: :toml:`Table`, with keys and values of :toml:`strings <String>`

	The console scripts provided by the project.

	The keys are the names of the scripts and the values are the object references
	in the form ``module.submodule:object``.

	See the `entry point specification`_ for more details.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.scripts]
		spam-cli = "spam:main_cli"
		# One which depends on extras:
		foobar = "foomod:main_bar [bar,baz]"


.. conf:: gui-scripts

	**Type**: :toml:`Table`, with keys and values of :toml:`strings <String>`

	The graphical application scripts provided by the project.

	The keys are the names of the scripts and the values are the object references
	in the form ``module.submodule:object``.

	See the `entry point specification`_ for more details.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.gui-scripts]
		spam-gui = "spam.gui:main_gui"


.. conf:: entry-points

	**Type**: :toml:`Table` of :toml:`tables <!Table>`, with keys and values of :toml:`strings <String>`

	Each sub-table's name is an entry point group.

	Users MUST NOT create nested sub-tables but instead keep the entry point groups to only one level deep.

	Users MUST NOT create sub-tables for ``console_scripts`` or ``gui_scripts``.
	Use ``[project.scripts]`` and ``[project.gui-scripts]`` instead.

	See the `entry point specification`_ for more details.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.entry-points."spam.magical"]
		tomatoes = "spam:main_tomatoes"

		# pytest plugins refer to a module, so there is no ':obj'
		[project.entry-points.pytest11]
		nbval = "nbval.plugin"

.. _entry point specification: https://packaging.python.org/specifications/entry-points/


.. conf:: dependencies

	**Type**: :toml:`Array` of :pep:`508` strings

	The dependencies of the project.

	Each string MUST be formatted as a valid :pep:`508` string.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		dependencies = [
			"httpx",
			"gidgethub[httpx]>4.0.0",
			"django>2.1; os_name != 'nt'",
			"django>2.0; os_name == 'nt'"
		]


.. conf:: optional-dependencies

	**Type**: :toml:`Table` with values of :toml:`arrays <Array>` of :pep:`508` strings

	The optional dependencies of the project.

	* The keys specify an extra, and must be valid Python identifiers.
	* The values are arrays of strings, which must be valid :pep:`508` strings.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.optional-dependencies]
		test = [
		  "pytest < 5.0.0",
		  "pytest-cov[all]"
		]


.. conf:: dynamic

	**Type**: :toml:`Array` of :toml:`strings <String>`

	Specifies which fields listed by :pep:`621` were intentionally unspecified
	so ``whey`` can provide such metadata dynamically.

	Whey currently only supports ``classifiers``, ``dependencies``, and ``requires-python`` as dynamic fields.


	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		dynamic = [ "classifiers", ]

		[tool.whey]
		base-classifiers = [
			"Development Status :: 3 - Alpha",
			"Typing :: Typed",
		]


``[tool.whey]``
-------------------

.. conf:: package

	**Type**: :toml:`String`

	The path to the package to distribute, relative to the directory containing ``pyproject.toml``.
	This defaults to :conf:`project.name <name>` if unspecified.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		name = "domdf-python-tools"

		[tool.whey]
		package = "domdf_python_tools"


.. conf:: source-dir

	**Type**: :toml:`String`

	The name of the directory containing the project's source.
	This defaults to ``'.'`` if unspecified.

	.. versionadded:: 0.0.4

	.. attention::

		:conf:`source-dir` does not currently work correctly with :conf:`additional-files`

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		name = "flake8"

		[tool.whey]
		source_dir = "src/flake8"


.. conf:: additional-files

	**Type**: :toml:`Array` of :toml:`strings <String>`

	A list of `MANIFEST.in <https://packaging.python.org/guides/using-manifest-in/>`_-style
	entries for additional files to include in distributions.

	The supported commands are:

	=========================================================  ==================================================================================================
	Command                                                    Description
	=========================================================  ==================================================================================================
	:samp:`include {pat1} {pat2} ...`                          Add all files matching any of the listed patterns
	:samp:`exclude {pat1} {pat2} ...`                          Remove all files matching any of the listed patterns
	:samp:`recursive-include {dir-pattern} {pat1} {pat2} ...`  Add all files under directories matching ``dir-pattern`` that match any of the listed patterns
	:samp:`recursive-exclude {dir-pattern} {pat1} {pat2} ...`  Remove all files under directories matching ``dir-pattern`` that match any of the listed patterns
	=========================================================  ==================================================================================================

	``whey`` was built with type hints in mind, so it will automatically include any ``py.typed`` files and ``*.pyi`` stub files automatically.

	.. raw:: latex

		\begin{minipage}{\textwidth}

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		additional-files = [
			"include domdf_python_tools/google-10000-english-no-swears.txt",
			"recursive-exclude domdf_python_tools *.json",
		]

	.. raw:: latex

		\end{minipage}

.. conf:: license-key

	**Type**: :toml:`String`

	An identifier giving the project's license. This is used for the `License <https://packaging.python.org/specifications/core-metadata/#license>`_ field in the Core Metadata, and to add the appropriate `trove classifier <https://pypi.org/classifiers/>`_.

	It is recommended to use an `SPDX Identifier <https://spdx.org/licenses/>`_, but note that not all map to classifiers.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		license-key = "MIT"


.. conf:: base-classifiers

	**Type**: :toml:`Array` of :toml:`strings <String>`

	A list of `trove classifiers <https://pypi.org/classifiers/>`_.

	This list will be extended with the appropriate classifiers for supported platforms,
	Python versions and implementations, and the project's license.
	This field is ignored if :conf:`classifiers` is not listed in :conf:`dynamic`

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		dynamic = [ "classifiers", ]

		[tool.whey]
		base-classifiers = [
			"Development Status :: 3 - Alpha",
			"Typing :: Typed",
		]



.. conf:: platforms

	**Type**: :toml:`Array` of :toml:`strings <String>`

	A list of supported platforms. This is used to add appropriate `trove classifiers <https://pypi.org/classifiers/>`__ and is listed under `Platform <https://packaging.python.org/specifications/core-metadata/#platform-multiple-use>`_ in the Core Metadata.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		platforms = [ "Windows", "Linux",]


.. conf:: python-implementations

	**Type**: :toml:`Array` of :toml:`strings <String>`

	A list of supported Python implementations. This can be used to add appropriate `trove classifiers <https://pypi.org/classifiers/>`__.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		python-implementations = [ "CPython", "PyPy",]


.. latex:clearpage::

.. conf:: python-versions

	**Type**: :toml:`Array` of :toml:`strings <String>`

	A list of supported Python versions. This can be used to add appropriate `trove classifiers <https://pypi.org/classifiers/>`__ and dynamically determine the minimum required Python version for :conf:`requires-python`.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		python-versions = [
			"3.6",
			"3.7",
		]
