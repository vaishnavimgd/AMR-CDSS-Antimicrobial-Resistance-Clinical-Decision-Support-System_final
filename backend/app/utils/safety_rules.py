"""
Clinical Safety Rule Engine.

Applies hard-coded clinical rules that override ML predictions when specific
high-risk gene patterns are detected. This is a critical safety layer that
ensures dangerous resistance patterns are never under-reported.
"""


# ─── Rule Definitions ────────────────────────────────────────────────────────
# Each rule is a dict with:
#   gene_index  — index in the gene vector to check
#   condition   — value that triggers the rule (1 = gene present)
#   antibiotic  — which prediction to override
#   override_to — forced prediction value
#   warning     — message added to the warnings list

SAFETY_RULES = [
    {
        "gene_index": 0,
        "condition": 1,
        "antibiotic": "ciprofloxacin",
        "override_to": "Resistant",
        "warning": "Critical resistance gene (blaTEM-1) detected — ciprofloxacin forced to Resistant.",
    },
    {
        "gene_index": 1,
        "condition": 1,
        "antibiotic": "ampicillin",
        "override_to": "Resistant",
        "warning": "Critical resistance gene (mecA) detected — ampicillin forced to Resistant.",
    },
    {
        "gene_index": 4,
        "condition": 1,
        "antibiotic": "tetracycline",
        "override_to": "Resistant",
        "warning": "Critical resistance gene (aac(6')) detected — tetracycline forced to Resistant.",
    },
]


def apply_safety_rules(
    genes: list[int], predictions: dict
) -> tuple[dict, list[str]]:
    """
    Apply clinical safety rules to override ML predictions when necessary.

    Args:
        genes: Binary gene presence vector from the scanner.
        predictions: ML model predictions (antibiotic → dict with prediction and confidence).

    Returns:
        Tuple of (updated_predictions, warnings).
    """
    updated = dict(predictions)  # shallow copy
    warnings: list[str] = []

    for rule in SAFETY_RULES:
        idx = rule["gene_index"]

        # Guard against index out of range
        if idx >= len(genes):
            continue

        if genes[idx] == rule["condition"]:
            antibiotic = rule["antibiotic"]

            current_info = updated.get(antibiotic, {})
            current_pred = current_info.get("prediction", "") if isinstance(current_info, dict) else str(current_info)
            
            # Only override if the current prediction is less severe
            if current_pred != rule["override_to"]:
                updated[antibiotic] = {
                    "prediction": rule["override_to"],
                    "confidence": 100.0
                }
                warnings.append(rule["warning"])

    return updated, warnings
