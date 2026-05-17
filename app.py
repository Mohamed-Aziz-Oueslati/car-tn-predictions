from pathlib import Path
import sys

from fastapi.responses import FileResponse
sys.stdout.reconfigure(encoding='utf-8')

import os
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
import glob
import io
import json
import shutil
import uuid
import hashlib
import secrets
import traceback
import tempfile
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import httpx
import joblib
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


DOWNLOAD_DIR = Path("3d_models")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
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
    from PIL import Image
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    gemini_client = None

try:
    from groq import Groq
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    if GROQ_API_KEY:
        custom_http_client = httpx.Client()
        groq_client = Groq(api_key=GROQ_API_KEY, http_client=custom_http_client)
    else:
        groq_client = None
except ImportError:
    groq_client = None
KAGGLE_API_URL = os.getenv("KAGGLE_API_URL", "https://stunt-wanting-agility.ngrok-free.dev")
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
    expose_headers=["*"],
)

@app.middleware("http")
async def force_utf8(request: Request, call_next):
    response = await call_next(request)
    if "application/json" in response.headers.get("content-type", ""):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/3d_models", StaticFiles(directory=str(DOWNLOAD_DIR)), name="3d_models")

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

def parse_images(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(img) for img in raw if img]
    if isinstance(raw, str) and raw.strip().startswith("["):
        try:
            parsed = json.loads(raw)
            return [str(i) for i in parsed if i]
        except:
            pass
    if isinstance(raw, str) and raw.startswith("http"):
        return [raw]
    return []

def _load_imputed_csvs() -> pd.DataFrame:
    csv_files = sorted(glob.glob("*_imputed.csv"))
    if not csv_files:
        raise HTTPException(status_code=404, detail="No imputed CSV data files found")
    return pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

def create_notifications_new_car(
    conn, car_id: int, seller_id: int,
    marque: str, modele: str, gouvernorat: str,
    energie: str, carrosserie: str,
    prix: float, kilometrage: float, age_voiture: int
):
    try:
        users_with_prefs = conn.execute(text("""
            SELECT
                u.id, p.marques, p.carrosseries, p.energies, p.gouvernorats,
                p.budget_min, p.budget_max, p.km_max, p.age_max, p.notify_enabled
            FROM users u
            LEFT JOIN user_preferences p ON p.user_id = u.id
            WHERE u.id != :seller_id
        """), {"seller_id": seller_id}).fetchall()

        for u in users_with_prefs:
            if u.notify_enabled is False:
                continue

            has_prefs = any([
                u.marques, u.carrosseries, u.energies,
                u.gouvernorats, u.budget_max, u.km_max
            ])

            if has_prefs:
                match = True
                if u.marques and len(u.marques) > 0 and marque not in u.marques: match = False
                if match and u.carrosseries and len(u.carrosseries) > 0 and carrosserie not in u.carrosseries: match = False
                if match and u.energies and len(u.energies) > 0 and energie not in u.energies: match = False
                if match and u.gouvernorats and len(u.gouvernorats) > 0 and gouvernorat not in u.gouvernorats: match = False
                if match and prix is not None:
                    budget_min = u.budget_min or 0
                    budget_max = u.budget_max or 999999
                    if not (budget_min <= prix <= budget_max): match = False
                if match and kilometrage is not None and u.km_max and kilometrage > u.km_max: match = False
                if match and age_voiture is not None and u.age_max and age_voiture > u.age_max: match = False
                
                if not match:
                    continue 

            title = f"Nouvelle annonce : {marque} {modele or ''}"
            body  = f"{gouvernorat} · {prix:,.0f} TND" if prix else f"{gouvernorat}"

            conn.execute(text("""
                INSERT INTO notifications (user_id, type, title, body, car_id)
                VALUES (:uid, 'new_car', :title, :body, :car_id)
            """), {"uid": u.id, "title": title, "body": body, "car_id": car_id})

    except Exception as e:
        print(f"Erreur notifications: {e}")

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
    statut: str 

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

class UserPreferences(BaseModel):
    marques: Optional[list] = []
    carrosseries: Optional[list] = []
    energies: Optional[list] = []
    gouvernorats: Optional[list] = []
    budget_min: Optional[float] = 0
    budget_max: Optional[float] = 999999
    km_max: Optional[float] = 999999
    age_max: Optional[int] = 20
    notify_enabled: Optional[bool] = True

class NotifPreferences(BaseModel):
    budget_min: Optional[float] = 0
    budget_max: Optional[float] = 9999999
    marques: Optional[list] = []
    energies: Optional[list] = []
    carrosseries: Optional[list] = []
    gouvernorats: Optional[list] = []
    kilometrage_max: Optional[float] = 999999
    annee_min: Optional[int] = 0
    notifications_actives: Optional[bool] = True

class ChatRequest(BaseModel):
    question: str
    history: Optional[list] = []

@app.get("/")
def root():
    return {
        "message": "Car Price Prediction API",
        "model_loaded": model is not None,
        "version": "1.0.0",
        "gemini_active": gemini_client is not None,
        "langchain_groq_active": groq_client is not None
    }

@app.get("/health")
def health_check():
    if model: return {"status": "ok", "model_loaded": True}
    return {"status": "degraded", "model_loaded": False}

def _build_csv_context(df: pd.DataFrame) -> str:
    row_count = len(df)
    columns = df.columns.tolist()
    sample = df.head(5).to_markdown(index=False)

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        numeric_summary = df[numeric_cols].describe().round(2).to_string()
    else:
        numeric_summary = "None"

    categorical_cols = [c for c in columns if c not in numeric_cols][:10]
    cat_lines = []
    for col in categorical_cols:
        try:
            vc = df[col].dropna().astype(str).value_counts().head(5)
        except Exception:
            continue
        if not vc.empty:
            pairs = ", ".join([f"{k}: {v}" for k, v in vc.items()])
            cat_lines.append(f"{col}: {pairs}")
    cat_summary = "\n".join(cat_lines) if cat_lines else "None"

    return (
        "CSV context:\n"
        f"Rows: {row_count}\n"
        f"Columns ({len(columns)}): {', '.join(columns)}\n\n"
        "Sample rows:\n"
        f"{sample}\n\n"
        "Numeric summary:\n"
        f"{numeric_summary}\n\n"
        "Top categorical values:\n"
        f"{cat_summary}"
    )

def _gemini_csv_answer(question: str) -> str:
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")

    df = _load_imputed_csvs()
    context = _build_csv_context(df)

    system_prompt = (
        "You are an expert assistant for the Tunisian car market. "
        "Answer using only the provided CSV context. "
        "If the answer cannot be determined, say so. "
        "Reply concisely and in the user's language."
    )

    user_text = f"{context}\n\nQuestion: {question}"

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=[genai.types.Content(role="user", parts=[genai.types.Part(text=user_text)])],
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.1,
            max_output_tokens=1024,
        ),
    )

    return response.text.strip() if response and response.text else ""

SYSTEM_PROMPT_CHATBOT = """
You are an expert assistant for the Tunisian car market.
You have been given access to a database of cars (DataFrame).

IMPORTANT DIRECTIVES:
1. ALWAYS answer politely and concisely.
2. If the user's question is in English, reply in English.
3. If the user's question is in Tunisian Darija (Tunisian dialect Arabic, e.g., "b9adeh", "karhba", "chnowa rayek"), you MUST reply in Tunisian Darija (you can use Latin/Franco-Arabic characters or Arabic letters depending on how the user typed/spoke).
4. Use your pandas tools to search for exact information from the database (e.g., average prices, mileage, brand availability).
"""

@app.post("/chat")
async def chat_text(req: ChatRequest):
    try:
        question = (req.question or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is empty")
        answer = _gemini_csv_answer(question)
        return {"answer": answer, "transcription": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/audio")
async def chat_audio(file: UploadFile = File(...)):
    if not groq_client:
        raise HTTPException(status_code=503, detail="Groq API is not configured.")
    
    ext = file.filename.split(".")[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(tmp_path, audio_file.read()),
                model="whisper-large-v3",
                prompt="Tunisian Arabic, Darija tunisien, English, karhba, b9adeh, soum, krahb."
            )
        question_text = transcription.text.strip()
        
        if not question_text:
            return {"answer": "Sorry, I couldn't hear your question.", "transcription": ""}

        answer = _gemini_csv_answer(question_text)

        return {
            "transcription": question_text,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/options")
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

@app.get("/models/{marque}")
def get_models_by_brand(marque: str):
    try:
        df = _load_imputed_csvs()
        filtered = df[df["Marque"].str.lower() == marque.lower()]
        return {"models": sorted(filtered["Modele"].dropna().unique().tolist()) if not filtered.empty else []}
    except Exception:
         return {"models": []}

@app.post("/autofill")
async def autofill_car(req: AutofillRequest):
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query is empty")

    try:
        system_prompt = """Tu es un expert automobile tunisien. L'utilisateur décrit une voiture et tu dois extraire les caractéristiques techniques pour une prédiction de prix.
Réponds TOUJOURS en JSON valide avec les champs exacts (met null si tu ne peux pas déterminer). 
{
  "matched": true,
  "message": "<court résumé>",
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
  "Gouvernorat": null
}"""
        contents = []
        for msg in req.history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append(genai.types.Content(role=role, parts=[genai.types.Part(text=msg.get("text", ""))]))
        contents.append(genai.types.Content(role="user", parts=[genai.types.Part(text=req.query.strip())]))

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=contents,
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1, max_output_tokens=1024),
        )

        raw = response.text.strip()
        if raw.startswith("```"): raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"): raw = raw.rsplit("```", 1)[0]
        result = json.loads(raw.strip())
        result.setdefault("matched", True)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-car-image")
async def analyze_car_image(file: UploadFile = File(...)):
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini non configuré")
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        system_prompt = """Tu es un expert automobile. Identifie la marque, le modèle et l'année (ou année approximative) de la voiture sur cette image.
Réponds TOUJOURS en JSON valide: {"marque": "<Marque>", "modele": "<Modèle>", "annee": <Année en entier ou null>}"""

        response = gemini_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[image, "Identifie cette voiture."],
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.1, max_output_tokens=512),
        )
        
        raw = response.text.strip()
        if raw.startswith("```json"): raw = raw[7:]
        elif raw.startswith("```"): raw = raw[3:]
        if raw.endswith("```"): raw = raw[:-3]
        return json.loads(raw.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
def predict_price(data: CarData):
    if not model: raise HTTPException(status_code=503, detail="Model not available")
    try:
        input_df = pd.DataFrame([data.model_dump()])
        prediction = model.predict(input_df)[0]
        return {
            "predicted_price": float(prediction), "currency": "TND", "marque": data.Marque,
            "details": {"kilometrage": data.Kilometrage, "annee": 2026 - data.age_voiture if data.age_voiture else None, "energie": data.Energie}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_batch")
def predict_batch(request: dict):
    if not model: raise HTTPException(status_code=503, detail="Model not available")
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

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        allowed = ["jpg", "jpeg", "png", "webp"]
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed: raise HTTPException(status_code=400, detail="Format non supporté.")
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        return {"image_url": f"{BASE_URL}/static/images/{filename}", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cars")
def create_car(car: CarAnnonce, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            user_row = conn.execute(text("SELECT nom, prenom, telephone FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            vendeur_nom = f"{user_row.prenom} {user_row.nom}" if user_row else None
            vendeur_telephone = user_row.telephone if user_row else None

            result = conn.execute(text("""
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
            """), {**car.model_dump(), "user_id": user_id, "vendeur_nom": vendeur_nom, "vendeur_telephone": vendeur_telephone, "images": car.images})
            conn.commit()
            new_id = result.fetchone()[0]

            create_notifications_new_car(
                conn, car_id=new_id, seller_id=user_id, marque=car.marque, modele=car.modele or "",
                gouvernorat=car.gouvernorat, energie=car.energie, carrosserie=car.carrosserie,
                prix=car.prix or 0, kilometrage=car.kilometrage, age_voiture=car.age_voiture or 0
            )
            conn.commit()
            return {"success": True, "id": new_id, "message": "Annonce publiée !"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/cars")
def get_cars(limit: int = 1000):
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM cars ORDER BY created_at DESC LIMIT :limit"), {"limit": limit}).fetchall()
            return [{
                "id": r.id, "make": r.marque, "model": r.modele or "", "mileage": r.kilometrage, "fuel": r.energie,
                "transmission": r.boite_vitesse, "puissance_fiscale": r.puissance_fiscale, "carrosserie": r.carrosserie,
                "statut": r.statut or "disponible", "location": r.gouvernorat, "price": r.prix or 0,
                "year": 2026 - (r.age_voiture or 0), "image": r.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                "images": parse_images(r.images), "badge": "Nouveau", "description": r.description or ""
            } for r in rows]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/cars/{car_id}")
def get_car(car_id: int):
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT c.*, u.email AS vendeur_email FROM cars c LEFT JOIN users u ON c.user_id = u.id WHERE c.id = :id"), {"id": car_id}).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Annonce introuvable")
            imgs = parse_images(row.images)
            return {
                "id": row.id, "make": row.marque, "model": row.modele or "", "mileage": row.kilometrage, "fuel": row.energie,
                "transmission": row.boite_vitesse, "puissance_fiscale": row.puissance_fiscale, "carrosserie": row.carrosserie,
                "location": row.gouvernorat, "statut": row.statut or "disponible", "price": row.prix or 0,
                "year": 2026 - (row.age_voiture or 0), "image": imgs[0] if imgs else (row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800"),
                "badge": "Nouveau", "description": row.description or "", "couleur_exterieure": row.couleur_exterieure,
                "couleur_interieure": row.couleur_interieure, "sellerie": row.sellerie, "nombre_places": row.nombre_places,
                "nombre_portes": row.nombre_portes, "cylindree": row.cylindree, "vendeur_nom": row.vendeur_nom or "Vendeur",
                "vendeur_telephone": row.vendeur_telephone or None, "vendeur_email": row.vendeur_email or None,
                "user_id": row.user_id, "created_at": str(row.created_at), "images": imgs
            }
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/my-cars")
def get_my_cars(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM cars WHERE user_id = :uid ORDER BY created_at DESC"), {"uid": user_id}).fetchall()
            return [{
                "id": r.id, "make": r.marque, "model": r.modele or "", "mileage": r.kilometrage, "fuel": r.energie,
                "transmission": r.boite_vitesse, "carrosserie": r.carrosserie, "location": r.gouvernorat,
                "statut": r.statut or "disponible", "price": r.prix or 0, "year": 2026 - (r.age_voiture or 0),
                "image": r.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                "images": parse_images(r.images), "badge": "Mon annonce", "description": r.description or "", "created_at": str(r.created_at)
            } for r in rows]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/cars/{car_id}/statut")
def update_car_statut(car_id: int, data: CarStatut, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT user_id FROM cars WHERE id = :id"), {"id": car_id}).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Annonce introuvable")
            if row.user_id != user_id: raise HTTPException(status_code=403, detail="Non autorisé")
            if data.statut not in ["disponible", "vendue"]: raise HTTPException(status_code=400, detail="Statut invalide")
            conn.execute(text("UPDATE cars SET statut = :statut WHERE id = :id"), {"statut": data.statut, "id": car_id})
            conn.commit()
            return {"success": True, "statut": data.statut}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cars/{car_id}")
def delete_car(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT user_id FROM cars WHERE id = :id"), {"id": car_id}).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Annonce introuvable")
            if row.user_id != user_id: raise HTTPException(status_code=403, detail="Non autorisé")
            conn.execute(text("DELETE FROM cars WHERE id = :id"), {"id": car_id})
            conn.commit()
            return {"success": True, "message": "Annonce supprimée"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/cars/{car_id}/view")
def record_view(car_id: int, request: Request):
    try:
        viewer_ip = request.client.host
        with engine.connect() as conn:
            existing = conn.execute(text("""
                SELECT id FROM car_views WHERE car_id = :car_id AND viewer_ip = :ip
                AND viewed_at > NOW() - INTERVAL '1 hour'
            """), {"car_id": car_id, "ip": viewer_ip}).fetchone()
            if not existing:
                conn.execute(text("INSERT INTO car_views (car_id, viewer_ip) VALUES (:car_id, :ip)"), {"car_id": car_id, "ip": viewer_ip})
                conn.commit()
        return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/register")
async def register(request: Request):
    try:
        body_bytes = await request.body()
        try:
            body_str = body_bytes.decode('utf-8')
        except UnicodeDecodeError:
            body_str = body_bytes.decode('utf-8', errors='ignore')
        data = json.loads(body_str)
        nom = data.get("nom", "").strip()
        prenom = data.get("prenom", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        telephone = data.get("telephone", "")
        if not all([nom, prenom, email, password]): raise HTTPException(status_code=400, detail="Tous les champs sont requis")

        with engine.connect() as conn:
            if conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email}).fetchone():
                raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
            result = conn.execute(text("""
                INSERT INTO users (nom, prenom, email, password_hash, telephone)
                VALUES (:nom, :prenom, :email, :hash, :tel) RETURNING id, nom, prenom, email, avatar_url
            """), {"nom": nom, "prenom": prenom, "email": email, "hash": hash_password(password), "tel": telephone})
            conn.commit()
            row = result.fetchone()
            token = create_token({"sub": str(row.id), "email": row.email})
            return {"access_token": token, "token_type": "bearer", "user": {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email, "avatar_url": row.avatar_url or ""}}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.post("/auth/login")
async def login(request: Request):
    try:
        body_bytes = await request.body()
        try:
            body_str = body_bytes.decode('utf-8')
        except UnicodeDecodeError:
            body_str = body_bytes.decode('utf-8', errors='ignore')
        data = json.loads(body_str)
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()
        if not email or not password: raise HTTPException(status_code=400, detail="Email et mot de passe requis")

        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
            if not row or not verify_password(password, row.password_hash):
                raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
            token = create_token({"sub": str(row.id), "email": row.email})
            return {"access_token": token, "token_type": "bearer", "user": {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email, "avatar_url": row.avatar_url or ""}}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@app.get("/auth/me")
def get_me(authorization: str = Header(None)):
    try:
        user_id = get_user_id_from_token(authorization)
        with engine.connect() as conn:
            row = conn.execute(text("SELECT id, nom, prenom, email FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email}
    except HTTPException: raise
    except Exception: raise HTTPException(status_code=401, detail="Token invalide")

@app.get("/auth/profile")
def get_profile(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email, "telephone": row.telephone or "", "avatar_url": row.avatar_url or "", "gouvernorat": row.gouvernorat or "", "bio": row.bio or "", "created_at": str(row.created_at)}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/auth/profile")
def update_profile(data: UserUpdate, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            user = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not user: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            email_changed, password_changed = data.email is not None and data.email != user.email, bool(data.new_password)
            
            if (email_changed or password_changed) and not data.current_password:
                raise HTTPException(status_code=400, detail="Mot de passe actuel requis")
            if (email_changed or password_changed) and not verify_password(data.current_password or "", user.password_hash):
                raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
            
            if email_changed:
                if conn.execute(text("SELECT id FROM users WHERE email = :email AND id != :id"), {"email": data.email, "id": user_id}).fetchone():
                    raise HTTPException(status_code=400, detail="Email déjà utilisé")
                conn.execute(text("UPDATE users SET email = :email WHERE id = :id"), {"email": data.email, "id": user_id})
            
            if password_changed:
                conn.execute(text("UPDATE users SET password_hash = :hash WHERE id = :id"), {"hash": hash_password(data.new_password), "id": user_id})
            
            conn.execute(text("""
                UPDATE users SET nom=COALESCE(:nom,nom), prenom=COALESCE(:prenom,prenom), 
                telephone=COALESCE(:tel,telephone), gouvernorat=COALESCE(:gouv,gouvernorat), 
                bio=COALESCE(:bio,bio), updated_at=NOW() WHERE id=:id
            """), {"nom": data.nom, "prenom": data.prenom, "tel": data.telephone, "gouv": data.gouvernorat, "bio": data.bio, "id": user_id})
            conn.commit()
            row = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            return {
                "success": True, "id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email,
                "telephone": row.telephone or "", "avatar_url": row.avatar_url or "",
                "gouvernorat": row.gouvernorat or "", "bio": row.bio or "",
                "access_token": create_token({"sub": str(row.id), "email": row.email}) if email_changed else None
            }
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/avatar")
async def update_avatar(file: UploadFile = File(...), authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]: raise HTTPException(status_code=400, detail="Format invalide")
        filename = f"avatar_{user_id}_{uuid.uuid4()}.{ext}"
        with open(f"static/images/{filename}", "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        url = f"{BASE_URL}/static/images/{filename}"
        with engine.connect() as conn:
            conn.execute(text("UPDATE users SET avatar_url = :url WHERE id = :id"), {"url": url, "id": user_id})
            conn.commit()
        return {"success": True, "avatar_url": url}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/auth/password")
def change_password(data: ChangePassword, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT password_hash FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not row: raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            if not verify_password(data.current_password, row.password_hash): raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
            conn.execute(text("UPDATE users SET password_hash = :hash WHERE id = :id"), {"hash": hash_password(data.new_password), "id": user_id})
            conn.commit()
            return {"success": True, "message": "Mot de passe mis à jour"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages")
def send_message(msg: MessageCreate, authorization: str = Header(None)):
    sender_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conv = conn.execute(text("""
                SELECT id FROM conversations 
                WHERE (user1_id = :u1 AND user2_id = :u2 AND car_id = :car) 
                   OR (user1_id = :u2 AND user2_id = :u1 AND car_id = :car)
            """), {"u1": sender_id, "u2": msg.receiver_id, "car": msg.car_id}).fetchone()
            if not conv:
                conv_id = conn.execute(text("""
                    INSERT INTO conversations (user1_id, user2_id, car_id) 
                    VALUES (:u1, :u2, :car) RETURNING id
                """), {"u1": sender_id, "u2": msg.receiver_id, "car": msg.car_id}).fetchone()[0]
            else: conv_id = conv[0]
            conn.execute(text("""
                INSERT INTO messages (sender_id, receiver_id, car_id, content) 
                VALUES (:s, :r, :c, :content)
            """), {"s": sender_id, "r": msg.receiver_id, "c": msg.car_id, "content": msg.content})
            conn.commit()
            return {"success": True, "conversation_id": conv_id}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations")
def get_conversations(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT c.id, c.car_id, ca.marque, ca.modele, ca.image_url,
                    CASE WHEN c.user1_id = :uid THEN c.user2_id ELSE c.user1_id END AS other_id,
                    CASE WHEN c.user1_id = :uid THEN u2.prenom ELSE u1.prenom END AS other_prenom,
                    CASE WHEN c.user1_id = :uid THEN u2.nom ELSE u1.nom END AS other_nom,
                    (SELECT content FROM messages m WHERE m.car_id = c.car_id AND ((m.sender_id = :uid AND m.receiver_id != :uid) OR (m.receiver_id = :uid AND m.sender_id != :uid)) ORDER BY m.created_at DESC LIMIT 1) AS last_message,
                    (SELECT created_at FROM messages m WHERE m.car_id = c.car_id AND ((m.sender_id = :uid AND m.receiver_id != :uid) OR (m.receiver_id = :uid AND m.sender_id != :uid)) ORDER BY m.created_at DESC LIMIT 1) AS last_at,
                    (SELECT COUNT(*) FROM messages m WHERE m.receiver_id = :uid AND m.car_id = c.car_id AND m.is_read = FALSE) AS unread_count
                FROM conversations c JOIN users u1 ON c.user1_id = u1.id JOIN users u2 ON c.user2_id = u2.id JOIN cars ca ON c.car_id = ca.id
                WHERE c.user1_id = :uid OR c.user2_id = :uid ORDER BY last_at DESC NULLS LAST
            """), {"uid": user_id}).fetchall()
            return [{"id": r.id, "car_id": r.car_id, "marque": r.marque, "modele": r.modele or "", "image_url": r.image_url or f"{BASE_URL}/static/default.jpg", "other_id": r.other_id, "other_prenom": r.other_prenom, "other_nom": r.other_nom, "last_message": r.last_message or "", "last_at": str(r.last_at) if r.last_at else "", "unread_count": r.unread_count} for r in rows]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{other_id}/{car_id}")
def get_messages(other_id: int, car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE messages SET is_read = TRUE WHERE receiver_id = :uid AND sender_id = :other AND car_id = :car"), {"uid": user_id, "other": other_id, "car": car_id})
            conn.commit()
            rows = conn.execute(text("""
                SELECT m.id, m.sender_id, m.receiver_id, m.content, m.is_read, m.created_at, u.prenom AS sender_prenom 
                FROM messages m JOIN users u ON m.sender_id = u.id 
                WHERE m.car_id = :car AND ((m.sender_id = :uid AND m.receiver_id = :other) OR (m.sender_id = :other AND m.receiver_id = :uid)) 
                ORDER BY m.created_at ASC
            """), {"uid": user_id, "other": other_id, "car": car_id}).fetchall()
            return [{"id": r.id, "sender_id": r.sender_id, "receiver_id": r.receiver_id, "content": r.content, "is_read": r.is_read, "created_at": str(r.created_at), "sender_prenom": r.sender_prenom, "is_mine": r.sender_id == user_id} for r in rows]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/unread-count")
def get_unread_count(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            return {"unread": conn.execute(text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid AND is_read = FALSE"), {"uid": user_id}).fetchone().count}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/stats")
def get_dashboard_stats(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            total_annonces = conn.execute(text("SELECT COUNT(*) AS count FROM cars WHERE user_id = :uid"), {"uid": user_id}).fetchone().count
            messages_non_lus = conn.execute(text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid AND is_read = FALSE"), {"uid": user_id}).fetchone().count
            total_messages = conn.execute(text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid"), {"uid": user_id}).fetchone().count
            total_vues = conn.execute(text("SELECT COUNT(*) AS count FROM car_views cv JOIN cars c ON cv.car_id = c.id WHERE c.user_id = :uid"), {"uid": user_id}).fetchone().count
            vues_7j = conn.execute(text("""
                SELECT DATE(cv.viewed_at) AS jour, COUNT(*) AS vues FROM car_views cv 
                JOIN cars c ON cv.car_id = c.id WHERE c.user_id = :uid AND cv.viewed_at > NOW() - INTERVAL '7 days' 
                GROUP BY DATE(cv.viewed_at) ORDER BY jour ASC
            """), {"uid": user_id}).fetchall()
            annonces_vues = conn.execute(text("""
                SELECT c.id, c.marque, c.modele, c.prix, c.image_url, c.created_at, COUNT(cv.id) AS vues 
                FROM cars c LEFT JOIN car_views cv ON cv.car_id = c.id 
                WHERE c.user_id = :uid GROUP BY c.id ORDER BY vues DESC LIMIT 5
            """), {"uid": user_id}).fetchall()
            annonces_par_mois = conn.execute(text("""
                SELECT TO_CHAR(created_at, 'Mon') AS mois, COUNT(*) AS count FROM cars 
                WHERE user_id = :uid AND created_at > NOW() - INTERVAL '6 months' 
                GROUP BY TO_CHAR(created_at, 'Mon'), DATE_TRUNC('month', created_at) ORDER BY DATE_TRUNC('month', created_at) ASC
            """), {"uid": user_id}).fetchall()
            return {
                "total_annonces": total_annonces, "total_messages": total_messages, "messages_non_lus": messages_non_lus, "total_vues": total_vues,
                "vues_7j": [{"jour": str(r.jour), "vues": r.vues} for r in vues_7j],
                "annonces_top": [{"id": r.id, "marque": r.marque, "modele": r.modele or "", "prix": r.prix or 0, "image_url": r.image_url or f"{BASE_URL}/static/default.jpg", "created_at": str(r.created_at), "vues": r.vues} for r in annonces_vues],
                "annonces_par_mois": [{"mois": r.mois, "count": r.count} for r in annonces_par_mois]
            }
    except Exception as e:
        print(f"❌ DASHBOARD ERROR: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/favorites")
def get_favorites(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT c.* FROM favorites f JOIN cars c ON f.car_id = c.id 
                WHERE f.user_id = :uid ORDER BY f.created_at DESC
            """), {"uid": user_id}).fetchall()
            return [{
                "id": r.id, "make": r.marque, "model": r.modele or "", "mileage": r.kilometrage, "fuel": r.energie,
                "transmission": r.boite_vitesse, "carrosserie": r.carrosserie, "statut": r.statut or "disponible",
                "location": r.gouvernorat, "price": r.prix or 0, "year": 2026 - (r.age_voiture or 0),
                "image": r.image_url or f"{BASE_URL}/static/default.jpg", "images": parse_images(r.images),
                "description": r.description or "", "created_at": str(r.created_at)
            } for r in rows]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/favorites/{car_id}")
def add_favorite(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            if not conn.execute(text("SELECT id FROM favorites WHERE user_id = :uid AND car_id = :car"), {"uid": user_id, "car": car_id}).fetchone():
                conn.execute(text("INSERT INTO favorites (user_id, car_id) VALUES (:uid, :car)"), {"uid": user_id, "car": car_id})
                conn.commit()
                return {"success": True, "message": "Ajouté aux favoris"}
            return {"success": True, "message": "Déjà en favori"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/favorites/{car_id}")
def remove_favorite(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM favorites WHERE user_id = :uid AND car_id = :car"), {"uid": user_id, "car": car_id})
            conn.commit()
            return {"success": True, "message": "Retiré des favoris"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/favorites/ids")
def get_favorite_ids(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            return {"ids": [r.car_id for r in conn.execute(text("SELECT car_id FROM favorites WHERE user_id = :uid"), {"uid": user_id}).fetchall()]}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications")
def get_notifications(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT n.id, n.type, n.title, n.body, n.is_read, n.created_at, n.car_id, 
                       c.marque, c.modele, c.image_url, c.gouvernorat 
                FROM notifications n LEFT JOIN cars c ON n.car_id = c.id 
                WHERE n.user_id = :uid ORDER BY n.created_at DESC LIMIT 30
            """), {"uid": user_id}).fetchall()
            return [{"id": r.id, "type": r.type, "title": r.title, "body": r.body, "is_read": r.is_read, "created_at": str(r.created_at), "car_id": r.car_id, "image_url": r.image_url or f"{BASE_URL}/static/default.jpg", "marque": r.marque or "", "modele": r.modele or "", "gouvernorat": r.gouvernorat or ""} for r in rows]
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications/unread-count")
def get_notif_unread_count(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            return {"unread": conn.execute(text("SELECT COUNT(*) AS count FROM notifications WHERE user_id = :uid AND is_read = FALSE"), {"uid": user_id}).fetchone().count}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE notifications SET is_read = TRUE WHERE id = :id AND user_id = :uid"), {"id": notif_id, "uid": user_id})
            conn.commit()
            return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/notifications/read-all")
def mark_all_notifications_read(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE notifications SET is_read = TRUE WHERE user_id = :uid AND is_read = FALSE"), {"uid": user_id})
            conn.commit()
            return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.delete("/notifications")
def delete_all_notifications(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM notifications WHERE user_id = :uid"), {"uid": user_id})
            conn.commit()
            return {"success": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/preferences")
def get_preferences(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM user_preferences WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            if not row: return {"marques": [], "carrosseries": [], "energies": [], "gouvernorats": [], "budget_min": 0, "budget_max": 999999, "km_max": 999999, "age_max": 20, "notify_enabled": True, "has_preferences": False}
            return {"marques": list(row.marques) if row.marques else [], "carrosseries": list(row.carrosseries) if row.carrosseries else [], "energies": list(row.energies) if row.energies else [], "gouvernorats": list(row.gouvernorats) if row.gouvernorats else [], "budget_min": row.budget_min or 0, "budget_max": row.budget_max or 999999, "km_max": row.km_max or 999999, "age_max": row.age_max or 20, "notify_enabled": row.notify_enabled, "has_preferences": True}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/preferences")
def save_preferences(data: UserPreferences, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            existing = conn.execute(text("SELECT id FROM user_preferences WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            params = {"uid": user_id, "marques": data.marques, "carrosseries": data.carrosseries, "energies": data.energies, "gouvernorats": data.gouvernorats, "budget_min": data.budget_min, "budget_max": data.budget_max, "km_max": data.km_max, "age_max": data.age_max, "notify_enabled": data.notify_enabled}
            if existing:
                conn.execute(text("""
                    UPDATE user_preferences SET marques=:marques, carrosseries=:carrosseries, energies=:energies, 
                    gouvernorats=:gouvernorats, budget_min=:budget_min, budget_max=:budget_max, km_max=:km_max, 
                    age_max=:age_max, notify_enabled=:notify_enabled, updated_at=NOW() WHERE user_id=:uid
                """), params)
            else:
                conn.execute(text("""
                    INSERT INTO user_preferences (user_id, marques, carrosseries, energies, gouvernorats, budget_min, budget_max, km_max, age_max, notify_enabled) 
                    VALUES (:uid, :marques, :carrosseries, :energies, :gouvernorats, :budget_min, :budget_max, :km_max, :age_max, :notify_enabled)
                """), params)
            conn.commit()
            return {"success": True, "message": "Preferences sauvegardees"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/notification-preferences")
def get_notif_preferences(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM notification_preferences WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            if not row: return {"budget_min": 0, "budget_max": 9999999, "marques": [], "energies": [], "carrosseries": [], "gouvernorats": [], "kilometrage_max": 999999, "annee_min": 0, "notifications_actives": True}
            return {"budget_min": row.budget_min or 0, "budget_max": row.budget_max or 9999999, "marques": list(row.marques) if row.marques else [], "energies": list(row.energies) if row.energies else [], "carrosseries": list(row.carrosseries) if row.carrosseries else [], "gouvernorats": list(row.gouvernorats) if row.gouvernorats else [], "kilometrage_max": row.kilometrage_max or 999999, "annee_min": row.annee_min or 0, "notifications_actives": row.notifications_actives}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.put("/notification-preferences")
def save_notif_preferences(data: NotifPreferences, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            existing = conn.execute(text("SELECT id FROM notification_preferences WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            params = {"uid": user_id, "budget_min": data.budget_min, "budget_max": data.budget_max, "marques": data.marques, "energies": data.energies, "carrosseries": data.carrosseries, "gouvernorats": data.gouvernorats, "kilometrage_max": data.kilometrage_max, "annee_min": data.annee_min, "notifications_actives": data.notifications_actives}
            if existing: 
                conn.execute(text("""
                    UPDATE notification_preferences SET budget_min=:budget_min, budget_max=:budget_max, marques=:marques, 
                    energies=:energies, carrosseries=:carrosseries, gouvernorats=:gouvernorats, kilometrage_max=:kilometrage_max, 
                    annee_min=:annee_min, notifications_actives=:notifications_actives, updated_at=NOW() WHERE user_id=:uid
                """), params)
            else: 
                conn.execute(text("""
                    INSERT INTO notification_preferences (user_id, budget_min, budget_max, marques, energies, carrosseries, gouvernorats, kilometrage_max, annee_min, notifications_actives) 
                    VALUES (:uid, :budget_min, :budget_max, :marques, :energies, :carrosseries, :gouvernorats, :kilometrage_max, :annee_min, :notifications_actives)
                """), params)
            conn.commit()
            return {"success": True, "message": "Préférences sauvegardées"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

if _ORM_AVAILABLE:
    @app.post("/register", response_model=Token)
    def register_oauth(user: UserCreate, db: Session = Depends(get_db)):
        if db.query(User).filter(User.email == user.email).first(): raise HTTPException(status_code=400, detail="Email déjà utilisé")
        new_user = User(full_name=user.full_name, email=user.email, password=auth_hash_password(user.password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"access_token": create_access_token({"sub": str(new_user.id), "email": new_user.email}), "token_type": "bearer", "user": new_user}

    @app.post("/login", response_model=Token)
    def login_oauth(credentials: UserLogin, db: Session = Depends(get_db)):
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not auth_verify_password(credentials.password, user.password): raise HTTPException(status_code=401, detail="Incorrect")
        return {"access_token": create_access_token({"sub": str(user.id), "email": user.email}), "token_type": "bearer", "user": user}

    @app.get("/me", response_model=UserOut)
    def get_me_oauth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        try: user_id = int(decode_token(token).get("sub"))
        except Exception: raise HTTPException(status_code=401, detail="Invalide")
        user = db.query(User).filter(User.id == user_id).first()
        if not user: raise HTTPException(status_code=404, detail="Non trouvé")
        return user
    

def _kaggle_url(path: str) -> str:
    base = (KAGGLE_API_URL or "").rstrip("/")
    return f"{base}{path}"



APP_3D_QUEUE_MAX = int(os.getenv("APP_3D_QUEUE_MAX", "4"))
APP_3D_STATUS_POLL_SEC = int(os.getenv("APP_3D_STATUS_POLL_SEC", "10"))
APP_3D_MAX_WAIT_SEC = int(os.getenv("APP_3D_MAX_WAIT_SEC", "3600"))
app_3d_queue = asyncio.Queue(maxsize=APP_3D_QUEUE_MAX)
app_3d_worker_task = None
app_3d_worker_lock = asyncio.Lock()
app_3d_jobs = {}
app_3d_jobs_lock = threading.Lock()


def _app_update_3d_job(job_id: str, payload: dict) -> None:
    with app_3d_jobs_lock:
        current = app_3d_jobs.get(job_id, {})
        if "created_at" not in current:
            current["created_at"] = time.time()
        current.update(payload)
        current["updated_at"] = time.time()
        app_3d_jobs[job_id] = current


def _app_get_3d_job(job_id: str):
    with app_3d_jobs_lock:
        return app_3d_jobs.get(job_id)


def _app_queue_position(job_id: str):
    try:
        queued_ids = [jid for jid, *_ in list(app_3d_queue._queue)]
        return queued_ids.index(job_id) + 1
    except ValueError:
        return None


def _app_remove_from_queue(job_id: str) -> None:
    try:
        app_3d_queue._queue = deque([item for item in app_3d_queue._queue if item[0] != job_id])
    except Exception:
        pass


def _app_finalize_3d_job(job_id: str, status: str, error: str | None = None) -> None:
    payload = {"status": status, "final": True, "ended_at": time.time()}
    if error:
        payload["error"] = error
    _app_update_3d_job(job_id, payload)
    _app_remove_from_queue(job_id)


async def _app_3d_worker_loop():
    while True:
        job_id, file_bytes, filename, content_type = await app_3d_queue.get()
        _app_update_3d_job(job_id, {"status": "submitting", "started_at": time.time()})
        try:
            submitted_ok = False
            files = {
                "file": (
                    filename or "upload",
                    file_bytes,
                    content_type or "application/octet-stream",
                )
            }
            try:
                async with httpx.AsyncClient(timeout=600.0) as client:
                    gen_resp = await client.post(_kaggle_url("/generate"), files=files, params={"job_id": job_id})
                    gen_resp.raise_for_status()
                    gen_data = gen_resp.json()
                submitted_ok = True
                _app_update_3d_job(
                    job_id,
                    {
                        "status": gen_data.get("status", "queued"),
                        "submitted": True,
                        "submitted_at": time.time(),
                    },
                )
            except Exception as e:
                _app_update_3d_job(
                    job_id,
                    {
                        "status": "submit_error",
                        "error": str(e),
                        "submitted": False,
                        "submitted_at": time.time(),
                    },
                )
            poll_started = time.monotonic()
            error_count = 0
            while True:
                if APP_3D_MAX_WAIT_SEC >= 0 and (time.monotonic() - poll_started) >= APP_3D_MAX_WAIT_SEC:
                    _app_finalize_3d_job(job_id, "timeout")
                    break
                try:
                    async with httpx.AsyncClient(timeout=600.0) as client:
                        status_resp = await client.get(_kaggle_url(f"/status/{job_id}"))
                        status_resp.raise_for_status()
                        status_data = status_resp.json()
                except Exception as e:
                    error_count += 1
                    _app_update_3d_job(
                        job_id,
                        {
                            "status": "status_error",
                            "error": str(e),
                            "status_error_count": error_count,
                        },
                    )
                    await asyncio.sleep(max(APP_3D_STATUS_POLL_SEC, 1))
                    continue

                status = status_data.get("status")
                error_count = 0
                _app_update_3d_job(job_id, {"status": status, "last_status": status_data})

                if status == "not_found" and not submitted_ok:
                    _app_finalize_3d_job(job_id, "failed_to_submit")
                    break

                if status == "failed":
                    _app_finalize_3d_job(job_id, "failed", status_data.get("error"))
                    break

                if status == "not_found":
                    _app_finalize_3d_job(job_id, "not_found")
                    break

                if status == "completed":
                    _app_finalize_3d_job(job_id, "completed")
                    break

                await asyncio.sleep(max(APP_3D_STATUS_POLL_SEC, 1))
        except Exception as e:
            _app_finalize_3d_job(job_id, "failed_to_submit", str(e))
        finally:
            app_3d_queue.task_done()


async def _ensure_app_3d_worker():
    global app_3d_worker_task
    async with app_3d_worker_lock:
        if app_3d_worker_task is None or app_3d_worker_task.done():
            app_3d_worker_task = asyncio.create_task(_app_3d_worker_loop())


@app.on_event("startup")
async def _startup_app_3d_queue():
    await _ensure_app_3d_worker()


@app.post("/process-3d")
async def process_image_to_3d(
    file: UploadFile = File(None),
    job_id: Optional[str] = None,
    wait: bool = False,
    download: bool = False,
    timeout_sec: int = 600,
    poll_interval: int = 10,
):
    if not KAGGLE_API_URL:
        raise HTTPException(status_code=503, detail="Kaggle API not configured")

    if file is None and not job_id:
        raise HTTPException(status_code=400, detail="Provide a file or job_id")

    if file is not None:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")

        job_id = job_id or str(uuid.uuid4())

        if app_3d_queue.full():
            raise HTTPException(status_code=429, detail="Queue is full. Try again later.")

        _app_update_3d_job(job_id, {"status": "queued_local", "queued_at": time.time()})
        await _ensure_app_3d_worker()
        try:
            app_3d_queue.put_nowait((job_id, file_bytes, file.filename, file.content_type))
        except asyncio.QueueFull:
            _app_update_3d_job(job_id, {"status": "rejected", "error": "Queue full"})
            raise HTTPException(status_code=429, detail="Queue is full. Try again later.")

        if not wait and not download:
            return {
                "job_id": job_id,
                "status": "queued",
                "position": _app_queue_position(job_id),
                "queue_size": app_3d_queue.qsize(),
                "next": f"/process-3d?job_id={job_id}",
            }

    if not job_id:
        raise HTTPException(status_code=400, detail="job_id is required")

    local = _app_get_3d_job(job_id)
    if not local:
        return {"job_id": job_id, "status": "not_found"}

    deadline = time.monotonic() + max(timeout_sec, 0)
    while True:
        local = _app_get_3d_job(job_id) or {}
        status = local.get("status") or "tracking"

        if status == "failed_to_submit":
            raise HTTPException(status_code=502, detail=f"Submission failed: {local.get('error')}")

        if status == "failed":
            raise HTTPException(status_code=500, detail=f"Generation failed: {local.get('error')}")

        if status == "completed":
            if download or wait:
                download_deadline = time.monotonic() + max(timeout_sec, 0)
                last_error = None
                while True:
                    try:
                        async with httpx.AsyncClient(timeout=600.0) as client:
                            download_resp = await client.get(_kaggle_url(f"/download/{job_id}"))
                        if download_resp.status_code == 200:
                            modelThreeD = str(DOWNLOAD_DIR / f"{job_id}.glb")
                            with open(modelThreeD, "wb") as f:
                                f.write(download_resp.content)

                            return FileResponse(
                                modelThreeD,
                                media_type="model/gltf-binary",
                                filename=f"{job_id}.glb",
                            )
                        last_error = f"Download not ready ({download_resp.status_code})"
                    except httpx.HTTPError as e:
                        last_error = str(e)

                    if timeout_sec >= 0 and time.monotonic() >= download_deadline:
                        return {"job_id": job_id, "status": "download_timeout", "error": last_error}

                    await asyncio.sleep(max(poll_interval, 1))

            return local.get("last_status") or {"job_id": job_id, "status": status}

        if not wait:
            response = {"job_id": job_id, "status": status}
            if status in {"queued_local", "submitting"}:
                response["position"] = _app_queue_position(job_id)
                response["queue_size"] = app_3d_queue.qsize()
            if local.get("last_status"):
                response["details"] = local.get("last_status")
            return response

        if timeout_sec >= 0 and time.monotonic() >= deadline:
            return {"job_id": job_id, "status": "timeout"}

        await asyncio.sleep(max(poll_interval, 1))


@app.get("/process-3d/in-progress")
async def process_3d_in_progress(job_id: str):
    local = _app_get_3d_job(job_id)
    if not local:
        return {"job_id": job_id, "exists": False, "in_progress": False, "status": "not_found"}

    status = local.get("status")
    in_progress = status in {"queued_local", "submitting", "queued", "processing", "tracking", "submitted", "status_error"}
    payload = {"job_id": job_id, "exists": True, "in_progress": in_progress, "status": status}
    if status in {"queued_local", "submitting"}:
        payload["position"] = _app_queue_position(job_id)
        payload["queue_size"] = app_3d_queue.qsize()
    return payload

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)