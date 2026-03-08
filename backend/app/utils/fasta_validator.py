"""
FASTA file format validator.

Validates that uploaded content conforms to the FASTA specification:
  - Starts with a header line beginning with '>'
  - Sequence lines contain only valid nucleotide characters (A, T, G, C, N)
  - At least one complete sequence (header + sequence data) is present
"""

import re


# Valid nucleotide characters (case-insensitive) plus whitespace
_VALID_SEQUENCE_PATTERN = re.compile(r"^[ATGCNatgcn\s]*$")


def validate_fasta(content: str) -> tuple[bool, int, str]:
    """
    Validate FASTA-formatted content.

    Args:
        content: The raw text content of the uploaded file.

    Returns:
        A tuple of (is_valid, sequence_count, error_message).
        - is_valid: True if the content is valid FASTA format.
        - sequence_count: Number of sequences found (0 if invalid).
        - error_message: Empty string if valid; describes the problem otherwise.
    """
    if not content or not content.strip():
        return False, 0, "File is empty."

    lines = content.splitlines()

    # ── Check that the file starts with a FASTA header ──────────────────
    first_non_empty = next((line for line in lines if line.strip()), None)
    if first_non_empty is None or not first_non_empty.strip().startswith(">"):
        return False, 0, "Invalid FASTA format: file must start with a '>' header line."

    sequence_count = 0
    has_sequence_data = False  # tracks whether current record has sequence lines

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            continue

        if stripped.startswith(">"):
            # If we were already inside a record, verify it had sequence data
            if sequence_count > 0 and not has_sequence_data:
                return (
                    False,
                    0,
                    f"Invalid FASTA format: header at line {line_number} has no preceding sequence data.",
                )
            sequence_count += 1
            has_sequence_data = False

            # Header line must have a description after '>'
            if len(stripped) < 2:
                return (
                    False,
                    0,
                    f"Invalid FASTA format: empty header at line {line_number}.",
                )
        else:
            # Sequence line — validate characters
            if not _VALID_SEQUENCE_PATTERN.match(stripped):
                return (
                    False,
                    0,
                    f"Invalid FASTA format: line {line_number} contains invalid characters. "
                    "Only A, T, G, C, N are allowed in sequence lines.",
                )
            has_sequence_data = True

    # ── Final checks ────────────────────────────────────────────────────
    if sequence_count == 0:
        return False, 0, "Invalid FASTA format: no sequences found."

    if not has_sequence_data:
        return False, 0, "Invalid FASTA format: last sequence has no sequence data."

    return True, sequence_count, ""
