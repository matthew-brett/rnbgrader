""" RNBGrader package
"""

from .nbparser import load, loads
from .kernels import JupyterKernel
from .nbrunner import NotebookRunner

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
