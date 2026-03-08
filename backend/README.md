# AMR Prediction Backend

Backend API for the **Antimicrobial Resistance (AMR)** prediction system. This server accepts bacterial genome files in FASTA format, validates them, scans for resistance genes using a high-speed C++ engine, and returns gene detection results.

## Project Overview

Antimicrobial Resistance is a global health crisis. Doctors typically wait 24–72 hours for culture-based tests. This system uses AI to predict antibiotic resistance from genome data in under a minute.

### Architecture

```
Doctor → Streamlit Frontend → FastAPI Backend → C++ Gene Scanner → AI Model → Results
```

### Data Flow

1. Doctor uploads a `.fasta` genome file
2. FastAPI validates the file format
3. FastAPI calls `gene_scanner.exe` via subprocess
4. C++ scanner outputs a binary gene presence vector (e.g. `1,0,1,0,0`)
5. FastAPI parses the output and returns JSON results

## Quick Start

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Compile the C++ gene scanner

Make sure `g++` is available on your system, then run:

```bash
g++ -O2 -std=c++17 gene_scanner.cpp -o gene_scanner.exe
```

The compiled `gene_scanner.exe` must be in the project root directory.

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

The server will start at **http://127.0.0.1:8000**.

### 4. Test via Swagger UI

Open your browser and navigate to:

```
http://127.0.0.1:8000/docs
```

Use the interactive interface to:

- **GET /** — Health check (returns `{"status": "ok"}`)
- **POST /upload-fasta** — Upload a genome file → returns gene detection results

Example response:

```json
{
  "file_id": "uuid-string",
  "filename": "sample.fasta",
  "num_sequences": 2,
  "genes_detected": [1, 1, 0, 0, 0],
  "message": "File uploaded and scanned successfully."
}
```

### 5. Test via cURL

```bash
# Health check
curl http://127.0.0.1:8000/

# Upload a FASTA file
curl -X POST http://127.0.0.1:8000/upload-fasta -F "file=@test.fasta"
```

## Project Structure

```
hackbio/
├── gene_scanner.cpp         # C++ gene scanner source
├── gene_scanner.exe         # Compiled scanner (must be in root)
├── model.pkl                # Trained ML model (must be in root)
├── create_dummy_model.py    # Script to generate a test model
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, health check
│   ├── config.py            # Upload dir, size limits, scanner/model paths
│   ├── routes/
│   │   └── upload.py        # POST /upload-fasta endpoint
│   ├── utils/
│   │   ├── fasta_validator.py      # FASTA format validation
│   │   ├── gene_scanner_runner.py  # Subprocess wrapper for C++ scanner
│   │   └── model_runner.py         # ML model loader and predictor
│   └── models/
│       └── schemas.py       # Pydantic response models
├── uploads/                 # Stored uploaded files (auto-created)
├── requirements.txt
└── README.md
```

## Configuration

| Setting              | Value                       |
|----------------------|-----------------------------|
| Max file size        | 10 MB                       |
| Allowed extensions   | `.fasta`, `.fa`, `.fna`     |
| Upload directory     | `uploads/`                  |
| Gene scanner path    | `gene_scanner.exe` (root)   |
| ML model path        | `model.pkl` (root)          |
| Scanner timeout      | 30 seconds                  |

## ML Model

The model predicts resistance for three antibiotics: **Ciprofloxacin**, **Ampicillin**, **Tetracycline**.

To generate a test model: `python create_dummy_model.py`

The model is loaded once at first request and cached in memory for performance.

## Safety Rules

Clinical safety rules automatically override ML predictions when high-risk gene patterns are detected. Rules only **escalate** severity — they never downgrade a prediction. Current rules:

| Gene Detected | Antibiotic Forced To | Warning |
|---------------|---------------------|---------|
| blaTEM-1 (index 0) | Ciprofloxacin → Resistant | Critical resistance gene detected |
| mecA (index 1) | Ampicillin → Resistant | Critical resistance gene detected |
| aac(6') (index 4) | Tetracycline → Resistant | Critical resistance gene detected |

## Anomaly Detection

Flags unusual gene patterns that may indicate novel or unknown bacterial strains:

- **High resistance threshold**: ≥4 genes active simultaneously
- **Unknown profile**: gene pattern not seen in training data

When an anomaly is detected, `anomaly: true` is returned and a warning recommends manual verification.
