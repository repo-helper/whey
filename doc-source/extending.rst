=====================
Extending whey
=====================

``whey`` can be extended to support building different distribution types (e.g. conda, DEB, RPM) or to modify the behaviour of an existing builder.

Custom builders must be registered as an entry point in the ``whey.builder`` group. For example:

.. code-block:: TOML

	# pyproject.toml

	[project.entry-points."whey.builder"]
	whey_sdist = "whey.builder:SDistBuilder"
	whey_wheel = "whey.builder:WheelBuilder"


.. code-block:: ini

	# setup.cfg

	[options.entry_points]
	whey.builder =
		whey_sdist = whey.builder:SDistBuilder
		whey_wheel = whey.builder:WheelBuilder

Each builder must inherit from :class:`whey.builder.AbstractBuilder`.

The custom builders can be enabled by setting keys in the ``tool.whey.builders`` table.
The table supports three keys: ``sdist``, ``wheel``, ``binary``.

* The ``sdist`` builder is used when running whey with the :option:`--sdist <whey -s>` option
  or when using the :pep:`517` backend to build an sdist.
* The ``wheel`` builder is used when running whey with the :option:`--wheel <whey -w>` option
  or when using the :pep:`517` backend to build a wheel.
* The ``binary`` builder is used when running whey with the :option:`--binary <whey -b>` option.

The value for each key is the name of an entry point, such as ``whey_sdist`` from the example above.
