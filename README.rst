#####
whey
#####

.. start short_desc

**A simple Python wheel builder for simple projects.**

.. end short_desc


``whey``:

* supports `PEP 621 <https://www.python.org/dev/peps/pep-0621/>`_ metadata.
* can be used as a `PEP 517 <https://www.python.org/dev/peps/pep-0517/>`_ build backend.
* creates `PEP 427 <https://www.python.org/dev/peps/pep-0427/>`_ `wheels <https://realpython.com/python-wheels/>`_.
* handles type hint files
  (`py.typed <https://www.python.org/dev/peps/pep-0561/>`_ and ``*.pyi`` stubs).
* is distributed under the `MIT License <https://choosealicense.com/licenses/mit/>`_.
* `is the liquid remaining after milk has been curdled and strained <https://en.wikipedia.org/wiki/Whey>`_.
  It is a byproduct of the manufacture of cheese and has several commercial uses.


See `the documentation`_ for configuration_ and usage_ information.

.. _the documentation: https://whey.readthedocs.io/en/latest/
.. _configuration: https://whey.readthedocs.io/en/latest/configuration.html
.. _usage: https://whey.readthedocs.io/en/latest/configuration.html

.. start shields

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

.. |docs| image:: https://img.shields.io/readthedocs/whey/latest?logo=read-the-docs
	:target: https://whey.readthedocs.io/en/latest
	:alt: Documentation Build Status

.. |docs_check| image:: https://github.com/repo-helper/whey/workflows/Docs%20Check/badge.svg
	:target: https://github.com/repo-helper/whey/actions?query=workflow%3A%22Docs+Check%22
	:alt: Docs Check Status

.. |actions_linux| image:: https://github.com/repo-helper/whey/workflows/Linux/badge.svg
	:target: https://github.com/repo-helper/whey/actions?query=workflow%3A%22Linux%22
	:alt: Linux Test Status

.. |actions_windows| image:: https://github.com/repo-helper/whey/workflows/Windows/badge.svg
	:target: https://github.com/repo-helper/whey/actions?query=workflow%3A%22Windows%22
	:alt: Windows Test Status

.. |actions_macos| image:: https://github.com/repo-helper/whey/workflows/macOS/badge.svg
	:target: https://github.com/repo-helper/whey/actions?query=workflow%3A%22macOS%22
	:alt: macOS Test Status

.. |actions_flake8| image:: https://github.com/repo-helper/whey/workflows/Flake8/badge.svg
	:target: https://github.com/repo-helper/whey/actions?query=workflow%3A%22Flake8%22
	:alt: Flake8 Status

.. |actions_mypy| image:: https://github.com/repo-helper/whey/workflows/mypy/badge.svg
	:target: https://github.com/repo-helper/whey/actions?query=workflow%3A%22mypy%22
	:alt: mypy status

.. |requires| image:: https://requires.io/github/repo-helper/whey/requirements.svg?branch=master
	:target: https://requires.io/github/repo-helper/whey/requirements/?branch=master
	:alt: Requirements Status

.. |coveralls| image:: https://img.shields.io/coveralls/github/repo-helper/whey/master?logo=coveralls
	:target: https://coveralls.io/github/repo-helper/whey?branch=master
	:alt: Coverage

.. |codefactor| image:: https://img.shields.io/codefactor/grade/github/repo-helper/whey?logo=codefactor
	:target: https://www.codefactor.io/repository/github/repo-helper/whey
	:alt: CodeFactor Grade

.. |pypi-version| image:: https://img.shields.io/pypi/v/whey
	:target: https://pypi.org/project/whey/
	:alt: PyPI - Package Version

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/whey?logo=python&logoColor=white
	:target: https://pypi.org/project/whey/
	:alt: PyPI - Supported Python Versions

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/whey
	:target: https://pypi.org/project/whey/
	:alt: PyPI - Supported Implementations

.. |wheel| image:: https://img.shields.io/pypi/wheel/whey
	:target: https://pypi.org/project/whey/
	:alt: PyPI - Wheel

.. |conda-version| image:: https://img.shields.io/conda/v/domdfcoding/whey?logo=anaconda
	:target: https://anaconda.org/domdfcoding/whey
	:alt: Conda - Package Version

.. |conda-platform| image:: https://img.shields.io/conda/pn/domdfcoding/whey?label=conda%7Cplatform
	:target: https://anaconda.org/domdfcoding/whey
	:alt: Conda - Platform

.. |license| image:: https://img.shields.io/github/license/repo-helper/whey
	:target: https://github.com/repo-helper/whey/blob/master/LICENSE
	:alt: License

.. |language| image:: https://img.shields.io/github/languages/top/repo-helper/whey
	:alt: GitHub top language

.. |commits-since| image:: https://img.shields.io/github/commits-since/repo-helper/whey/v0.0.16
	:target: https://github.com/repo-helper/whey/pulse
	:alt: GitHub commits since tagged version

.. |commits-latest| image:: https://img.shields.io/github/last-commit/repo-helper/whey
	:target: https://github.com/repo-helper/whey/commit/master
	:alt: GitHub last commit

.. |maintained| image:: https://img.shields.io/maintenance/yes/2021
	:alt: Maintenance

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/whey
	:target: https://pypi.org/project/whey/
	:alt: PyPI - Downloads

.. end shields

Installation
--------------

.. start installation

``whey`` can be installed from PyPI or Anaconda.

To install with ``pip``:

.. code-block:: bash

	$ python -m pip install whey

To install with ``conda``:

	* First add the required channels

	.. code-block:: bash

		$ conda config --add channels https://conda.anaconda.org/conda-forge
		$ conda config --add channels https://conda.anaconda.org/domdfcoding

	* Then install

	.. code-block:: bash

		$ conda install whey

.. end installation

``whey`` also has an optional README validation feature, which checks the README will render correctly on PyPI.
This requires that the ``readme`` extra is installed:

.. code-block:: bash

	$ python -m pip install whey[readme]

and in ``pyproject.toml``:

.. code-block:: TOML

	[build-system]
	requires = [ "whey[readme]",]
	build-backend = "whey"
