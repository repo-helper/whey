# stdlib
from pprint import pprint

# this package
from whey.config import load_toml

config = load_toml("example_pyproject.toml")
pprint(config)
