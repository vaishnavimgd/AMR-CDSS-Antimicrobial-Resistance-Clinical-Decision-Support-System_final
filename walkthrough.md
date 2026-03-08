# AMR System Integration — Walkthrough

## Summary

Integrated three independent components (backend, frontend, ML model) into a single end-to-end AMR diagnostic pipeline. The system now runs as:

```
Doctor uploads FASTA → Frontend → Backend API → FASTA validation
→ C++ gene scanner → Gene vector → ML prediction (25+ classifiers)
→ Safety rules → Anomaly detection → JSON response → Frontend visualization
```

---

## Changes Made

### Task 1 & 5 — Backend → Model Connection + Import Paths

| File | Change |
|------|--------|
| [model_runner.py](file:///c:/Users/HP/Desktop/final_amr/backend/app/utils/model_runner.py) | **Rewritten** — delegates to `model.predict.predict_from_genes()` via `sys.path` injection |
| [predict.py](file:///c:/Users/HP/Desktop/final_amr/model/predict.py) | Fixed all [.pkl](file:///c:/Users/HP/Desktop/final_amr/backend/model.pkl) paths to use `os.path.dirname(__file__)` via `_MODEL_DIR` |
| [config.py](file:///c:/Users/HP/Desktop/final_amr/backend/app/config.py) | Added `MODEL_DIR` pointing to `model/` at project root |
| [model/\_\_init\_\_.py](file:///c:/Users/HP/Desktop/final_amr/model/__init__.py) | **New** — makes `model/` a Python package |
| [\_\_init\_\_.py](file:///c:/Users/HP/Desktop/final_amr/__init__.py) | **New** — makes project root importable |

```diff:model_runner.py
"""
ML Model Runner — loads the trained AMR prediction model and runs inference.

The model is loaded once at module import time (singleton pattern) so that
it stays in memory across requests, avoiding repeated disk I/O.
"""

import os

import joblib
import numpy as np

from app.config import MODEL_PATH

# ─── Antibiotic mapping ──────────────────────────────────────────────────────
# The model predicts a class for each of these antibiotics (in order).

ANTIBIOTICS: list[str] = ["ciprofloxacin", "ampicillin", "tetracycline"]

# Class labels produced by the model
RESISTANCE_LABELS: dict[int, str] = {
    0: "Susceptible",
    1: "Intermediate",
    2: "Resistant",
}

# ─── Model loading (singleton) ───────────────────────────────────────────────

_model = None


def _load_model():
    """Load the model from disk once and cache it in a module-level variable."""
    global _model
    if _model is not None:
        return _model

    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at '{MODEL_PATH}'. "
            "Please place a trained model.pkl in the project root."
        )

    _model = joblib.load(MODEL_PATH)
    return _model


def predict_resistance(genes: list[int]) -> dict[str, str]:
    """
    Predict antibiotic resistance from a gene presence vector.

    Args:
        genes: Binary list (e.g. [1, 0, 1, 0, 0]) from the gene scanner.

    Returns:
        Dictionary mapping antibiotic names to predicted resistance status.
        Example: {"ciprofloxacin": "Resistant", "ampicillin": "Susceptible", ...}

    Raises:
        FileNotFoundError: If model.pkl is missing.
        RuntimeError: If prediction fails for any reason.
    """
    model = _load_model()

    try:
        # Reshape to (1, n_features) for a single sample
        input_array = np.array(genes).reshape(1, -1)
        raw_predictions = model.predict(input_array)
    except Exception as e:
        raise RuntimeError(f"Model prediction failed: {e}") from e

    # Map numeric predictions to human-readable labels
    predictions: dict[str, str] = {}
    for i, antibiotic in enumerate(ANTIBIOTICS):
        class_id = int(raw_predictions[0][i])
        predictions[antibiotic] = RESISTANCE_LABELS.get(class_id, "Unknown")

    return predictions
===
"""
ML Model Runner — delegates to the real ML model in model/predict.py.

Adds the project root to sys.path so that `model.predict` can be imported,
then calls predict_from_genes() which loads 25+ trained classifiers across
three species and returns antibiotic resistance predictions.
"""

import os
import sys

# ─── Ensure the project root is on sys.path ──────────────────────────────────
# The project root is two levels up from this file:
#   this file : final_amr/backend/app/utils/model_runner.py
#   project root : final_amr/
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ─── Import from the real ML module ──────────────────────────────────────────
from model.predict import predict_from_genes  # noqa: E402


def predict_resistance(genes: list[int]) -> dict[str, str]:
    """
    Predict antibiotic resistance from a gene presence vector.

    Args:
        genes: Binary list (e.g. [1, 0, 1, 0, 0]) from the gene scanner.

    Returns:
        Dictionary mapping antibiotic names to predicted resistance status.
        Example: {"ciprofloxacin": "Resistant", "ampicillin": "Susceptible", ...}

    Raises:
        RuntimeError: If prediction fails for any reason.
    """
    try:
        return predict_from_genes(genes)
    except Exception as e:
        raise RuntimeError(f"ML prediction failed: {e}") from e

```

```diff:predict.py
# predict.py — FINAL VERSION
# Person 2 imports this: from predict import predict_resistance

import numpy as np
import joblib
import json
import os
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# CLINICAL SAFETY RULES
# ============================================================
SAFETY_RULES = {
    "meropenem":                    "🚨 Carbapenem resistance — last resort antibiotic compromised",
    "imipenem":                     "🚨 Carbapenem resistance — escalate to infectious disease specialist",
    "colistin":                     "🚨 Colistin resistance — pandrug resistance possible",
    "ciprofloxacin":                "⚠️  Fluoroquinolone resistance — avoid empirical use",
    "cefotaxime":                   "⚠️  3rd gen cephalosporin resistance — possible ESBL producer",
    "ceftazidime":                  "⚠️  3rd gen cephalosporin resistance — possible ESBL producer",
    "ceftriaxone":                  "⚠️  3rd gen cephalosporin resistance — possible ESBL producer",
    "methicillin":                  "🚨 MRSA detected — use vancomycin or linezolid",
    "vancomycin":                   "🚨 VRSA/VRE detected — extremely limited treatment options",
    "piperacillin/tazobactam":      "⚠️  Beta-lactam/inhibitor resistance detected",
    "amoxicillin/clavulanic acid":  "⚠️  Beta-lactam/inhibitor resistance detected",
    "trimethoprim/sulfamethoxazole":"⚠️  Sulfonamide resistance detected",
    "ampicillin":                   "⚠️  Penicillin resistance detected",
}

SPECIES_NAMES = {
    "ecoli":   "Escherichia coli",
    "saureus": "Staphylococcus aureus",
    "cdiff":   "Clostridioides difficile"
}

# Gene-index-to-antibiotic mapping for C++ scanner output
GENE_INDEX_MAP = {
    0: "ciprofloxacin",
    1: "ampicillin",
    2: "tetracycline",
    3: "gentamicin",
    4: "ceftriaxone",
}

# ============================================================
# LOAD ALL MODELS AT STARTUP
# ============================================================
print("Loading models...")

loaded_models     = {}
anomaly_detectors = {}
all_feature_names = {}

for species_key in ["ecoli", "saureus", "cdiff"]:
    try:
        antibiotics = joblib.load(f"antibiotics_{species_key}.pkl")
        anomaly_detectors[species_key] = joblib.load(f"anomaly_{species_key}.pkl")
        all_feature_names[species_key] = joblib.load(f"all_features_{species_key}.pkl")
    except FileNotFoundError:
        continue

    loaded_models[species_key] = {}
    for abx in antibiotics:
        safe_abx     = abx.replace("/", "_").replace(" ", "_")
        model_file   = f"model_{species_key}_{safe_abx}.pkl"
        feature_file = f"features_{species_key}_{safe_abx}.pkl"
        if os.path.exists(model_file) and os.path.exists(feature_file):
            loaded_models[species_key][abx] = {
                "model":    joblib.load(model_file),
                "features": joblib.load(feature_file)
            }

    count = len(loaded_models[species_key])
    print(f"  {SPECIES_NAMES.get(species_key)}: {count} models loaded")

print(f"Ready: {list(loaded_models.keys())}")


# ============================================================
# ADAPTER — convert gene vector from C++ scanner
# ============================================================

def gene_vector_to_phenotype(genes: list[int]) -> dict:
    """
    Convert a gene presence vector (from the C++ scanner) into
    the phenotype dictionary expected by predict_resistance().

    Args:
        genes: e.g. [1, 0, 1, 0, 0]
            Each position maps to an antibiotic via GENE_INDEX_MAP.
            Values: 1 = Resistant gene present,
                    0 = Susceptible / gene absent.
            Indices beyond the vector length default to -1 (unknown).

    Returns:
        e.g. {"ciprofloxacin": 1, "ampicillin": 0, "tetracycline": 1,
              "gentamicin": -1, "ceftriaxone": -1}
    """
    phenotype = {}
    for idx, antibiotic in GENE_INDEX_MAP.items():
        if idx < len(genes):
            phenotype[antibiotic] = genes[idx]
        else:
            phenotype[antibiotic] = -1  # unknown
    return phenotype


def predict_from_genes(gene_vector: list[int], species: str = "ecoli") -> dict:
    """
    End-to-end wrapper for the FastAPI backend.

    1. Converts the gene vector → phenotype dict
    2. Calls predict_resistance()
    3. Returns simplified output (label only, no confidence/SHAP)

    Args:
        gene_vector: e.g. [1, 0, 1, 0, 0]
        species:     "ecoli", "saureus", or "cdiff"

    Returns:
        {"ciprofloxacin": "Resistant", "ampicillin": "Susceptible", ...}
    """
    phenotype = gene_vector_to_phenotype(gene_vector)
    result    = predict_resistance(phenotype, species)

    if "error" in result:
        return result

    # Flatten to {antibiotic: label} — strip confidence, SHAP, etc.
    return {
        abx: info["prediction"]
        for abx, info in result["predictions"].items()
    }


# ============================================================
# PREDICT FUNCTION — Person 2 calls this
# ============================================================

def predict_resistance(phenotype_dict: dict, species: str = "ecoli") -> dict:
    """
    Args:
        phenotype_dict: known resistance values
            {"ciprofloxacin": 1, "ampicillin": 0}
            1=Resistant, 0=Susceptible, -1=Unknown

        species: "ecoli", "saureus", or "cdiff"

    Returns:
        JSON-compatible dict matching agreed contract
    """
    if species not in loaded_models:
        return {"error": f"Species '{species}' not available. Choose from: {list(loaded_models.keys())}"}

    models      = loaded_models[species]
    features    = all_feature_names[species]
    anomaly_det = anomaly_detectors[species]

    # Anomaly detection
    anomaly_input = np.array(
        [max(phenotype_dict.get(f, 0), 0) for f in features],
        dtype=float
    ).reshape(1, -1)

    anomaly_score = float(anomaly_det.decision_function(anomaly_input)[0])
    is_anomaly    = bool(anomaly_det.predict(anomaly_input)[0] == -1)

    # Predict each antibiotic
    predictions = {}
    warnings_list = []
    shap_values = {}

    for abx, info in models.items():
        model        = info["model"]
        feature_cols = info["features"]

        x = np.array(
            [phenotype_dict.get(f, -1) for f in feature_cols],
            dtype=float
        ).reshape(1, -1)

        prob       = float(model.predict_proba(x)[0][1])
        pred_label = "Resistant" if prob > 0.5 else "Susceptible"
        confidence = round(max(prob, 1 - prob), 3)

        predictions[abx] = {
            "prediction":            pred_label,
            "confidence":            confidence,
            "resistant_probability": round(prob, 3)
        }

        # Top features as SHAP proxy
        importances = model.feature_importances_
        top_idx     = np.argsort(importances)[::-1][:5]
        shap_values[abx] = {
            feature_cols[i]: round(float(importances[i]), 4)
            for i in top_idx
        }

        # Safety warnings
        if pred_label == "Resistant" and abx in SAFETY_RULES:
            warnings_list.append(SAFETY_RULES[abx])

    avg_confidence = round(
        float(np.mean([v["confidence"] for v in predictions.values()])), 3
    ) if predictions else 0.0

    # Final output — agreed JSON contract
    return {
        "species":       SPECIES_NAMES.get(species, species),
        "predictions":   predictions,
        "anomaly":       is_anomaly,
        "anomaly_score": round(anomaly_score, 3),
        "shap_values":   shap_values,
        "warnings":      list(set(warnings_list)),
        "confidence":    avg_confidence
    }


# ============================================================
# TESTS — run directly to verify
# ============================================================

if __name__ == "__main__":

    for species in ["ecoli", "saureus", "cdiff"]:
        if species not in loaded_models or not loaded_models[species]:
            continue

        abx_list = list(loaded_models[species].keys())
        print(f"\n{'='*60}")
        print(f"TESTS — {SPECIES_NAMES[species]}")
        print(f"{'='*60}")

        # Test 1: Superbug
        print("\n🔴 TEST 1: Superbug (all Resistant)")
        result = predict_resistance({abx: 1 for abx in abx_list}, species)
        for abx, pred in result["predictions"].items():
            symbol = "🔴" if pred["prediction"] == "Resistant" else "🟢"
            print(f"  {symbol} {abx:42s} {pred['prediction']:12s} conf:{pred['confidence']*100:.1f}%")
        print(f"  Anomaly: {result['anomaly']} | Warnings: {len(result['warnings'])}")

        # Test 2: Healthy
        print("\n🟢 TEST 2: Healthy (all Susceptible)")
        result = predict_resistance({abx: 0 for abx in abx_list}, species)
        for abx, pred in result["predictions"].items():
            symbol = "🔴" if pred["prediction"] == "Resistant" else "🟢"
            print(f"  {symbol} {abx:42s} {pred['prediction']:12s} conf:{pred['confidence']*100:.1f}%")
        print(f"  Anomaly: {result['anomaly']}")

        # Test 3: Alien
        print("\n👾 TEST 3: Unknown genome (empty input)")
        result = predict_resistance({}, species)
        print(f"  Anomaly detected: {result['anomaly']}")
        print(f"  Anomaly score:    {result['anomaly_score']}")

    # ----------------------------------------------------------
    # ADAPTER TEST — predict_from_genes
    # ----------------------------------------------------------
    print(f"\n{'='*60}")
    print("ADAPTER TEST — predict_from_genes([1, 0, 1, 0, 0])")
    print(f"{'='*60}")
    genes = [1, 0, 1, 0, 0]
    adapter_result = predict_from_genes(genes)
    for abx, label in adapter_result.items():
        symbol = "🔴" if label == "Resistant" else "🟢"
        print(f"  {symbol} {abx:42s} {label}")

    print("\n✅ predict.py working!")
    print("Backend: from predict import predict_from_genes")
===
# predict.py — FINAL VERSION
# Person 2 imports this: from predict import predict_resistance

import numpy as np
import joblib
import json
import os
import warnings

# Directory containing this file and all .pkl model artifacts
_MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
warnings.filterwarnings("ignore")

# ============================================================
# CLINICAL SAFETY RULES
# ============================================================
SAFETY_RULES = {
    "meropenem":                    "🚨 Carbapenem resistance — last resort antibiotic compromised",
    "imipenem":                     "🚨 Carbapenem resistance — escalate to infectious disease specialist",
    "colistin":                     "🚨 Colistin resistance — pandrug resistance possible",
    "ciprofloxacin":                "⚠️  Fluoroquinolone resistance — avoid empirical use",
    "cefotaxime":                   "⚠️  3rd gen cephalosporin resistance — possible ESBL producer",
    "ceftazidime":                  "⚠️  3rd gen cephalosporin resistance — possible ESBL producer",
    "ceftriaxone":                  "⚠️  3rd gen cephalosporin resistance — possible ESBL producer",
    "methicillin":                  "🚨 MRSA detected — use vancomycin or linezolid",
    "vancomycin":                   "🚨 VRSA/VRE detected — extremely limited treatment options",
    "piperacillin/tazobactam":      "⚠️  Beta-lactam/inhibitor resistance detected",
    "amoxicillin/clavulanic acid":  "⚠️  Beta-lactam/inhibitor resistance detected",
    "trimethoprim/sulfamethoxazole":"⚠️  Sulfonamide resistance detected",
    "ampicillin":                   "⚠️  Penicillin resistance detected",
}

SPECIES_NAMES = {
    "ecoli":   "Escherichia coli",
    "saureus": "Staphylococcus aureus",
    "cdiff":   "Clostridioides difficile"
}

# Gene-index-to-antibiotic mapping for C++ scanner output
GENE_INDEX_MAP = {
    0: "ciprofloxacin",
    1: "ampicillin",
    2: "tetracycline",
    3: "gentamicin",
    4: "ceftriaxone",
}

# ============================================================
# LOAD ALL MODELS AT STARTUP
# ============================================================
print("Loading models...")

loaded_models     = {}
anomaly_detectors = {}
all_feature_names = {}

for species_key in ["ecoli", "saureus", "cdiff"]:
    try:
        antibiotics = joblib.load(os.path.join(_MODEL_DIR, f"antibiotics_{species_key}.pkl"))
        anomaly_detectors[species_key] = joblib.load(os.path.join(_MODEL_DIR, f"anomaly_{species_key}.pkl"))
        all_feature_names[species_key] = joblib.load(os.path.join(_MODEL_DIR, f"all_features_{species_key}.pkl"))
    except FileNotFoundError:
        continue

    loaded_models[species_key] = {}
    for abx in antibiotics:
        safe_abx     = abx.replace("/", "_").replace(" ", "_")
        model_file   = os.path.join(_MODEL_DIR, f"model_{species_key}_{safe_abx}.pkl")
        feature_file = os.path.join(_MODEL_DIR, f"features_{species_key}_{safe_abx}.pkl")
        if os.path.exists(model_file) and os.path.exists(feature_file):
            loaded_models[species_key][abx] = {
                "model":    joblib.load(model_file),
                "features": joblib.load(feature_file)
            }

    count = len(loaded_models[species_key])
    print(f"  {SPECIES_NAMES.get(species_key)}: {count} models loaded")

print(f"Ready: {list(loaded_models.keys())}")


# ============================================================
# ADAPTER — convert gene vector from C++ scanner
# ============================================================

def gene_vector_to_phenotype(genes: list[int]) -> dict:
    """
    Convert a gene presence vector (from the C++ scanner) into
    the phenotype dictionary expected by predict_resistance().

    Args:
        genes: e.g. [1, 0, 1, 0, 0]
            Each position maps to an antibiotic via GENE_INDEX_MAP.
            Values: 1 = Resistant gene present,
                    0 = Susceptible / gene absent.
            Indices beyond the vector length default to -1 (unknown).

    Returns:
        e.g. {"ciprofloxacin": 1, "ampicillin": 0, "tetracycline": 1,
              "gentamicin": -1, "ceftriaxone": -1}
    """
    phenotype = {}
    for idx, antibiotic in GENE_INDEX_MAP.items():
        if idx < len(genes):
            phenotype[antibiotic] = genes[idx]
        else:
            phenotype[antibiotic] = -1  # unknown
    return phenotype


def predict_from_genes(gene_vector: list[int], species: str = "ecoli") -> dict:
    """
    End-to-end wrapper for the FastAPI backend.

    1. Converts the gene vector → phenotype dict
    2. Calls predict_resistance()
    3. Returns simplified output (label only, no confidence/SHAP)

    Args:
        gene_vector: e.g. [1, 0, 1, 0, 0]
        species:     "ecoli", "saureus", or "cdiff"

    Returns:
        {"ciprofloxacin": "Resistant", "ampicillin": "Susceptible", ...}
    """
    phenotype = gene_vector_to_phenotype(gene_vector)
    result    = predict_resistance(phenotype, species)

    if "error" in result:
        return result

    # Flatten to {antibiotic: label} — strip confidence, SHAP, etc.
    return {
        abx: info["prediction"]
        for abx, info in result["predictions"].items()
    }


# ============================================================
# PREDICT FUNCTION — Person 2 calls this
# ============================================================

def predict_resistance(phenotype_dict: dict, species: str = "ecoli") -> dict:
    """
    Args:
        phenotype_dict: known resistance values
            {"ciprofloxacin": 1, "ampicillin": 0}
            1=Resistant, 0=Susceptible, -1=Unknown

        species: "ecoli", "saureus", or "cdiff"

    Returns:
        JSON-compatible dict matching agreed contract
    """
    if species not in loaded_models:
        return {"error": f"Species '{species}' not available. Choose from: {list(loaded_models.keys())}"}

    models      = loaded_models[species]
    features    = all_feature_names[species]
    anomaly_det = anomaly_detectors[species]

    # Anomaly detection
    anomaly_input = np.array(
        [max(phenotype_dict.get(f, 0), 0) for f in features],
        dtype=float
    ).reshape(1, -1)

    anomaly_score = float(anomaly_det.decision_function(anomaly_input)[0])
    is_anomaly    = bool(anomaly_det.predict(anomaly_input)[0] == -1)

    # Predict each antibiotic
    predictions = {}
    warnings_list = []
    shap_values = {}

    for abx, info in models.items():
        model        = info["model"]
        feature_cols = info["features"]

        x = np.array(
            [phenotype_dict.get(f, -1) for f in feature_cols],
            dtype=float
        ).reshape(1, -1)

        prob       = float(model.predict_proba(x)[0][1])
        pred_label = "Resistant" if prob > 0.5 else "Susceptible"
        confidence = round(max(prob, 1 - prob), 3)

        predictions[abx] = {
            "prediction":            pred_label,
            "confidence":            confidence,
            "resistant_probability": round(prob, 3)
        }

        # Top features as SHAP proxy
        importances = model.feature_importances_
        top_idx     = np.argsort(importances)[::-1][:5]
        shap_values[abx] = {
            feature_cols[i]: round(float(importances[i]), 4)
            for i in top_idx
        }

        # Safety warnings
        if pred_label == "Resistant" and abx in SAFETY_RULES:
            warnings_list.append(SAFETY_RULES[abx])

    avg_confidence = round(
        float(np.mean([v["confidence"] for v in predictions.values()])), 3
    ) if predictions else 0.0

    # Final output — agreed JSON contract
    return {
        "species":       SPECIES_NAMES.get(species, species),
        "predictions":   predictions,
        "anomaly":       is_anomaly,
        "anomaly_score": round(anomaly_score, 3),
        "shap_values":   shap_values,
        "warnings":      list(set(warnings_list)),
        "confidence":    avg_confidence
    }


# ============================================================
# TESTS — run directly to verify
# ============================================================

if __name__ == "__main__":

    for species in ["ecoli", "saureus", "cdiff"]:
        if species not in loaded_models or not loaded_models[species]:
            continue

        abx_list = list(loaded_models[species].keys())
        print(f"\n{'='*60}")
        print(f"TESTS — {SPECIES_NAMES[species]}")
        print(f"{'='*60}")

        # Test 1: Superbug
        print("\n🔴 TEST 1: Superbug (all Resistant)")
        result = predict_resistance({abx: 1 for abx in abx_list}, species)
        for abx, pred in result["predictions"].items():
            symbol = "🔴" if pred["prediction"] == "Resistant" else "🟢"
            print(f"  {symbol} {abx:42s} {pred['prediction']:12s} conf:{pred['confidence']*100:.1f}%")
        print(f"  Anomaly: {result['anomaly']} | Warnings: {len(result['warnings'])}")

        # Test 2: Healthy
        print("\n🟢 TEST 2: Healthy (all Susceptible)")
        result = predict_resistance({abx: 0 for abx in abx_list}, species)
        for abx, pred in result["predictions"].items():
            symbol = "🔴" if pred["prediction"] == "Resistant" else "🟢"
            print(f"  {symbol} {abx:42s} {pred['prediction']:12s} conf:{pred['confidence']*100:.1f}%")
        print(f"  Anomaly: {result['anomaly']}")

        # Test 3: Alien
        print("\n👾 TEST 3: Unknown genome (empty input)")
        result = predict_resistance({}, species)
        print(f"  Anomaly detected: {result['anomaly']}")
        print(f"  Anomaly score:    {result['anomaly_score']}")

    # ----------------------------------------------------------
    # ADAPTER TEST — predict_from_genes
    # ----------------------------------------------------------
    print(f"\n{'='*60}")
    print("ADAPTER TEST — predict_from_genes([1, 0, 1, 0, 0])")
    print(f"{'='*60}")
    genes = [1, 0, 1, 0, 0]
    adapter_result = predict_from_genes(genes)
    for abx, label in adapter_result.items():
        symbol = "🔴" if label == "Resistant" else "🟢"
        print(f"  {symbol} {abx:42s} {label}")

    print("\n✅ predict.py working!")
    print("Backend: from predict import predict_from_genes")
```

### Tasks 2, 3, 4 — Gene Scanner, Model Adapter, Frontend

All verified working without changes:
- **Gene scanner**: [gene_scanner_runner.py](file:///c:/Users/HP/Desktop/final_amr/backend/app/utils/gene_scanner_runner.py) calls `gene_scanner.exe <fasta>`, parses `1,0,1,0,0` output
- **Model adapter**: [predict_from_genes()](file:///c:/Users/HP/Desktop/final_amr/model/predict.py#111-137) converts gene vector → phenotype → ML inference
- **Frontend**: [app.py](file:///c:/Users/HP/Desktop/final_amr/frontend/app.py) sends to `POST /upload-fasta`, parses `predictions`, `genes_detected`, `warnings`, [anomaly](file:///c:/Users/HP/Desktop/final_amr/backend/app/utils/anomaly_detector.py#29-51)

### Task 6 — Unified Requirements

[requirements.txt](file:///c:/Users/HP/Desktop/final_amr/requirements.txt) — covers backend, ML, and frontend.

### Task 8 — End-to-End Test

[test_integration.py](file:///c:/Users/HP/Desktop/final_amr/test_integration.py) — automated test that starts backend, uploads FASTA, validates response.

---

## Verification Results

### Backend Startup
- Models loaded: **E. coli (14), S. aureus (6), C. difficile (5)** — 25 total classifiers
- Server runs on `http://127.0.0.1:8000`

### API Test — `POST /upload-fasta` with [test.fasta](file:///c:/Users/HP/Desktop/final_amr/backend/test.fasta)

```json
{
  "file_id": "1e94f200-2050-4ce8-9662-9ade916af70d",
  "filename": "test.fasta",
  "num_sequences": 2,
  "genes_detected": [1, 1, 0, 0, 0],
  "predictions": {
    "ampicillin": "Resistant",
    "ciprofloxacin": "Resistant",
    "amoxicillin/clavulanic acid": "Susceptible",
    "cefotaxime": "Susceptible",
    "trimethoprim/sulfamethoxazole": "Resistant",
    "ceftazidime": "Resistant",
    "tetracycline": "Resistant",
    "gentamicin": "Resistant",
    "ceftriaxone": "Susceptible",
    "trimethoprim": "Resistant",
    "cefuroxime": "Susceptible",
    "nalidixic acid": "Susceptible",
    "chloramphenicol": "Resistant",
    "piperacillin/tazobactam": "Susceptible"
  },
  "warnings": [
    "Critical resistance gene (blaTEM-1) detected — ciprofloxacin forced to Resistant."
  ],
  "anomaly": false,
  "message": "File uploaded, scanned, and analyzed successfully."
}
```

### Integration Test Script
- **Exit code**: 0 (all checks passed)

---

## Runtime Instructions

**Backend:**
```bash
cd c:\Users\HP\Desktop\final_amr\backend
python -m uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd c:\Users\HP\Desktop\final_amr\frontend
streamlit run app.py
```

**Integration Test:**
```bash
cd c:\Users\HP\Desktop\final_amr
python test_integration.py
```

---

## Final Folder Structure

```
final_amr/
├── __init__.py                    ← NEW
├── requirements.txt               ← NEW (unified)
├── test_integration.py            ← NEW
├── api_response.json              ← test output
├── backend/
│   ├── requirements.txt
│   ├── gene_scanner.exe
│   ├── gene_scanner.cpp
│   ├── model.pkl                  (legacy, no longer used)
│   ├── test.fasta
│   ├── uploads/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py              ← MODIFIED
│       ├── models/
│       │   ├── __init__.py
│       │   └── schemas.py
│       ├── routes/
│       │   ├── __init__.py
│       │   └── upload.py
│       └── utils/
│           ├── __init__.py
│           ├── anomaly_detector.py
│           ├── fasta_validator.py
│           ├── gene_scanner_runner.py
│           ├── model_runner.py    ← REWRITTEN
│           └── safety_rules.py
├── frontend/
│   └── app.py
└── model/
    ├── __init__.py                ← NEW
    ├── predict.py                 ← MODIFIED
    ├── train_model.py
    ├── prepare_data.py
    ├── explore_data.py
    ├── *.pkl                      (25 model files + features + anomaly detectors)
    └── *.csv                      (training data)
```
