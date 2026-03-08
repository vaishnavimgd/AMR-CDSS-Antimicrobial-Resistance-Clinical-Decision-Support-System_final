"""
Anomaly Detector — flags unusual gene patterns that may indicate
unknown or novel bacterial strains.

Uses a simple heuristic approach:
  - Flags if too many resistance genes are detected simultaneously
  - Flags if the gene pattern doesn't match any known profile
"""

# ─── Known Gene Profiles ─────────────────────────────────────────────────────
# Common resistance profiles seen in training data.
# If a sample doesn't match any known profile, it's flagged as anomalous.

KNOWN_PROFILES: list[tuple[int, ...]] = [
    (1, 1, 0, 0, 0),
    (0, 0, 0, 0, 0),
    (1, 0, 1, 0, 0),
    (0, 1, 0, 1, 0),
    (1, 1, 1, 1, 1),
    (0, 0, 1, 0, 1),
    (1, 0, 0, 1, 0),
    (0, 1, 1, 0, 0),
]

# If this many or more genes are active, flag as anomalous regardless
HIGH_RESISTANCE_THRESHOLD: int = 4


def detect_anomaly(genes: list[int]) -> bool:
    """
    Determine whether a gene vector represents an anomalous (potentially novel) strain.

    Args:
        genes: Binary gene presence vector from the scanner.

    Returns:
        True if the sample is flagged as anomalous, False otherwise.
    """

    # Rule 1: Unusually high number of resistance genes
    active_genes = sum(genes)
    if active_genes >= HIGH_RESISTANCE_THRESHOLD:
        return True

    # Rule 2: Gene pattern not seen in training data
    gene_tuple = tuple(genes)
    if gene_tuple not in KNOWN_PROFILES:
        return True

    return False
