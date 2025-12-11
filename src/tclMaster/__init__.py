from .core import tclMaster

from .utilities import utilities
from .utilities import TclPreprocessor
from .utilities.batch_replace import batch_replace
from .utilities.batch_comment_out_block import batch_comment_out_block

__all__ = [
    "tclMaster",
    "utilities",
    "TclPreprocessor",
    'batch_replace',
    'batch_comment_out_block',
]