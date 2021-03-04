MINIMAL_CONFIG = '[project]\nname = "spam"\nversion = "2020.0.0"'

KEYWORDS = f"""\
{MINIMAL_CONFIG}
keywords = ["egg", "bacon", "sausage", "tomatoes", "Lobster Thermidor"]
"""

AUTHORS = f"""\
{MINIMAL_CONFIG}
authors = [
  {{email = "hi@pradyunsg.me"}},
  {{name = "Tzu-Ping Chung"}}
]
"""

UNICODE = f"""\
{MINIMAL_CONFIG}
description = "Factory ⸻ A code generator 🏭"
authors = [{{name = "Łukasz Langa"}}]
"""

MAINTAINERS = f"""\
{MINIMAL_CONFIG}
maintainers = [
  {{name = "Brett Cannon", email = "brett@python.org"}}
]
"""

CLASSIFIERS = f"""\
{MINIMAL_CONFIG}
classifiers = [
  "Development Status :: 4 - Beta",
  "Programming Language :: Python"
]
"""

DEPENDENCIES = f"""\
{MINIMAL_CONFIG}
dependencies = [
  "httpx",
  "gidgethub[httpx]>4.0.0",
  "django>2.1; os_name != 'nt'",
  "django>2.0; os_name == 'nt'"
]
"""

OPTIONAL_DEPENDENCIES = f"""\
{MINIMAL_CONFIG}

[project.optional-dependencies]
test = [
  "pytest < 5.0.0",
  "pytest-cov[all]"
]
"""

URLS = f"""\
{MINIMAL_CONFIG}

[project.urls]
homepage = "example.com"
documentation = "readthedocs.org"
repository = "github.com"
changelog = "github.com/me/spam/blob/master/CHANGELOG.md"
"""

ENTRY_POINTS = f"""\
{MINIMAL_CONFIG}

[project.scripts]
spam-cli = "spam:main_cli"

[project.gui-scripts]
spam-gui = "spam:main_gui"

[project.entry-points."spam.magical"]
tomatoes = "spam:main_tomatoes"
"""
