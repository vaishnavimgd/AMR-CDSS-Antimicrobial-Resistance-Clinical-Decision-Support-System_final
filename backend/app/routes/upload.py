"""
Upload route — handles FASTA uploads, gene scanning, ML prediction, safety rules, and anomaly detection.
"""

import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR
from app.models.schemas import UploadResponse
from app.utils.fasta_validator import validate_fasta
from app.utils.gene_scanner_runner import run_gene_scanner
from app.utils.model_runner import predict_resistance
from app.utils.safety_rules import apply_safety_rules
from app.utils.anomaly_detector import detect_anomaly

router = APIRouter()


@router.post(
    "/upload-fasta",
    response_model=UploadResponse,
    summary="Upload a FASTA genome file",
    description=(
        "Accepts a FASTA (.fasta, .fa, .fna) genome file, validates its format, "
        "stores it, runs the C++ gene scanner, predicts antibiotic resistance, "
        "applies clinical safety rules, and performs anomaly detection."
    ),
)
async def upload_fasta(file: UploadFile = File(..., description="FASTA genome file")):
    """
    Upload and validate a FASTA genome file.

    Steps:
        1. Check file extension is among the allowed types.
        2. Read file content and enforce the size limit.
        3. Validate FASTA format (headers, nucleotide characters, sequences).
        4. Save the file with a UUID-prefixed name.
        5. Run the C++ gene scanner on the saved file.
        6. Run the ML model to predict antibiotic resistance.
        7. Apply clinical safety rule overrides.
        8. Run anomaly detection.
        9. Return final results.
    """

    # ── 1. Validate file extension ──────────────────────────────────────
    filename = file.filename or "unknown"
    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid file extension '{extension}'. "
                f"Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
            ),
        )

    # ── 2. Read content and validate size ───────────────────────────────
    content_bytes = await file.read()

    if len(content_bytes) > MAX_FILE_SIZE:
        size_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the maximum allowed size of {size_mb:.0f} MB.",
        )

    content = content_bytes.decode("utf-8", errors="replace")

    # ── 3. Validate FASTA format ────────────────────────────────────────
    is_valid, num_sequences, error_message = validate_fasta(content)

    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # ── 4. Save file ────────────────────────────────────────────────────
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # ── 5. Run gene scanner ──────────────────────────────────────────────
    try:
        genes_detected = run_gene_scanner(file_path)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gene scanner not available: {e}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gene scanning failed: {e}",
        )

    # ── 6. Run ML prediction ────────────────────────────────────────────
    try:
        predictions = predict_resistance(genes_detected)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction model not available: {e}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {e}",
        )

    # ── 7. Apply safety rules ───────────────────────────────────────────
    predictions, warnings = apply_safety_rules(genes_detected, predictions)

    # ── 8. Anomaly detection ────────────────────────────────────────────
    anomaly = detect_anomaly(genes_detected)
    if anomaly:
        warnings.append(
            "Anomaly detected: gene pattern may indicate a novel or unknown strain. "
            "Manual verification recommended."
        )

    # ── 9. Return response ──────────────────────────────────────────────
    return UploadResponse(
        file_id=file_id,
        filename=filename,
        num_sequences=num_sequences,
        genes_detected=genes_detected,
        predictions=predictions,
        warnings=warnings,
        anomaly=anomaly,
        message="File uploaded, scanned, and analyzed successfully.",
    )
