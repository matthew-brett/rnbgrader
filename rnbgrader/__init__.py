""" RNBGrader package
"""

from .nbparser import load, loads
from .kernels import JupyterKernel
from .chunkrunner import ChunkRunner

from . import _version
__version__ = _version.get_versions()['version']
