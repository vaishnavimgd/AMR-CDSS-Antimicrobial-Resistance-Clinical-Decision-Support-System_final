"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    """Schema for a successful FASTA file upload response."""

    file_id: str
    filename: str
    num_sequences: int
    genes_detected: list[int]
    predictions: dict[str, str]
    warnings: list[str]
    anomaly: bool
    message: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
