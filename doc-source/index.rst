=====
whey
=====

.. figure:: Little_Miss_Muffet_-_Sir_John_Everett_Millais.png
	:figwidth: 30%
	:align: right

	Miss Muffet sitting on a tuffet, by :wikipedia:`John Everett Millais`, 1884

.. start short_desc

.. documentation-summary::
	:meta:

.. end short_desc


..

	| Little Miss Muffet
	| She sat on a tuffet,
	| Eating of curds and whey;
	| There came a little spider,
	| Who sat down beside her,
	| And frighten'd Miss Muffet away.


``whey``:

* supports :pep:`621` metadata.
* can be used as a :pep:`517` build backend.
* creates :pep:`427` `wheels <https://realpython.com/python-wheels/>`_.
* handles type hint files
  (`py.typed <https://www.python.org/dev/peps/pep-0561/>`_ and ``*.pyi`` stubs).
* is distributed under the `MIT License <https://choosealicense.com/licenses/mit/>`_.
* :wikipedia:`is the liquid remaining after milk has been curdled and strained <Whey>`.
  It is a byproduct of the manufacture of cheese and has several commercial uses.

.. start shields

.. only:: html

	.. list-table::
		:stub-columns: 1
		:widths: 10 90

		* - Docs
		  - |docs| |docs_check|
		* - Tests
		  - |actions_linux| |actions_windows| |actions_macos| |coveralls|
		* - PyPI
		  - |pypi-version| |supported-versions| |supported-implementations| |wheel|
		* - Anaconda
		  - |conda-version| |conda-platform|
		* - Activity
		  - |commits-latest| |commits-since| |maintained| |pypi-downloads|
		* - QA
		  - |codefactor| |actions_flake8| |actions_mypy|
		* - Other
		  - |license| |language| |requires|

	.. |docs| rtfd-shield::
		:project: whey
		:alt: Documentation Build Status

	.. |docs_check| actions-shield::
		:workflow: Docs Check
		:alt: Docs Check Status

	.. |actions_linux| actions-shield::
		:workflow: Linux
		:alt: Linux Test Status

	.. |actions_windows| actions-shield::
		:workflow: Windows
		:alt: Windows Test Status

	.. |actions_macos| actions-shield::
		:workflow: macOS
		:alt: macOS Test Status

	.. |actions_flake8| actions-shield::
		:workflow: Flake8
		:alt: Flake8 Status

	.. |actions_mypy| actions-shield::
		:workflow: mypy
		:alt: mypy status

	.. |requires| image:: https://dependency-dash.herokuapp.com/github/repo-helper/whey/badge.svg
		:target: https://dependency-dash.herokuapp.com/github/repo-helper/whey/
		:alt: Requirements Status

	.. |coveralls| coveralls-shield::
		:alt: Coverage

	.. |codefactor| codefactor-shield::
		:alt: CodeFactor Grade

	.. |pypi-version| pypi-shield::
		:project: whey
		:version:
		:alt: PyPI - Package Version

	.. |supported-versions| pypi-shield::
		:project: whey
		:py-versions:
		:alt: PyPI - Supported Python Versions

	.. |supported-implementations| pypi-shield::
		:project: whey
		:implementations:
		:alt: PyPI - Supported Implementations

	.. |wheel| pypi-shield::
		:project: whey
		:wheel:
		:alt: PyPI - Wheel

	.. |conda-version| image:: https://img.shields.io/conda/v/domdfcoding/whey?logo=anaconda
		:target: https://anaconda.org/domdfcoding/whey
		:alt: Conda - Package Version

	.. |conda-platform| image:: https://img.shields.io/conda/pn/domdfcoding/whey?label=conda%7Cplatform
		:target: https://anaconda.org/domdfcoding/whey
		:alt: Conda - Platform

	.. |license| github-shield::
		:license:
		:alt: License

	.. |language| github-shield::
		:top-language:
		:alt: GitHub top language

	.. |commits-since| github-shield::
		:commits-since: v0.0.17
		:alt: GitHub commits since tagged version

	.. |commits-latest| github-shield::
		:last-commit:
		:alt: GitHub last commit

	.. |maintained| maintained-shield:: 2021
		:alt: Maintenance

	.. |pypi-downloads| pypi-shield::
		:project: whey
		:downloads: month
		:alt: PyPI - Downloads

.. end shields

Installation
---------------

.. start installation

.. installation:: whey
	:pypi:
	:github:
	:anaconda:
	:conda-channels: conda-forge, domdfcoding

.. end installation


.. latex:vspace:: 20px


``whey`` also has an optional README validation feature, which checks the README will render correctly on PyPI.
This requires that the ``readme`` extra is installed:

.. code-block:: bash

	$ python -m pip install whey[readme]

and in ``pyproject.toml``:

.. code-block:: TOML

	[build-system]
	requires = [ "whey[readme]",]
	build-backend = "whey"

Once the dependencies are installed the validation can be disabled by setting the
:envvar:`CHECK_README` environment variable to ``0``.

Contents
-----------

.. html-section::

.. toctree::
	:hidden:

	Home<self>

.. toctree::
	:maxdepth: 3
	:caption: Documentation
	:glob:

	configuration
	cli
	Source
	license

.. toctree::
	:maxdepth: 3
	:caption: API Reference
	:glob:

	api/*
	extending

.. sidebar-links::
	:caption: Links
	:github:
	:pypi: whey

	Contributing Guide <https://contributing.repo-helper.uk>

.. start links

.. only:: html

	View the :ref:`Function Index <genindex>` or browse the `Source Code <_modules/index.html>`__.

	:github:repo:`Browse the GitHub Repository <repo-helper/whey>`

.. end links
