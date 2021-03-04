=====================
Configuration
=====================

``whey`` is configured in the ``pyproject.toml`` file defined in :pep:`517` and :pep:`517`.


``[build-system]``
-------------------


``whey`` must be set as the ``build-backend`` in the ``[build-system]`` table.

**Example**:

.. code-block:: TOML

	[build-system]
	requires = ["whey"]
	build-backend = "whey"

``[project]``
-------------------

The metadata used by ``whey`` is defined in the ``[project]`` table, per :pep:`621`;
see that document for more details on the keys and their values.

As a minimum, the table should contain the keys ``name`` and ``version``.

.. conf:: dynamic

	**Type**: :class:`list`\[:class:`str`\]

	Specifies which fields listed by :pep:`621` were intentionally unspecified so ``whey`` can provide such metadata dynamically.
	Whey currently only supports ``classifiers``, ``dependencies``, and ``requires-python`` as dynamic fields.


``[tool.whey]``
-------------------

.. conf:: package

	**Type**: :class:`str`

	The path to the package to distribute, relative to the directory containing ``pyproject.toml``.
	This defaults to `project.name <https://www.python.org/dev/peps/pep-0621/#name>`_ if unspecified.

	**Examples**:

	.. code-block:: TOML

		[project]
		name = "flake8"

		[tool.whey]
		package = "src/flake8"

	.. code-block:: TOML

		[project]
		name = "domdf-python-tools"

		[tool.whey]
		package = "domdf_python_tools"


.. conf:: additional-files

	**Type**: :class:`list`\[:class:`str`\]

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

	``whey`` was built with type hints in mind, and so it will automatically include any ``py.typed`` files and ``*.pyi`` stub files automatically.

	**Example**:

	.. code-block:: TOML

		[tool.whey]
		additional-files = [
			"include domdf_python_tools/google-10000-english-no-swears.txt",
			"recursive-exclude domdf_python_tools *.json",
		]


.. conf:: license-key

	**Type**: :class:`str`

	An identifier giving the project's license. This is used for the `License <https://packaging.python.org/specifications/core-metadata/#license>`_ field in the Core Metadata, and to add the appropriate `trove classifier <https://pypi.org/classifiers/>`_.

	It is recommended to use an `SPDX Identifier <https://spdx.org/licenses/>`_, but note that not all map to classifiers.

	**Example**:

	.. code-block:: TOML

		[tool.whey]
		license-key = "MIT"


.. conf:: base-classifiers

	**Type**: :class:`list`\[:class:`str`\]

	A list of `trove classifiers <https://pypi.org/classifiers/>`_.

	This list will be extended with the appropriate classifiers for supported platforms,
	Python versions and implementations, and the project's license.
	This field is ignored if `classifiers <https://www.python.org/dev/peps/pep-0621/#classifiers>`_
	is not listed in `dynamic <https://www.python.org/dev/peps/pep-0621/#dynamic>`_

	**Example**:

	.. code-block:: TOML

		[tool.whey]
		base-classifiers = [
			"Development Status :: 3 - Alpha",
			"Typing :: Typed",
		]



.. conf:: platforms

	**Type**: :class:`list`\[:class:`str`\]

	A list of supported platforms. This is used to add appropriate `trove classifiers <https://pypi.org/classifiers/>`__ and is listed under `Platform <https://packaging.python.org/specifications/core-metadata/#platform-multiple-use>`_ in the Core Metadata.

	**Example**:

	.. code-block:: TOML

		[tool.whey]
		platforms = [
			"Windows",
			"Linux",
		]


.. conf:: python-implementations

	**Type**: :class:`list`\[:class:`str`\]

	A list of supported Python implementations. This can be used to add appropriate `trove classifiers <https://pypi.org/classifiers/>`__.

	**Example**:

	.. code-block:: TOML

		[tool.whey]
		python-implementations = [
			"CPython",
			"PyPy",
		]



.. conf:: python-versions

	**Type**: :class:`list`\[:class:`str`\]

	A list of supported Python versions. This can be used to add appropriate `trove classifiers <https://pypi.org/classifiers/>`__ and dynamically determine the minimum required Python version for `requires-python <https://www.python.org/dev/peps/pep-0621/#requires-python>`_.

	**Example**:

	.. code-block:: TOML

		[tool.whey]
		python-versions = [
			"3.6",
			"3.7",
		]
