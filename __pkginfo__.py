#  This file is managed by 'repo_helper'. Don't edit it directly.

__all__ = ["extras_require"]

extras_require = {
		"readme": [
				"docutils<0.22,>=0.16",
				'nh3<0.3.2; platform_python_implementation == "PyPy" and python_version < "3.11"',
				"pyproject-parser[readme]>=0.11.0b1"
				],
		"editable": ["editables>=0.2"],
		"all": [
				"docutils<0.22,>=0.16",
				"editables>=0.2",
				'nh3<0.3.2; platform_python_implementation == "PyPy" and python_version < "3.11"',
				"pyproject-parser[readme]>=0.11.0b1"
				]
		}
