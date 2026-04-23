# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import glob
import io
import json
import shutil
import uuid
import hashlib
import secrets
import traceback
from datetime import datetime, timedelta
from typing import Optional

import joblib
import pandas as pd
from fastapi import FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

try:
    from fastapi import Depends
    from database import get_db, engine as orm_engine
    from models import Base, User
    from schemas import UserCreate, Token, UserOut
    from auth import (
        hash_password as auth_hash_password,
        verify_password as auth_verify_password,
        create_access_token,
        decode_token,
    )
    import models as _models
    Base.metadata.create_all(bind=orm_engine)
    _ORM_AVAILABLE = True
except ImportError:
    _ORM_AVAILABLE = False

try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    gemini_client = None

app = FastAPI(title="Car Price Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "http://localhost:80",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def force_utf8(request: Request, call_next):
    response = await call_next(request)
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

MODEL_PATH = "best_model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/automarket")
engine = create_engine(
    DATABASE_URL,
    connect_args={"client_encoding": "utf8"},
    pool_pre_ping=True,
    echo=False,
)

SECRET_KEY = "ton_secret_key_change_moi"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")



def hash_password(password: str) -> str:
    """SHA-256 + random salt hashing."""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{hashed}"


def verify_password(plain: str, hashed_with_salt: str) -> bool:
    try:
        salt, hashed = hashed_with_salt.split(":")
        return hashlib.sha256((plain + salt).encode()).hexdigest() == hashed
    except Exception:
        return False


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_user_id_from_token(authorization: str) -> int:
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token manquant")
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide")



class CarData(BaseModel):
    Marque: str
    Kilometrage: float
    Energie: str
    Boite_vitesse: str
    Puissance_fiscale: int
    Puissance_ch: Optional[int] = None
    Transmission: str
    Carrosserie: str
    Proprietaires: Optional[int] = None
    Gouvernorat: str
    Couleur_exterieure: Optional[str] = None
    Couleur_interieure: Optional[str] = None
    Sellerie: Optional[str] = None
    Nombre_places: Optional[int] = None
    Nombre_portes: Optional[int] = None
    Cylindree: Optional[float] = None
    age_voiture: Optional[int] = None


class CarAnnonce(BaseModel):
    marque: str
    modele: Optional[str] = None
    kilometrage: float
    energie: str
    boite_vitesse: str
    puissance_fiscale: int
    puissance_ch: Optional[int] = None
    carrosserie: str
    gouvernorat: str
    couleur_exterieure: Optional[str] = None
    couleur_interieure: Optional[str] = None
    sellerie: Optional[str] = None
    nombre_places: Optional[int] = None
    nombre_portes: Optional[int] = None
    cylindree: Optional[float] = None
    age_voiture: Optional[int] = None
    prix: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    vendeur_nom: Optional[str] = None
    vendeur_telephone: Optional[str] = None
    images: Optional[list] = None


class CarStatut(BaseModel):
    statut: str  # "disponible" | "vendue"


class UserRegister(BaseModel):
    nom: str
    prenom: str
    email: str
    password: str
    telephone: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    gouvernorat: Optional[str] = None
    bio: Optional[str] = None
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class MessageCreate(BaseModel):
    receiver_id: int
    car_id: int
    content: str


class AutofillRequest(BaseModel):
    query: str
    history: list = []



def _load_imputed_csvs() -> pd.DataFrame:
    csv_files = sorted(glob.glob("*_imputed.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail="No imputed CSV data files found")
    return pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)


def create_notifications_new_car(
    conn, car_id: int, seller_id: int, marque: str, modele: str, gouvernorat: str
):
    """Insert a notification for every user except the seller."""
    try:
        users = conn.execute(
            text("SELECT id FROM users WHERE id != :seller_id"),
            {"seller_id": seller_id},
        ).fetchall()
        title = f"Nouvelle annonce : {marque} {modele}"
        body = f"Une nouvelle voiture vient d'être publiée à {gouvernorat}."
        for u in users:
            conn.execute(
                text("""
                    INSERT INTO notifications (user_id, type, title, body, car_id)
                    VALUES (:user_id, 'new_car', :title, :body, :car_id)
                """),
                {"user_id": u.id, "title": title, "body": body, "car_id": car_id},
            )
    except Exception:
        pass  # Never block a car publication because of a notification failure



@app.get("/")
def root():
    return {
        "message": "Car Price Prediction API",
        "model_loaded": model is not None,
        "version": "1.0.0",
        "endpoints": {
            "/health":        "Check API and model status",
            "/predict":       "Predict price for a single car (POST)",
            "/predict_batch": "Predict prices from CSV (POST)",
            "/options":       "Get valid field options from training data (GET)",
            "/models/{marque}": "Get models for a brand (GET)",
            "/autofill":      "AI autofill car details from text (POST)",
            "/cars":          "List / create car listings (GET | POST)",
            "/upload-image":  "Upload car image (POST)",
            "/auth/register": "Register (POST)",
            "/auth/login":    "Login (POST)",
            "/auth/me":       "Current user info (GET)",
        },
    }


@app.get("/health")
def health_check():
    if model:
        return {"status": "ok", "model_loaded": True}
    return {"status": "degraded", "model_loaded": False}



@app.get("/options")
def get_options():
    try:
        df = _load_imputed_csvs()

        def to_numeric(series):
            return pd.to_numeric(
                series.astype(str).str.replace(r"\s+", "", regex=True),
                errors="coerce",
            )

        categorical_cols = [
            "Marque", "Energie", "Boite_vitesse", "Transmission",
            "Carrosserie", "Gouvernorat", "Couleur_exterieure",
            "Couleur_interieure", "Sellerie",
        ]
        numeric_cols = [
            "Puissance_fiscale", "Puissance_ch", "Nombre_places",
            "Nombre_portes", "Cylindree",
        ]
        range_cols = [
            "Kilometrage", "Puissance_fiscale", "Puissance_ch",
            "Nombre_places", "Nombre_portes", "Cylindree",
        ]

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
            years = df["Mise_en_circulation"].dropna().apply(
                lambda x: int(str(x).split(".")[-1]) if "." in str(x) else int(x)
            )
            current_year = 2026
            numeric_ranges["age_voiture"] = {
                "min": current_year - int(years.max()),
                "max": current_year - int(years.min()),
            }

        return {"options": options, "numeric_ranges": numeric_ranges}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading options: {str(e)}")


@app.get("/models/{marque}")
def get_models_by_brand(marque: str):
    df = _load_imputed_csvs()
    filtered = df[df["Marque"].str.lower() == marque.lower()]
    if filtered.empty:
        return {"models": []}
    return {"models": sorted(filtered["Modele"].dropna().unique().tolist())}


@app.post("/autofill")
async def autofill_car(req: AutofillRequest):
    if not gemini_client:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set the GEMINI_API_KEY environment variable.",
        )
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is empty")

    try:
        valid_options: dict = {}
        try:
            df = _load_imputed_csvs()
            for col in [
                "Marque", "Energie", "Boite_vitesse", "Transmission",
                "Carrosserie", "Gouvernorat", "Couleur_exterieure",
                "Couleur_interieure", "Sellerie",
            ]:
                if col in df.columns:
                    valid_options[col] = sorted(df[col].dropna().unique().tolist())
        except Exception:
            pass

        system_prompt = f"""Tu es un expert automobile tunisien. L'utilisateur décrit une voiture et tu dois extraire les caractéristiques techniques pour une prédiction de prix.

Réponds TOUJOURS en JSON valide avec ces champs (met null si tu ne peux pas déterminer) :
{{
  "matched": true,
  "message": "<court résumé de la voiture identifiée>",
  "Marque": "<marque>",
  "Energie": "<Essence|Diesel|Electrique|Hybride|GPL>",
  "Boite_vitesse": "<Manuelle|Automatique>",
  "Transmission": "<Traction avant|Propulsion|Intégrale|4x4>",
  "Carrosserie": "<Berline|SUV|Citadine|Compacte|Break|Cabriolet|Coupé|Pick-up|Monospace|Utilitaire>",
  "Puissance_fiscale": <int CV fiscaux>,
  "Puissance_ch": <int chevaux>,
  "Nombre_places": <int>,
  "Nombre_portes": <int>,
  "Cylindree": <int cc>,
  "Kilometrage": null,
  "age_voiture": <int âge en années depuis 2026>,
  "Gouvernorat": null,
  "Couleur_exterieure": null,
  "Couleur_interieure": null,
  "Sellerie": null
}}

RÈGLES IMPORTANTES :
- Utilise tes connaissances automobiles pour remplir un maximum de champs.
- Pour la Marque, choisis UNIQUEMENT parmi : {valid_options.get('Marque', [])}
- Pour Energie, choisis parmi : {valid_options.get('Energie', [])}
- Pour Boite_vitesse, choisis parmi : {valid_options.get('Boite_vitesse', [])}
- Pour Transmission, choisis parmi : {valid_options.get('Transmission', [])}
- Pour Carrosserie, choisis parmi : {valid_options.get('Carrosserie', [])}
- Si l'utilisateur mentionne une année (ex: 2019), calcule age_voiture = 2026 - année.
- Réponds UNIQUEMENT avec le JSON, sans texte autour, sans markdown.
- Si la description ne correspond à aucune voiture connue, mets "matched": false et dans "message" explique pourquoi."""

        contents = []
        for msg in req.history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(
                genai.types.Content(role=role, parts=[genai.types.Part(text=msg.get("text", ""))])
            )
        contents.append(
            genai.types.Content(
                role="user", parts=[genai.types.Part(text=req.query.strip())]
            )
        )

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=contents,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                max_output_tokens=1024,
            ),
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        result = json.loads(raw)
        result.setdefault("matched", True)
        return result

    except json.JSONDecodeError:
        return {
            "matched": True,
            "message": raw if "raw" in dir() else "Réponse non structurée du LLM",
            "parse_error": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autofill error: {str(e)}")



@app.post("/predict")
def predict_price(data: CarData):
    if not model:
        raise HTTPException(status_code=503, detail="Model not available")
    try:
        input_df = pd.DataFrame([data.model_dump()])
        prediction = model.predict(input_df)[0]
        return {
            "predicted_price": float(prediction),
            "currency": "TND",
            "marque": data.Marque,
            "details": {
                "kilometrage": data.Kilometrage,
                "annee": 2026 - data.age_voiture if data.age_voiture else None,
                "energie": data.Energie,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_batch")
def predict_batch(request: dict):
    if not model:
        raise HTTPException(status_code=503, detail="Model not available")
    try:
        if "csv_data" not in request:
            raise HTTPException(status_code=400, detail="Request must include 'csv_data' field")
        df = pd.read_csv(io.StringIO(request["csv_data"]))
        predictions = model.predict(df)
        df["Predicted_Price"] = predictions
        if "Price" in df.columns:
            df["Price_Difference"] = df["Price"] - df["Predicted_Price"]
            df["Percentage_Error"] = (
                (df["Price"] - df["Predicted_Price"]) / df["Price"] * 100
            ).round(2)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



@app.post("/cars")
def create_car(car: CarAnnonce, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            user_row = conn.execute(
                text("SELECT nom, prenom, telephone FROM users WHERE id = :id"),
                {"id": user_id},
            ).fetchone()
            vendeur_nom = f"{user_row.prenom} {user_row.nom}" if user_row else None
            vendeur_telephone = user_row.telephone if user_row else None

            result = conn.execute(
                text("""
                    INSERT INTO cars (
                        marque, modele, kilometrage, energie, boite_vitesse,
                        puissance_fiscale, puissance_ch, carrosserie, gouvernorat,
                        couleur_exterieure, couleur_interieure, sellerie,
                        nombre_places, nombre_portes, cylindree, age_voiture,
                        prix, description, image_url, user_id,
                        vendeur_nom, vendeur_telephone, images
                    ) VALUES (
                        :marque, :modele, :kilometrage, :energie, :boite_vitesse,
                        :puissance_fiscale, :puissance_ch, :carrosserie, :gouvernorat,
                        :couleur_exterieure, :couleur_interieure, :sellerie,
                        :nombre_places, :nombre_portes, :cylindree, :age_voiture,
                        :prix, :description, :image_url, :user_id,
                        :vendeur_nom, :vendeur_telephone, :images
                    ) RETURNING id
                """),
                {
                    **car.model_dump(),
                    "user_id": user_id,
                    "vendeur_nom": vendeur_nom,
                    "vendeur_telephone": vendeur_telephone,
                },
            )
            conn.commit()
            new_id = result.fetchone()[0]

            create_notifications_new_car(
                conn,
                car_id=new_id,
                seller_id=user_id,
                marque=car.marque,
                modele=car.modele or "",
                gouvernorat=car.gouvernorat,
            )
            conn.commit()
            return {"success": True, "id": new_id, "message": "Annonce publiée !"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cars")
def get_cars(limit: int = 1000):
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM cars ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit},
            ).fetchall()
            return [
                {
                    "id":                row.id,
                    "make":              row.marque,
                    "model":             row.modele or "",
                    "mileage":           row.kilometrage,
                    "fuel":              row.energie,
                    "transmission":      row.boite_vitesse,
                    "puissance_fiscale": row.puissance_fiscale,
                    "carrosserie":       row.carrosserie,
                    "statut":            row.statut or "disponible",
                    "location":          row.gouvernorat,
                    "price":             row.prix or 0,
                    "year":              2026 - (row.age_voiture or 0),
                    "image":             row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                    "badge":             "Nouveau",
                    "description":       row.description or "",
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cars/{car_id}")
def get_car(car_id: int):
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("""
                    SELECT c.*, u.email AS vendeur_email
                    FROM cars c
                    LEFT JOIN users u ON c.user_id = u.id
                    WHERE c.id = :id
                """),
                {"id": car_id},
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Annonce introuvable")
            return {
                "id":                 row.id,
                "make":               row.marque,
                "model":              row.modele or "",
                "mileage":            row.kilometrage,
                "fuel":               row.energie,
                "transmission":       row.boite_vitesse,
                "puissance_fiscale":  row.puissance_fiscale,
                "carrosserie":        row.carrosserie,
                "location":           row.gouvernorat,
                "statut":             row.statut or "disponible",
                "price":              row.prix or 0,
                "year":               2026 - (row.age_voiture or 0),
                "image":              row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                "badge":              "Nouveau",
                "description":        row.description or "",
                "couleur_exterieure": row.couleur_exterieure,
                "couleur_interieure": row.couleur_interieure,
                "sellerie":           row.sellerie,
                "nombre_places":      row.nombre_places,
                "nombre_portes":      row.nombre_portes,
                "cylindree":          row.cylindree,
                "vendeur_nom":        row.vendeur_nom or "Vendeur",
                "vendeur_telephone":  row.vendeur_telephone or None,
                "vendeur_email":      row.vendeur_email or None,
                "user_id":            row.user_id,
                "created_at":         str(row.created_at),
                "images":             list(row.images) if row.images else [],
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/my-cars")
def get_my_cars(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT * FROM cars WHERE user_id = :uid ORDER BY created_at DESC"),
                {"uid": user_id},
            ).fetchall()
            return [
                {
                    "id":           row.id,
                    "make":         row.marque,
                    "model":        row.modele or "",
                    "mileage":      row.kilometrage,
                    "fuel":         row.energie,
                    "transmission": row.boite_vitesse,
                    "carrosserie":  row.carrosserie,
                    "location":     row.gouvernorat,
                    "statut":       row.statut or "disponible",
                    "price":        row.prix or 0,
                    "year":         2026 - (row.age_voiture or 0),
                    "image":        row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                    "badge":        "Mon annonce",
                    "description":  row.description or "",
                    "created_at":   str(row.created_at),
                }
                for row in rows
            ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/cars/{car_id}/statut")
def update_car_statut(car_id: int, data: CarStatut, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT user_id FROM cars WHERE id = :id"), {"id": car_id}
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Annonce introuvable")
            if row.user_id != user_id:
                raise HTTPException(status_code=403, detail="Non autorisé")
            if data.statut not in ("disponible", "vendue"):
                raise HTTPException(status_code=400, detail="Statut invalide")
            conn.execute(
                text("UPDATE cars SET statut = :statut WHERE id = :id"),
                {"statut": data.statut, "id": car_id},
            )
            conn.commit()
            return {"success": True, "statut": data.statut}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cars/{car_id}")
def delete_car(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT user_id FROM cars WHERE id = :id"), {"id": car_id}
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Annonce introuvable")
            if row.user_id != user_id:
                raise HTTPException(status_code=403, detail="Non autorisé")
            conn.execute(text("DELETE FROM cars WHERE id = :id"), {"id": car_id})
            conn.commit()
            return {"success": True, "message": "Annonce supprimée"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/cars/{car_id}/view")
def record_view(car_id: int, request: Request):
    try:
        viewer_ip = request.client.host
        with engine.connect() as conn:
            existing = conn.execute(
                text("""
                    SELECT id FROM car_views
                    WHERE car_id = :car_id
                      AND viewer_ip = :ip
                      AND viewed_at > NOW() - INTERVAL '1 hour'
                """),
                {"car_id": car_id, "ip": viewer_ip},
            ).fetchone()
            if not existing:
                conn.execute(
                    text("INSERT INTO car_views (car_id, viewer_ip) VALUES (:car_id, :ip)"),
                    {"car_id": car_id, "ip": viewer_ip},
                )
                conn.commit()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        allowed = ["jpg", "jpeg", "png", "webp"]
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Format non supporté. Utilisez : {', '.join(allowed)}")
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"image_url": f"{BASE_URL}/static/images/{filename}", "filename": filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-car-image")
async def analyze_car_image(file: UploadFile = File(...)):
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini non configuré")
    
    try:
        from PIL import Image
        import io
        import json
        
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        system_prompt = """Tu es un expert automobile. Identifie la marque, le modèle et l'année (ou année approximative) de la voiture sur cette image.
Réponds TOUJOURS en JSON valide avec ces champs :
{
  "marque": "<Marque>",
  "modele": "<Modèle>",
  "annee": <Année en entier ou null>
}
Ne renvoie que le JSON, sans formattage Markdown supplémentaire."""

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[image, "Identifie cette voiture (marque, modèle, année)."],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                max_output_tokens=512,
            ),
        )
        
        raw = response.text.strip()
        if raw.startswith("```json"):
            raw = raw[7:]
        elif raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
        
        return json.loads(raw)
        
    except json.JSONDecodeError:
        return {"error": "Format inattendu rendu par l'IA", "raw": raw}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/auth/register")
async def register(request: Request):
    try:
        body_bytes = await request.body()
        try:
            body_str = body_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                body_str = body_bytes.decode("latin-1")
            except Exception:
                body_str = body_bytes.decode("utf-8", errors="ignore")

        try:
            data = json.loads(body_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON invalide: {str(e)}")

        nom = data.get("nom", "").strip()
        prenom = data.get("prenom", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        telephone = data.get("telephone", "")

        if not all([nom, prenom, email, password]):
            raise HTTPException(status_code=400, detail="Tous les champs sont requis")

        with engine.connect() as conn:
            if conn.execute(
                text("SELECT id FROM users WHERE email = :email"), {"email": email}
            ).fetchone():
                raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

            result = conn.execute(
                text("""
                    INSERT INTO users (nom, prenom, email, password_hash, telephone)
                    VALUES (:nom, :prenom, :email, :password_hash, :telephone)
                    RETURNING id, nom, prenom, email, avatar_url
                """),
                {
                    "nom": nom,
                    "prenom": prenom,
                    "email": email,
                    "password_hash": hash_password(password),
                    "telephone": telephone,
                },
            )
            conn.commit()
            row = result.fetchone()
            token = create_token({"sub": str(row.id), "email": row.email})
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": row.id,
                    "nom": row.nom,
                    "prenom": row.prenom,
                    "email": row.email,
                    "avatar_url": row.avatar_url or "",
                },
            }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.post("/auth/login")
async def login(request: Request):
    try:
        body_bytes = await request.body()
        try:
            body_str = body_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                body_str = body_bytes.decode("latin-1")
            except Exception:
                body_str = body_bytes.decode("utf-8", errors="ignore")

        try:
            data = json.loads(body_str)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON invalide: {str(e)}")

        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email et mot de passe requis")

        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE email = :email"), {"email": email}
            ).fetchone()
            if not row or not verify_password(password, row.password_hash):
                raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
            token = create_token({"sub": str(row.id), "email": row.email})
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": row.id,
                    "nom": row.nom,
                    "prenom": row.prenom,
                    "email": row.email,
                    "avatar_url": row.avatar_url or "",
                },
            }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@app.get("/auth/me")
def get_me(authorization: str = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token manquant")
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, nom, prenom, email FROM users WHERE id = :id"),
                {"id": int(user_id)},
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")


@app.get("/auth/profile")
def get_profile(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {
                "id":          row.id,
                "nom":         row.nom,
                "prenom":      row.prenom,
                "email":       row.email,
                "telephone":   row.telephone or "",
                "avatar_url":  row.avatar_url or "",
                "gouvernorat": row.gouvernorat or "",
                "bio":         row.bio or "",
                "created_at":  str(row.created_at),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/auth/profile")
def update_profile(data: UserUpdate, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            user = conn.execute(
                text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
            ).fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")

            email_changed = data.email is not None and data.email != user.email
            password_changed = bool(data.new_password)

            if (email_changed or password_changed) and not data.current_password:
                raise HTTPException(
                    status_code=400,
                    detail="Mot de passe actuel requis pour modifier l'email ou le mot de passe",
                )
            if (email_changed or password_changed) and not verify_password(
                data.current_password, user.password_hash
            ):
                raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")

            if email_changed:
                if conn.execute(
                    text("SELECT id FROM users WHERE email = :email AND id != :id"),
                    {"email": data.email, "id": user_id},
                ).fetchone():
                    raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
                conn.execute(
                    text("UPDATE users SET email = :email WHERE id = :id"),
                    {"email": data.email, "id": user_id},
                )

            if password_changed:
                conn.execute(
                    text("UPDATE users SET password_hash = :hash WHERE id = :id"),
                    {"hash": hash_password(data.new_password), "id": user_id},
                )

            conn.execute(
                text("""
                    UPDATE users SET
                        nom         = COALESCE(:nom,         nom),
                        prenom      = COALESCE(:prenom,      prenom),
                        telephone   = COALESCE(:telephone,   telephone),
                        gouvernorat = COALESCE(:gouvernorat, gouvernorat),
                        bio         = COALESCE(:bio,         bio),
                        updated_at  = NOW()
                    WHERE id = :id
                """),
                {
                    "nom": data.nom,
                    "prenom": data.prenom,
                    "telephone": data.telephone,
                    "gouvernorat": data.gouvernorat,
                    "bio": data.bio,
                    "id": user_id,
                },
            )
            conn.commit()

            row = conn.execute(
                text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
            ).fetchone()
            new_token = create_token({"sub": str(row.id), "email": row.email}) if email_changed else None

            return {
                "success":      True,
                "id":           row.id,
                "nom":          row.nom,
                "prenom":       row.prenom,
                "email":        row.email,
                "telephone":    row.telephone or "",
                "avatar_url":   row.avatar_url or "",
                "gouvernorat":  row.gouvernorat or "",
                "bio":          row.bio or "",
                "access_token": new_token,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/avatar")
async def update_avatar(file: UploadFile = File(...), authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        allowed = ["jpg", "jpeg", "png", "webp"]
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail="Format non supporté.")
        filename = f"avatar_{user_id}_{uuid.uuid4()}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        avatar_url = f"{BASE_URL}/static/images/{filename}"
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE users SET avatar_url = :url WHERE id = :id"),
                {"url": avatar_url, "id": user_id},
            )
            conn.commit()
        return {"success": True, "avatar_url": avatar_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/auth/password")
def change_password(data: ChangePassword, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT password_hash FROM users WHERE id = :id"), {"id": user_id}
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            if not verify_password(data.current_password, row.password_hash):
                raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
            conn.execute(
                text("UPDATE users SET password_hash = :hash WHERE id = :id"),
                {"hash": hash_password(data.new_password), "id": user_id},
            )
            conn.commit()
            return {"success": True, "message": "Mot de passe mis à jour"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/messages")
def send_message(msg: MessageCreate, authorization: str = Header(None)):
    sender_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conv = conn.execute(
                text("""
                    SELECT id FROM conversations
                    WHERE (user1_id = :u1 AND user2_id = :u2 AND car_id = :car)
                       OR (user1_id = :u2 AND user2_id = :u1 AND car_id = :car)
                """),
                {"u1": sender_id, "u2": msg.receiver_id, "car": msg.car_id},
            ).fetchone()

            if not conv:
                conv_id = conn.execute(
                    text("""
                        INSERT INTO conversations (user1_id, user2_id, car_id)
                        VALUES (:u1, :u2, :car)
                        RETURNING id
                    """),
                    {"u1": sender_id, "u2": msg.receiver_id, "car": msg.car_id},
                ).fetchone()[0]
            else:
                conv_id = conv[0]

            conn.execute(
                text("""
                    INSERT INTO messages (sender_id, receiver_id, car_id, content)
                    VALUES (:sender, :receiver, :car, :content)
                """),
                {
                    "sender": sender_id,
                    "receiver": msg.receiver_id,
                    "car": msg.car_id,
                    "content": msg.content,
                },
            )
            conn.commit()
            return {"success": True, "conversation_id": conv_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations")
def get_conversations(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT
                        c.id,
                        c.car_id,
                        ca.marque,
                        ca.modele,
                        ca.image_url,
                        CASE WHEN c.user1_id = :uid THEN c.user2_id ELSE c.user1_id END AS other_id,
                        CASE WHEN c.user1_id = :uid THEN u2.prenom   ELSE u1.prenom   END AS other_prenom,
                        CASE WHEN c.user1_id = :uid THEN u2.nom      ELSE u1.nom      END AS other_nom,
                        (SELECT content FROM messages m
                         WHERE m.car_id = c.car_id
                           AND ((m.sender_id = :uid AND m.receiver_id != :uid)
                             OR (m.receiver_id = :uid AND m.sender_id != :uid))
                         ORDER BY m.created_at DESC LIMIT 1) AS last_message,
                        (SELECT created_at FROM messages m
                         WHERE m.car_id = c.car_id
                           AND ((m.sender_id = :uid AND m.receiver_id != :uid)
                             OR (m.receiver_id = :uid AND m.sender_id != :uid))
                         ORDER BY m.created_at DESC LIMIT 1) AS last_at,
                        (SELECT COUNT(*) FROM messages m
                         WHERE m.receiver_id = :uid
                           AND m.car_id = c.car_id
                           AND m.is_read = FALSE) AS unread_count
                    FROM conversations c
                    JOIN users u1 ON c.user1_id = u1.id
                    JOIN users u2 ON c.user2_id = u2.id
                    JOIN cars  ca ON c.car_id   = ca.id
                    WHERE c.user1_id = :uid OR c.user2_id = :uid
                    ORDER BY last_at DESC NULLS LAST
                """),
                {"uid": user_id},
            ).fetchall()

            return [
                {
                    "id":           row.id,
                    "car_id":       row.car_id,
                    "marque":       row.marque,
                    "modele":       row.modele or "",
                    "image_url":    row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                    "other_id":     row.other_id,
                    "other_prenom": row.other_prenom,
                    "other_nom":    row.other_nom,
                    "last_message": row.last_message or "",
                    "last_at":      str(row.last_at) if row.last_at else "",
                    "unread_count": row.unread_count,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/messages/{other_id}/{car_id}")
def get_messages(other_id: int, car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    UPDATE messages SET is_read = TRUE
                    WHERE receiver_id = :uid AND sender_id = :other AND car_id = :car
                """),
                {"uid": user_id, "other": other_id, "car": car_id},
            )
            conn.commit()
            rows = conn.execute(
                text("""
                    SELECT m.id, m.sender_id, m.receiver_id, m.content,
                           m.is_read, m.created_at,
                           u.prenom AS sender_prenom
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    WHERE m.car_id = :car
                      AND ((m.sender_id = :uid AND m.receiver_id = :other)
                        OR (m.sender_id = :other AND m.receiver_id = :uid))
                    ORDER BY m.created_at ASC
                """),
                {"uid": user_id, "other": other_id, "car": car_id},
            ).fetchall()

            return [
                {
                    "id":            row.id,
                    "sender_id":     row.sender_id,
                    "receiver_id":   row.receiver_id,
                    "content":       row.content,
                    "is_read":       row.is_read,
                    "created_at":    str(row.created_at),
                    "sender_prenom": row.sender_prenom,
                    "is_mine":       row.sender_id == user_id,
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/unread-count")
def get_unread_count(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid AND is_read = FALSE"),
                {"uid": user_id},
            ).fetchone()
            return {"unread": row.count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/notifications")
def get_notifications(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT
                        n.id, n.type, n.title, n.body,
                        n.is_read, n.created_at, n.car_id,
                        c.marque, c.modele, c.image_url, c.gouvernorat
                    FROM notifications n
                    LEFT JOIN cars c ON n.car_id = c.id
                    WHERE n.user_id = :uid
                    ORDER BY n.created_at DESC
                    LIMIT 30
                """),
                {"uid": user_id},
            ).fetchall()
            return [
                {
                    "id":          row.id,
                    "type":        row.type,
                    "title":       row.title,
                    "body":        row.body,
                    "is_read":     row.is_read,
                    "created_at":  str(row.created_at),
                    "car_id":      row.car_id,
                    "image_url":   row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=200",
                    "marque":      row.marque or "",
                    "modele":      row.modele or "",
                    "gouvernorat": row.gouvernorat or "",
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/unread-count")
def get_notif_unread_count(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT COUNT(*) AS count FROM notifications WHERE user_id = :uid AND is_read = FALSE"),
                {"uid": user_id},
            ).fetchone()
            return {"unread": row.count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE notifications SET is_read = TRUE WHERE id = :id AND user_id = :uid"),
                {"id": notif_id, "uid": user_id},
            )
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/notifications/read-all")
def mark_all_notifications_read(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("UPDATE notifications SET is_read = TRUE WHERE user_id = :uid AND is_read = FALSE"),
                {"uid": user_id},
            )
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/notifications")
def delete_all_notifications(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(
                text("DELETE FROM notifications WHERE user_id = :uid"), {"uid": user_id}
            )
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/dashboard/stats")
def get_dashboard_stats(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            total_annonces = conn.execute(
                text("SELECT COUNT(*) AS count FROM cars WHERE user_id = :uid"), {"uid": user_id}
            ).fetchone().count

            messages_non_lus = conn.execute(
                text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid AND is_read = FALSE"),
                {"uid": user_id},
            ).fetchone().count

            total_messages = conn.execute(
                text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid"), {"uid": user_id}
            ).fetchone().count

            total_vues = conn.execute(
                text("""
                    SELECT COUNT(*) AS count FROM car_views cv
                    JOIN cars c ON cv.car_id = c.id
                    WHERE c.user_id = :uid
                """),
                {"uid": user_id},
            ).fetchone().count

            vues_7j = conn.execute(
                text("""
                    SELECT DATE(cv.viewed_at) AS jour, COUNT(*) AS vues
                    FROM car_views cv
                    JOIN cars c ON cv.car_id = c.id
                    WHERE c.user_id = :uid
                      AND cv.viewed_at > NOW() - INTERVAL '7 days'
                    GROUP BY DATE(cv.viewed_at)
                    ORDER BY jour ASC
                """),
                {"uid": user_id},
            ).fetchall()

            annonces_vues = conn.execute(
                text("""
                    SELECT c.id, c.marque, c.modele, c.prix, c.image_url, c.created_at,
                           COUNT(cv.id) AS vues
                    FROM cars c
                    LEFT JOIN car_views cv ON cv.car_id = c.id
                    WHERE c.user_id = :uid
                    GROUP BY c.id
                    ORDER BY vues DESC
                    LIMIT 5
                """),
                {"uid": user_id},
            ).fetchall()

            annonces_par_mois = conn.execute(
                text("""
                    SELECT TO_CHAR(created_at, 'Mon') AS mois, COUNT(*) AS count
                    FROM cars
                    WHERE user_id = :uid
                      AND created_at > NOW() - INTERVAL '6 months'
                    GROUP BY TO_CHAR(created_at, 'Mon'), DATE_TRUNC('month', created_at)
                    ORDER BY DATE_TRUNC('month', created_at) ASC
                """),
                {"uid": user_id},
            ).fetchall()

            return {
                "total_annonces":   total_annonces,
                "total_messages":   total_messages,
                "messages_non_lus": messages_non_lus,
                "total_vues":       total_vues,
                "vues_7j":          [{"jour": str(r.jour), "vues": r.vues} for r in vues_7j],
                "annonces_top": [
                    {
                        "id":        r.id,
                        "marque":    r.marque,
                        "modele":    r.modele or "",
                        "prix":      r.prix or 0,
                        "image_url": r.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400",
                        "created_at": str(r.created_at),
                        "vues":      r.vues,
                    }
                    for r in annonces_vues
                ],
                "annonces_par_mois": [{"mois": r.mois, "count": r.count} for r in annonces_par_mois],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if _ORM_AVAILABLE:
    from fastapi import Depends

    @app.post("/register", response_model=Token)
    def register_oauth(user: UserCreate, db: Session = Depends(get_db)):
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        new_user = User(
            full_name=user.full_name,
            email=user.email,
            password=auth_hash_password(user.password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
        return {"access_token": token, "token_type": "bearer", "user": new_user}

    @app.post("/login", response_model=Token)
    def login_oauth(credentials: UserLogin, db: Session = Depends(get_db)):
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not auth_verify_password(credentials.password, user.password):
            raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
        token = create_access_token({"sub": str(user.id), "email": user.email})
        return {"access_token": token, "token_type": "bearer", "user": user}

    @app.get("/me", response_model=UserOut)
    def get_me_oauth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        try:
            payload = decode_token(token)
            user_id = int(payload.get("sub"))
        except Exception:
            raise HTTPException(status_code=401, detail="Token invalide")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        return user



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)