"""
ML Model Runner — delegates to the real ML model in model/predict.py.

Adds the project root to sys.path so that `model.predict` can be imported,
then calls predict_from_genes() which loads 25+ trained classifiers across
three species and returns antibiotic resistance predictions.
"""

import os
import sys

# ─── Ensure the project root is on sys.path ──────────────────────────────────
# The project root is three levels up from this file:
#   this file : src/backend/app/utils/model_runner.py
#   project root : src/
# We use os.path.abspath to resolve this properly.
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)

if _PROJECT_ROOT not in sys.path:
    # Insert at position 1 to allow current directory to take precedence but
    # still allow absolute imports from the project root.
    sys.path.insert(1, _PROJECT_ROOT)

# ─── Import from the real ML module ──────────────────────────────────────────
from model.predict import predict_from_genes  # noqa: E402


def predict_resistance(genes: list[int]) -> dict[str, str]:
    """
    Predict antibiotic resistance from a gene presence vector.

    Args:
        genes: Binary list (e.g. [1, 0, 1, 0, 0]) from the gene scanner.

    Returns:
        Dictionary mapping antibiotic names to predicted resistance status.
        Example: {"ciprofloxacin": "Resistant", "ampicillin": "Susceptible", ...}

    Raises:
        RuntimeError: If prediction fails for any reason.
    """
    try:
        return predict_from_genes(genes)
    except Exception as e:
        raise RuntimeError(f"ML prediction failed: {e}") from e
