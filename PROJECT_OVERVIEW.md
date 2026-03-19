# AMR-CDSS — Antimicrobial Resistance Clinical Decision Support System

## What is This?

**AMR-CDSS** is an AI-powered clinical decision support system that helps healthcare professionals
quickly identify antimicrobial resistance (AMR) patterns in bacterial samples and receive
evidence-based antibiotic recommendations.

Antimicrobial resistance is one of the greatest global health threats — bacteria are evolving
to resist the antibiotics used to treat them. This system provides clinicians with a fast,
data-driven tool to make smarter prescribing decisions.

---

## The Dashboard — What You See

When you open the dashboard at `http://localhost:8000`, you'll find four main sections:

### 📁 Upload Dataset
Upload a **CSV/Excel file** containing patient or genomic data for a batch preview,
or upload a **FASTA genome file** (.fasta / .fa) for full AMR analysis:
- The genome is scanned by a C++ gene scanner for known resistance genes
- The ML model predicts resistance to specific antibiotics
- Clinical safety rules are applied on top of the predictions
- An anomaly detector flags any unusual gene patterns

### 🧑‍⚕️ Patient Input Form
Enter individual patient details directly:
- **Age**, **Gender**, **Species** (E. coli / S. aureus / C. diff)
- **Antibiotic being considered**, **Hospital stay duration**, **Prior antibiotic use**

The form submits to the ML model and returns resistance predictions instantly.

### 🔬 Model Prediction Output
After any submission (form or file), the results panel shows:
- **Resistance/Susceptibility** verdict per antibiotic, with confidence %
- **Antibiotic Stewardship Card** — WHO AWaRe-based recommendations:
  - ✅ Recommended antibiotics
  - ❌ Antibiotics to avoid
  - 🏷️ WHO Category: Access / Watch / Reserve
- **⚠️ Outbreak Alert Banner** — if 3+ matching resistance profiles appear
  in the same ward within 7 days, a red banner fires automatically

### 📊 Analytics Dashboard
Four real-time charts powered by Chart.js:
| Chart | What it shows |
|-------|--------------|
| Infection Distribution | Breakdown by species |
| Antibiotic Usage | Prescription frequency |
| Resistance Trends | Monthly resistance % over 6 months |
| Model Accuracy | Accuracy per species (Radar chart) |

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🧬 Gene Scanning | C++ executable scans FASTA genomes for resistance genes |
| 🤖 ML Prediction | 25 trained Random Forest models (per species × antibiotic) |
| 💊 Stewardship | WHO AWaRe guideline recommendations (10 clinical rules) |
| 🚨 Outbreak Alerts | Real-time in-session outbreak detection (3+ cases / 7 days) |
| 📊 Analytics | Live Chart.js visualizations |
| 🔒 Safety Rules | Clinical override layer on top of ML predictions |
| 🔍 Anomaly Detection | Flags novel/unusual gene patterns for manual review |

---

## Supported Species & Antibiotics

| Species | Antibiotics Modelled |
|---------|---------------------|
| *Escherichia coli* | Ampicillin, Ciprofloxacin, Ceftriaxone, Tetracycline, Gentamicin, + 9 more |
| *Staphylococcus aureus* | Methicillin, Vancomycin, Ciprofloxacin, Clindamycin, + 2 more |
| *Clostridioides difficile* | Azithromycin, Clindamycin, Moxifloxacin, + 2 more |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend API** | Python · FastAPI · Uvicorn |
| **Machine Learning** | scikit-learn · Random Forest (25 models) · joblib |
| **Gene Scanner** | C++ compiled executable |
| **Frontend** | HTML5 · Vanilla CSS · Vanilla JavaScript |
| **Charts** | Chart.js (CDN) |
| **Data** | pandas · numpy · openpyxl |

---

## Project Structure

```
final_amr/
├── main.py                    ← Single command launcher (opens browser + starts server)
├── requirements.txt           ← Python dependencies
├── frontend/
│   ├── amr_dashboard.html     ← Dashboard UI
│   ├── script.js              ← All frontend logic & API calls
│   └── style.css              ← Dark-mode design system
├── backend/
│   ├── gene_scanner.exe       ← Compiled C++ gene scanner
│   └── app/
│       ├── main.py            ← FastAPI app setup
│       ├── routes/
│       │   ├── dashboard.py   ← /predict, /analytics, /outbreak-status endpoints
│       │   └── upload.py      ← /upload-fasta endpoint (full pipeline)
│       └── utils/
│           ├── stewardship.py      ← WHO AWaRe recommendation engine
│           ├── outbreak_tracker.py ← In-session outbreak detection
│           ├── safety_rules.py     ← Clinical override rules
│           └── anomaly_detector.py ← Novel strain detection
└── model/
    ├── predict.py             ← ML inference interface
    └── model_*.pkl            ← 25 trained Random Forest models
```

---

## How to Run

```bash
# Install dependencies (once)
pip install -r requirements.txt

# Start the system
python main.py
```

This opens the dashboard automatically at **http://localhost:8000**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload-fasta` | Upload genome file for full AMR analysis |
| `POST` | `/api/dashboard/predict` | Patient form prediction |
| `POST` | `/api/dashboard/upload_dataset` | CSV/Excel dataset preview |
| `GET`  | `/api/dashboard/analytics` | Analytics data for charts |
| `GET`  | `/api/dashboard/outbreak-status` | Current active outbreak alerts |
| `GET`  | `/health` | Server health check |

---

## Clinical Context

This system is designed as a **decision support tool** — it augments, not replaces, clinical judgment.
All recommendations are based on:
- **WHO AWaRe Guidelines** (Access / Watch / Reserve antibiotic classification)
- **Machine learning models** trained on publicly available AMR genomic datasets
- **Clinical safety rules** that override ML predictions when warranted

> ⚠️ This is a research/academic prototype. It is **not** approved for clinical use without
> proper validation and regulatory review.
