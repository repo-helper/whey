.. _configuration:

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
	requires = [ "whey",]
	build-backend = "whey"


``[project]``
-------------------

The metadata used by ``whey`` is defined in the ``[project]`` table, per :pep:`621`.

As a minimum, the table MUST contain the keys :tconf:`~project.name` and :tconf:`~project.version` [1]_.

.. [1] Other tools, such as flit_ and trampolim_, may support determining :tconf:`project.version`
       dynamically without specifying a value in ``pyproject.toml``.

.. _flit: https://flit.readthedocs.io/en/latest/
.. _trampolim: https://github.com/FFY00/trampolim


.. tconf:: project.name
	:type: :toml:`String`
	:required: True

	The name of the project.

	Ideally, the name should be normalised to lowercase, with underscores replaced by hyphens.

	This key is required, and MUST be defined statically.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		name = "spam"


.. latex:clearpage::

.. tconf:: project.version
	:type: :toml:`String`

	The version of the project as supported by :pep:`440`.

	With ``whey`` this key is required, and must be defined statically.
	Other backends may support determining this value automatically if it is listed in :tconf:`project.dynamic`.


	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		version = "2020.0.0"


.. tconf:: project.description
	:type: :toml:`String`

	A short summary description of the project.

	PyPI will display this towards the top of the `project page`_.
	A longer description can be provided as :tconf:`~project.readme`.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		description = "Lovely Spam! Wonderful Spam!"


.. tconf:: project.readme
	:type: :toml:`String` or :toml:`table <Table>`

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

	PyPI will display this on the `project page`_

	:bold-title:`Examples:`

	.. code-block:: TOML

		[project]
		readme = "README.rst"

	.. code-block:: TOML

		[project]
		readme = {file = "README.md", content-type = "text/markdown", encoding = "UTF-8"}

	.. code-block:: TOML

		[project.readme]
		text = "Spam is a brand of canned cooked pork made by Hormel Foods Corporation."
		content-type = "text/x-rst"


.. tconf:: project.requires-python
	:type: :toml:`String`

	The Python version requirements of the project, as a :pep:`508` specifier.

	.. latex:vspace:: -5px

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		requires-python = ">=3.6"


.. tconf:: project.license
	:type: :toml:`Table`


	The table may have one of two keys:

	* ``file`` -- a string value that is a relative file path to the file which contains
	  the license for the project. The file's encoding MUST be UTF-8.
	* ``text`` -- string value which is the license of the project.

	These keys are mutually exclusive.

	.. latex:vspace:: -5px

	:bold-title:`Examples:`

	.. code-block:: TOML

		[project]
		license = {file = "LICENSE.rst"}

	.. code-block:: TOML

		[project.license]
		file = "COPYING"

	.. code-block:: TOML

		[project.license]
		text = """
		This software may only be obtained by sending the author a postcard,
		and then the user promises not to redistribute it.
		"""


.. tconf:: project.authors
	:type: :toml:`Array` of :toml:`tables <Table>` with string keys and values

	The tables list the people or organizations considered to be the "authors" of the project.

	Each table has 2 keys: ``name`` and ``email``. Both keys are optional, and both values must be strings.

	* The ``name`` value MUST be a valid email name (i.e. whatever can be put as a name,
	  before an email, in :rfc:`822`) and not contain commas.
	* The ``email`` value MUST be a valid email address.

	.. latex:vspace:: -5px

	:bold-title:`Examples:`

	.. code-block:: TOML

		[project]
		authors = [
			{name = "Dominic Davis-Foster", email = "dominic@davis-foster.co.uk"},
			{name = "The pip developers", email = "distutils-sig@python.org"}
		]

	.. code-block:: TOML

		[[project.authors]]
		name = "Tzu-ping Chung"

		[[project.authors]]
		email = "hi@pradyunsg.me"


.. tconf:: project.maintainers
	:type: :toml:`Array` of :toml:`tables <Table>` with string keys and values

	The tables list the people or organizations considered to be the "maintainers" of the project.

	This field otherwise functions the same as :tconf:`~project.authors`.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		authors = [
		  {email = "hi@pradyunsg.me"},
		  {name = "Tzu-ping Chung"}
		]
		maintainers = [
		  {name = "Brett Cannon", email = "brett@python.org"}
		]


.. tconf:: project.keywords
	:type: :toml:`Array` of :toml:`strings <String>`

	The keywords for the project.

	These can be used by community members to find projects based on their desired criteria.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		keywords = [ "egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor",]


.. tconf:: project.classifiers
	:type: :toml:`Array` of :toml:`strings <String>`

	The `trove classifiers`_ which apply to the project.

	Classifiers describe who the project is for, what systems it can run on, and how mature it is.
	These can then be used by community members to find projects based on their desired criteria.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		classifiers = [
			"Development Status :: 4 - Beta",
			"Programming Language :: Python"
		]


.. tconf:: project.urls
	:type: :toml:`Table`, with keys and values of :toml:`strings <String>`

	A table of URLs where the key is the URL label and the value is the URL itself.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.urls]
		homepage = "https://example.com"
		documentation = "https://readthedocs.org"
		repository = "https://github.com"
		changelog = "https://github.com/me/spam/blob/master/CHANGELOG.md"


.. tconf:: project.scripts
	:type: :toml:`Table`, with keys and values of :toml:`strings <String>`

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


.. tconf:: project.gui-scripts
	:type: :toml:`Table`, with keys and values of :toml:`strings <String>`

	The graphical application scripts provided by the project.

	The keys are the names of the scripts, and the values are the object references
	in the form ``module.submodule:object``.

	See the `entry point specification`_ for more details.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project.gui-scripts]
		spam-gui = "spam.gui:main_gui"


.. latex:clearpage::


.. tconf:: project.entry-points
	:type: :toml:`Table` of :toml:`tables <!Table>`, with keys and values of :toml:`strings <String>`

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


.. tconf:: project.dependencies
	:type: :toml:`Array` of :pep:`508` strings

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


.. tconf:: project.optional-dependencies
	:type: :toml:`Table` with values of :toml:`arrays <Array>` of :pep:`508` strings

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


.. latex:clearpage::


.. tconf:: project.dynamic
	:type: :toml:`Array` of :toml:`strings <String>`

	Specifies which fields listed by :pep:`621` were intentionally unspecified
	so ``whey`` can provide such metadata dynamically.

	Whey currently only supports :tconf:`~project.classifiers`, :tconf:`~project.dependencies`,
	and :tconf:`~project.requires-python` as dynamic fields.
	Other tools may support different dynamic fields.


	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		dynamic = [ "classifiers",]

		[tool.whey]
		base-classifiers = [
			"Development Status :: 3 - Alpha",
			"Typing :: Typed",
		]


``[tool.whey]``
-------------------

.. tconf:: tool.whey.package
	:type: :toml:`String`

	The path to the package to distribute, relative to the directory containing ``pyproject.toml``.
	This defaults to :tconf:`project.name` if unspecified.

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		name = "domdf-python-tools"

		[tool.whey]
		package = "domdf_python_tools"


.. tconf:: tool.whey.source-dir
	:type: :toml:`String`

	The name of the directory containing the project's source.
	This defaults to ``'.'`` if unspecified.

	:bold-title:`Examples:`

	.. code-block:: TOML

		[project]
		name = "flake8"

	.. code-block:: TOML

		[tool.whey]
		source_dir = "src/flake8"


.. tconf:: tool.whey.additional-files
	:type: :toml:`Array` of :toml:`strings <String>`

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

	.. note::

		If using :tconf:`tool.whey.source-dir`, the entries for files within the package
		must start with the value of :tconf:`~tool.whey.source-dir`.

		For example, if :tconf:`~tool.whey.source-dir` is ``'src'`` and the package
		is at ``src/spam`` an entry might be ``include src/spam/template.scss``.

	.. raw:: latex

		\begin{minipage}{\textwidth}

	:bold-title:`Examples:`

	.. code-block:: TOML

		[tool.whey]
		additional-files = [
			"include domdf_python_tools/google-10000-english-no-swears.txt",
			"recursive-exclude domdf_python_tools *.json",
		]

	.. code-block:: TOML

		[tool.whey]
		source-dir = "src"
		additional-files = [
			"include src/domdf_python_tools/google-10000-english-no-swears.txt",
			"recursive-exclude src/domdf_python_tools *.json",
		]

	.. raw:: latex

		\end{minipage}

.. tconf:: tool.whey.license-key
	:type: :toml:`String`

	An identifier giving the project's license.

	This is used for the :core-meta:`License` field in the Core Metadata,
	and to add the appropriate `trove classifier`_.

	It is recommended to use an `SPDX Identifier`_, but note that not all map to classifiers.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		license-key = "MIT"


.. tconf:: tool.whey.base-classifiers
	:type: :toml:`Array` of :toml:`strings <String>`

	A list of `trove classifiers <https://pypi.org/classifiers/>`_.

	This list will be extended with the appropriate classifiers for the :tconf:`~tool.whey.license-key`
	and the supported :tconf:`~tool.whey.platforms`, :tconf:`~tool.whey.python-implementations`
	and :tconf:`~tool.whey.python-versions`.

	This field is ignored if :tconf:`~project.classifiers` is not listed in :tconf:`project.dynamic`

	:bold-title:`Example:`

	.. code-block:: TOML

		[project]
		dynamic = [ "classifiers", ]

		[tool.whey]
		base-classifiers = [
			"Development Status :: 3 - Alpha",
			"Typing :: Typed",
		]


.. tconf:: tool.whey.platforms
	:type: :toml:`Array` of :toml:`strings <String>`

	A list of supported platforms. This is used to add appropriate `trove classifiers`_
	and is listed under :core-meta:`Platform` in the Core Metadata.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		platforms = [ "Windows", "Linux",]


.. tconf:: tool.whey.python-implementations
	:type: :toml:`Array` of :toml:`strings <String>`

	A list of supported Python implementations. This can be used to add appropriate `trove classifiers`_.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		python-implementations = [ "CPython", "PyPy",]


.. tconf:: tool.whey.python-versions
	:type: :toml:`Array` of :toml:`strings <String>`

	A list of supported Python versions. This can be used to add appropriate `trove classifiers`_
	and dynamically determine the minimum required Python version for :tconf:`project.requires-python`.

	:bold-title:`Example:`

	.. code-block:: TOML

		[tool.whey]
		python-versions = [
			"3.6",
			"3.7",
		]


.. _trove classifier: https://pypi.org/classifiers/
.. _SPDX Identifier: https://spdx.org/licenses/
.. _project page: https://pypi.org/project/whey/
.. _trove classifiers: https://pypi.org/classifiers/


Enironment Variables
--------------------------

.. envvar:: CHECK_README

	Setting this to ``0`` disables the optional README validation feature,
	which checks the README will render correctly on PyPI.

.. envvar:: SOURCE_DATE_EPOCH

	To make reproducible builds, set this to a timestamp as a number of seconds since
	1970-01-01 UTC, and document the value you used.
	On Unix systems, you can get a value for the current time by running:

	.. prompt:: bash

		date +%s

	.. note:: The timestamp cannot be before 1980-01-01 or after 2170-12-31.

	.. seealso::

		`The SOURCE_DATE_EPOCH specification <https://reproducible-builds.org/specs/source-date-epoch/>`_


Complete Example
------------------

This is an example of a complete ``pyproject.toml`` file for :pep:`621`.

For an explanation of each field, see the :ref:`configuration` section.


.. literalinclude:: pyproject.toml
	:caption: :download:`pyproject.toml`
	:language: toml
