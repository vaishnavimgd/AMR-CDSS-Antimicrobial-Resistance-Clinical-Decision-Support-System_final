import sys
import os
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from model.predict import predict_resistance

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

class PatientData(BaseModel):
    age: int
    gender: str
    species: str
    antibiotic: str
    hospital_stay: Optional[int] = 0
    previous_antibiotic: Optional[str] = "No"

@router.post("/predict")
async def predict(data: PatientData):
    """
    Endpoint for patient form prediction test.
    Maps patient form entries to the ML model.
    """
    phenotype = {
        "age": data.age,
        "hospital_stay": data.hospital_stay,
    }
    
    try:
        result = predict_resistance(phenotype, data.species)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
        
    predictions = result.get("predictions", {})
    
    formatted_results = {}
    if predictions:
        for abx_name, abx_data in predictions.items():
            formatted_results[abx_name] = {
                "prediction": abx_data.get("prediction", "Unknown"),
                "confidence": abx_data.get("confidence", 0.0)
            }
    else:
        # Fallback if no specific antibiotics
        formatted_results[data.antibiotic] = {"prediction": "Unknown", "confidence": 0.0}

    return {
        "status": "success",
        "results": formatted_results
    }

@router.post("/upload_dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Endpoint to receive a CSV/Excel dataset and return a preview.
    """
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif file.filename.endswith((".xls", ".xlsx")):
            # Requires openpyxl installed
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported for tabular datasets.")
            
        # Get first 5 rows and replace NaNs with empty strings
        preview_data = df.head(5).fillna("").to_dict(orient="records")
        return {"preview": preview_data, "filename": file.filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset: {str(e)}")

@router.get("/analytics")
async def get_analytics():
    """
    Endpoint to return mock analytics data for Chart.js
    """
    return {
        "infection_distribution": {
            "Escherichia coli": 45,
            "Staphylococcus aureus": 30,
            "Clostridioides difficile": 25
        },
        "antibiotic_usage": {
            "Ciprofloxacin": 120,
            "Ampicillin": 80,
            "Meropenem": 40,
            "Tetracycline": 90
        },
        "resistance_trends": {
            "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            "data": [15, 18, 22, 20, 25, 28]
        },
        "model_accuracy": {
            "E. coli": 92,
            "S. aureus": 88,
            "C. diff": 85,
            "Overall": 90
        }
    }
