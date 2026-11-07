"""Evaluation Deepeval integration package."""

__version__ = "0.1.0"

# Public objects exported by this package
__all__ = [
    "GroqDeepEvalModel",
    "run_deepeval_evaluation",
]

# Local imports – no relative imports of the package itself
from evaluation_deepeval.models import GroqDeepEvalModel
from evaluation_deepeval.runner import run_deepeval_evaluation