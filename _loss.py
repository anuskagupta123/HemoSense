"""Compatibility shim for older pickled sklearn models.

Some legacy model pickles reference a top-level `_loss` module.
This re-exports the modern sklearn loss symbols so unpickling works.
"""

from sklearn._loss.loss import *  # noqa: F401,F403
