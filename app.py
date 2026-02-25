from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import joblib
import os

app = FastAPI(title="Car Price Prediction API")

app.add_middleware(
    CORSMiddleware,
    # APRÈS
    allow_origins=[
    "http://localhost:5173",   # dev Vite
    "http://localhost",        # prod Nginx port 80
    "http://localhost:80",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "best_model.pkl"
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None

class CarData(BaseModel):
    Marque: str
    Kilometrage: float
    Energie: str
    Boite_vitesse: str
    Puissance_fiscale: int
    Puissance_ch: Optional[int] = None
    Transmission: str
    Carrosserie: str
    Proprietaires: int
    Gouvernorat: str
    Couleur_exterieure: Optional[str] = None
    Couleur_interieure: Optional[str] = None
    Sellerie: Optional[str] = None
    Nombre_places: Optional[int] = None
    Nombre_portes: Optional[int] = None
    Cylindree: Optional[float] = None
    age_voiture: Optional[int] = None

@app.get("/health")
def health_check():
    """
    Health check endpoint to ensure API is running and model is loaded.
    """
    if model:
        return {"status": "ok", "model_loaded": True}
    return {"status": "degraded", "model_loaded": False}

@app.post("/predict")
def predict_price(data: CarData):
    """
    Real-time price prediction for a single car.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Model pipeline not available")
    
    try:
       
        input_df = pd.DataFrame([data.model_dump()])
        
        prediction = model.predict(input_df)[0]
        
        return {
            "predicted_price": float(prediction),
            "currency": "TND",
            "marque": data.Marque,
            "modele": data.Marque,  # You might want to add Modele to CarData
            "details": {
                "kilometrage": data.Kilometrage,
                "annee": 2026 - data.age_voiture if data.age_voiture else None,
                "energie": data.Energie
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Error making prediction. The model may not have proper preprocessing: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict_batch")
def predict_batch(request: dict):
    """
    Batch prediction endpoint expecting CSV data as string.
    Returns the input CSV with a new column: 'Predicted_Price'.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Model pipeline not available")
    
    try:
        if 'csv_data' in request:
            csv_content = request['csv_data']
        else:
            raise HTTPException(status_code=400, detail="Request must include 'csv_data' field")
        
        import io
        df = pd.read_csv(io.StringIO(csv_content))
        
        predictions = model.predict(df)
        
        df['Predicted_Price'] = predictions
        
        if 'Price' in df.columns:
            df['Price_Difference'] = df['Price'] - df['Predicted_Price']
            df['Percentage_Error'] = ((df['Price'] - df['Predicted_Price']) / df['Price'] * 100).round(2)
        
        return df.to_dict(orient='records')
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

@app.get("/")
def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Car Price Prediction API",
        "endpoints": {
            "/health": "Check API and model status",
            "/predict": "Predict price for a single car (POST)",
            "/predict_batch": "Predict prices for multiple cars from CSV (POST)"
        },
        "model_info": {
            "loaded": model is not None,
            "path": MODEL_PATH
        },
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)