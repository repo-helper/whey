#  This file is managed by 'repo_helper'. Don't edit it directly.

__all__ = ["extras_require"]

extras_require = {
		"readme": ["docutils==0.16", "pyproject-parser[readme]>=0.6.0"],
		"editable": ["editables>=0.2"],
		"all": ["docutils==0.16", "editables>=0.2", "pyproject-parser[readme]>=0.6.0"]
		}
