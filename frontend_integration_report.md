# 🧬 AMR Prediction Dashboard — Frontend Technical Summary

## 1. Framework

**Streamlit** (Python-based web framework for data applications). The entire frontend is a single-page Streamlit app with custom HTML/CSS injected via `st.markdown(unsafe_allow_html=True)`.

---

## 2. Folder Structure

```
amr/
└── frontend/
    └── app.py          ← sole frontend file (168 lines, 7.4 KB)
```

> [!NOTE]
> The frontend consists of a single file with no additional assets, configs, or sub-modules.

---

## 3. Entry Point

[app.py](file:///c:/Users/HP/Desktop/amr/frontend/app.py) — executed with:

```bash
streamlit run frontend/app.py
```

Page config is set on [line 9](file:///c:/Users/HP/Desktop/amr/frontend/app.py#L9):
```python
st.set_page_config(page_title="🧬 AMR Prediction Dashboard", layout="wide", initial_sidebar_state="expanded")
```

---

## 4. FASTA File Upload & API Call

### File Upload Widget ([lines 40–44](file:///c:/Users/HP/Desktop/amr/frontend/app.py#L40-L44))

```python
uploaded_file = st.file_uploader(
    "📂 Upload FASTA File",
    type=["fasta", "fa", "txt"],
    help="Drag & drop FASTA file. Max 200MB."
)
```

### API Call ([lines 48–56](file:///c:/Users/HP/Desktop/amr/frontend/app.py#L48-L56))

```python
files = {'file': (uploaded_file.name, uploaded_file, 'text/plain')}

api_url = "http://127.0.0.1:8000/analyze"
response = requests.post(api_url, files=files)
result = response.json()
```

| Detail | Value |
|---|---|
| **Method** | `POST` |
| **Endpoint** | `http://127.0.0.1:8000/analyze` |
| **Content type** | `multipart/form-data` (file upload) |
| **Form field** | `file` |

---

## 5. Expected Backend Response Format

The frontend reads these keys from the JSON response:

```json
{
  "summary": {
    "sequences_analyzed": 1,
    "genes_detected": 3,
    "highest_score": 0.9
  },
  "prediction": {
    "Ciprofloxacin": "Resistant",
    "Ampicillin": "Susceptible",
    "Tetracycline": "Resistant"
  },
  "gene_scores": {
    "geneA": 0.6,
    "geneB": 0.59,
    "geneC": 0.592
  },
  "anomaly": false
}
```

| Key | Type | Purpose |
|---|---|---|
| `summary` | `dict` | Numeric KPIs (sequences, genes, score) |
| `prediction` | `dict` | Per-antibiotic resistance status (`"Resistant"` / `"Susceptible"`) |
| `gene_scores` | `dict` | Per-gene importance scores (float) |
| `anomaly` | `bool` | Zero-day threat flag |

---

## 6. Prediction Display Components

The dashboard uses **5 tabbed views**:

| Tab | Visualization | Library | What it Shows |
|---|---|---|---|
| **Summary** | Colored status cards (HTML) | Custom CSS | KPI metrics (sequences, genes, score) |
| **Antibiotics** | Resistant / Susceptible cards | Custom CSS | Per-antibiotic status with gradient colors |
| **Gene Scores** | Bar chart, Bubble chart, Line chart | Altair | Gene importance scores |
| **SHAP Heatmap** | Heatmap (Gene × Antibiotic) | Altair | SHAP feature-attribution values |
| **Pie Chart** | Arc chart | Altair | Resistant vs Susceptible proportion |

### Card Styling
- **Resistant** → red gradient (`#FF416C → #FF4B2B`)
- **Susceptible** → green gradient (`#43e97b → #38f9d7`)
- **Anomaly alert** → `st.error()` banner when `anomaly == true`

---

## 7. Loading States & Progress Indicators

Two sequential `st.spinner()` calls on [lines 52–55](file:///c:/Users/HP/Desktop/amr/frontend/app.py#L52-L55):

```python
with st.spinner("⚙️ Initializing C++ Extraction Engine..."):
    pass  # decorative — no actual work
with st.spinner("🤖 Running PyTorch Inference..."):
    response = requests.post(api_url, files=files)  # actual API call
```

> [!NOTE]
> The first spinner is cosmetic (empty `pass`). The second spinner wraps the real `requests.post` call.

---

## 8. Dependencies

No `requirements.txt` exists in the project. Based on imports in [app.py](file:///c:/Users/HP/Desktop/amr/frontend/app.py):

| Package | Import | Purpose |
|---|---|---|
| `streamlit` | `import streamlit as st` | UI framework |
| `requests` | `import requests` | HTTP client for backend API |
| `pandas` | `import pandas as pd` | DataFrames for chart data |
| `altair` | `import altair as alt` | Declarative charting |
| `numpy` | `import numpy as np` | SHAP heatmap random data generation |

Install all with:
```bash
pip install streamlit requests pandas altair numpy
```

---

## 9. How to Start the Frontend

```bash
cd c:\Users\HP\Desktop\amr
streamlit run frontend/app.py
```

The app opens at **`http://localhost:8501`** by default.

---

## 10. Configured Backend URL

Defined on [line 51](file:///c:/Users/HP/Desktop/amr/frontend/app.py#L51):

```python
api_url = "http://127.0.0.1:8000/analyze"
```

| Setting | Value |
|---|---|
| **Host** | `127.0.0.1` (localhost) |
| **Port** | `8000` |
| **Endpoint** | `/analyze` |
| **Full URL** | `http://127.0.0.1:8000/analyze` |

> [!IMPORTANT]
> The URL is **hard-coded**. To change it, edit line 51 of [app.py](file:///c:/Users/HP/Desktop/amr/frontend/app.py) directly. There is no environment variable or config file abstraction.
