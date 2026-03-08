"""
Gene Scanner Runner — subprocess wrapper for the C++ gene scanner.

Calls the compiled gene_scanner.exe executable, passing a FASTA file path,
and parses the comma-separated binary output into a Python list of integers.
"""

import os
import subprocess

from app.config import GENE_SCANNER_PATH


def run_gene_scanner(file_path: str) -> list[int]:
    """
    Execute the C++ gene scanner on a FASTA file and return the gene presence vector.

    Args:
        file_path: Absolute path to the saved FASTA file.

    Returns:
        A list of integers (0 or 1) representing gene presence.
        Example: [1, 0, 1, 0, 0]

    Raises:
        FileNotFoundError: If the gene_scanner executable is missing.
        RuntimeError: If the scanner exits with an error or produces invalid output.
    """

    # ── Verify executable exists ────────────────────────────────────────
    if not os.path.isfile(GENE_SCANNER_PATH):
        raise FileNotFoundError(
            f"Gene scanner executable not found at '{GENE_SCANNER_PATH}'. "
            "Please compile gene_scanner.cpp first."
        )

    # ── Run the C++ scanner ─────────────────────────────────────────────
    try:
        result = subprocess.run(
            [GENE_SCANNER_PATH, file_path],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,  # Safety timeout for very large files
        )
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.strip() if e.stderr else "Unknown error"
        raise RuntimeError(
            f"Gene scanner failed (exit code {e.returncode}): {stderr_msg}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            "Gene scanner timed out. The file may be too large."
        ) from e

    # ── Parse output ────────────────────────────────────────────────────
    raw_output = result.stdout.strip()

    if not raw_output:
        raise RuntimeError("Gene scanner produced no output.")

    try:
        gene_vector = [int(x) for x in raw_output.split(",")]
    except ValueError as e:
        raise RuntimeError(
            f"Gene scanner output is not valid. Expected comma-separated integers, "
            f"got: '{raw_output}'"
        ) from e

    return gene_vector
