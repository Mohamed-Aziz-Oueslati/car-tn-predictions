import io
import pandas as pd
from fastapi import APIRouter, HTTPException

from api.schemas import CarData
from api.state import model

router = APIRouter()

@router.post("/predict")
def predict_price(data: CarData):
    if not model:
        raise HTTPException(status_code=503, detail="Model not available")
    try:
        input_df = pd.DataFrame([data.model_dump()])
        prediction = model.predict(input_df)[0]
        return {
            "predicted_price": float(prediction), "currency": "TND", "marque": data.Marque,
            "details": {"kilometrage": data.Kilometrage, "annee": 2026 - data.age_voiture if data.age_voiture else None, "energie": data.Energie}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict_batch")
def predict_batch(request: dict):
    if not model:
        raise HTTPException(status_code=503, detail="Model not available")
    try:
        df = pd.read_csv(io.StringIO(request["csv_data"]))
        predictions = model.predict(df)
        df["Predicted_Price"] = predictions
        if "Price" in df.columns:
            df["Price_Difference"] = df["Price"] - df["Predicted_Price"]
            df["Percentage_Error"] = ((df["Price"] - df["Predicted_Price"]) / df["Price"] * 100).round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
