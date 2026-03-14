"""
Configuration settings for the AMR Backend application.
"""

import os

# ─── Upload Settings ─────────────────────────────────────────────────────────

# Directory where uploaded FASTA files are stored
UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

# Maximum allowed file size in bytes (10 MB)
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

# Accepted file extensions for FASTA uploads
ALLOWED_EXTENSIONS: list[str] = [".fasta", ".fa", ".fna"]

# ─── Gene Scanner Settings ───────────────────────────────────────────────────

# Path to the compiled C++ gene scanner executable
_scanner_filename = "gene_scanner.exe" if os.name == "nt" else "gene_scanner"
GENE_SCANNER_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), _scanner_filename
)

# ─── ML Model Settings ──────────────────────────────────────────────────────

# Path to the trained prediction model (legacy — kept for reference)
MODEL_PATH: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model.pkl"
)

# Directory containing the real ML models (model/ at project root)
MODEL_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "model"
)
