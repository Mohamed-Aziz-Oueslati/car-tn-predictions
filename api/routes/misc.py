from fastapi import APIRouter, HTTPException
import pandas as pd

from api.state import model, gemini_client, groq_client
from api.services.csv_data import _load_imputed_csvs

router = APIRouter()

@router.get("/")
def root():
    return {
        "message": "Car Price Prediction API",
        "model_loaded": model is not None,
        "version": "1.0.0",
        "gemini_active": gemini_client is not None,
        "langchain_groq_active": groq_client is not None
    }

@router.get("/health")
def health_check():
    if model:
        return {"status": "ok", "model_loaded": True}
    return {"status": "degraded", "model_loaded": False}

@router.get("/options")
def get_options():
    try:
        df = _load_imputed_csvs()

        def to_numeric(series):
            return pd.to_numeric(series.astype(str).str.replace(r"\s+", "", regex=True), errors="coerce")

        categorical_cols = ["Marque", "Energie", "Boite_vitesse", "Transmission", "Carrosserie", "Gouvernorat", "Couleur_exterieure", "Couleur_interieure", "Sellerie"]
        numeric_cols = ["Puissance_fiscale", "Puissance_ch", "Nombre_places", "Nombre_portes", "Cylindree"]
        range_cols = ["Kilometrage", "Puissance_fiscale", "Puissance_ch", "Nombre_places", "Nombre_portes", "Cylindree"]

        options: dict = {}
        for col in categorical_cols:
            if col in df.columns:
                options[col] = sorted(df[col].dropna().str.upper().unique().tolist())
        for col in numeric_cols:
            if col in df.columns:
                vals = to_numeric(df[col]).dropna()
                options[col] = sorted([int(v) if v == int(v) else v for v in vals.unique()])

        numeric_ranges: dict = {}
        for col in range_cols:
            if col in df.columns:
                vals = to_numeric(df[col]).dropna()
                numeric_ranges[col] = {"min": int(vals.min()), "max": int(vals.max())}

        if "Mise_en_circulation" in df.columns:
            years = df["Mise_en_circulation"].dropna().apply(lambda x: int(str(x).split(".")[-1]) if "." in str(x) else int(x))
            numeric_ranges["age_voiture"] = {"min": 2026 - int(years.max()), "max": 2026 - int(years.min())}

        return {"options": options, "numeric_ranges": numeric_ranges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading options: {str(e)}")

@router.get("/models/{marque}")
def get_models_by_brand(marque: str):
    try:
        df = _load_imputed_csvs()
        filtered = df[df["Marque"].str.lower() == marque.lower()]
        return {"models": sorted(filtered["Modele"].dropna().unique().tolist()) if not filtered.empty else []}
    except Exception:
        return {"models": []}
