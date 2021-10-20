=====================
Command Line Usage
=====================

whey
--------------------

.. click:: whey.__main__:main
	:prog: whey
	:nested: none

Editable installs
------------------

Whey also supports :pep:`660` editable installs via :github:repo:`pip <pypa/pip>`.
Editable installs allow changes to the project's source code (but not its entry points and other metadata)
to be automatically reflected when the module is next imported.

To install the project in the current directory in editable mode, run the following command:

.. prompt:: bash

	python3 -m pip install --editable .

See the pip documentation_ for more details.

If using pip's ``--no-build-isolation`` flag [1]_, whey must be installed with the ``editable`` extra, as additional requirements are required for editable installs.

.. _documentation: https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-e
.. [1] https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-build-isolation
