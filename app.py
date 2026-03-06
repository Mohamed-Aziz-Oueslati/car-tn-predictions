from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import joblib
import os
import shutil
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# ─── Ajouts pour SQLAlchemy et OAuth2 ──────────────────────────────
from database import get_db, engine
from models import Base, User
from schemas import UserCreate, UserLogin, Token, UserOut
from auth import hash_password, verify_password, create_access_token, decode_token
import models

# Crée les tables au démarrage
Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ─── App ─────────────────────────────────────────────────────────────
app = FastAPI(title="Car Price Prediction API")

# ─── CORS ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost",
        "http://localhost:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files (images) ────────────────────────────────────────────
os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ─── Modèle ML ───────────────────────────────────────────────────────
MODEL_PATH = "best_model.pkl"
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None

# ─── Base de données PostgreSQL ───────────────────────────────────────
DATABASE_URL = "postgresql://postgres:yasmine123@localhost:5432/automarket"
engine = create_engine(DATABASE_URL)

# ─── Config JWT ───────────────────────────────────────────
SECRET_KEY = "ton_secret_key_change_moi"
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Schémas Pydantic ─────────────────────────────────────────
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

class UserRegister(BaseModel):
    nom: str
    prenom: str
    email: str
    password: str
    telephone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

# ─── Fonctions utilitaires Auth ─────────────────────────────
def hash_password(password: str) -> str:
    truncated = password[:72]
    return pwd_context.hash(truncated)

def verify_password(plain: str, hashed: str) -> bool:
    truncated = plain[:72]
    return pwd_context.verify(truncated, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ─── ENDPOINTS ────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "Car Price Prediction API",
        "endpoints": {
            "/health":        "Check API and model status",
            "/predict":       "Predict price for a single car (POST)",
            "/predict_batch": "Predict prices for multiple cars from CSV (POST)",
            "/cars":          "Get all car listings (GET) / Create listing (POST)",
            "/upload-image":  "Upload car image (POST)",
            "/auth/register": "Register new user (POST)",
            "/auth/login":    "Login user (POST)",
            "/auth/me":       "Get current user info (GET)"
        },
        "model_info": {
            "loaded": model is not None,
            "path": MODEL_PATH
        },
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    if model:
        return {"status": "ok", "model_loaded": True}
    return {"status": "degraded", "model_loaded": False}

# ─── Prédiction prix ─────────────────────────────────────────────────
@app.post("/predict")
def predict_price(data: CarData):
    if not model:
        raise HTTPException(status_code=503, detail="Model pipeline not available")
    try:
        input_df = pd.DataFrame([data.model_dump()])
        prediction = model.predict(input_df)[0]
        return {
            "predicted_price": float(prediction),
            "currency": "TND",
            "marque": data.Marque,
            "modele": data.Marque,
            "details": {
                "kilometrage": data.Kilometrage,
                "annee": 2026 - data.age_voiture if data.age_voiture else None,
                "energie": data.Energie
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error making prediction: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/predict_batch")
def predict_batch(request: dict):
    if not model:
        raise HTTPException(status_code=503, detail="Model pipeline not available")
    try:
        if "csv_data" not in request:
            raise HTTPException(status_code=400, detail="Request must include 'csv_data' field")
        import io
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
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# ─── Annonces voitures ───────────────────────────────────────────────
@app.post("/cars")
def create_car(car: CarAnnonce):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                INSERT INTO cars (
                    marque, modele, kilometrage, energie, boite_vitesse,
                    puissance_fiscale, puissance_ch, carrosserie, gouvernorat,
                    couleur_exterieure, couleur_interieure, sellerie,
                    nombre_places, nombre_portes, cylindree, age_voiture,
                    prix, description, image_url
                ) VALUES (
                    :marque, :modele, :kilometrage, :energie, :boite_vitesse,
                    :puissance_fiscale, :puissance_ch, :carrosserie, :gouvernorat,
                    :couleur_exterieure, :couleur_interieure, :sellerie,
                    :nombre_places, :nombre_portes, :cylindree, :age_voiture,
                    :prix, :description, :image_url
                ) RETURNING id
            """), car.model_dump())
            conn.commit()
            new_id = result.fetchone()[0]
            return {"success": True, "id": new_id, "message": "Annonce publiée avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cars")
def get_cars(limit: int = 1000):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM cars
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"limit": limit})
            rows = result.fetchall()
            cars = []
            for row in rows:
                cars.append({
                    "id":                row.id,
                    "make":              row.marque,
                    "model":             row.modele or "",
                    "mileage":           row.kilometrage,
                    "fuel":              row.energie,
                    "transmission":      row.boite_vitesse,
                    "puissance_fiscale": row.puissance_fiscale,
                    "carrosserie":       row.carrosserie,
                    "location":          row.gouvernorat,
                    "price":             row.prix or 0,
                    "year":              2026 - (row.age_voiture or 0),
                    "image":             row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                    "badge":             "Nouveau",
                    "description":       row.description or "",
                })
            return cars
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cars/{car_id}")
def get_car(car_id: int):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM cars WHERE id = :id"), {"id": car_id})
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Annonce introuvable")
            return {
                "id":                row.id,
                "make":              row.marque,
                "model":             row.modele or "",
                "mileage":           row.kilometrage,
                "fuel":              row.energie,
                "transmission":      row.boite_vitesse,
                "puissance_fiscale": row.puissance_fiscale,
                "carrosserie":       row.carrosserie,
                "location":          row.gouvernorat,
                "price":             row.prix or 0,
                "year":              2026 - (row.age_voiture or 0),
                "image":             row.image_url or "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
                "badge":             "Nouveau",
                "description":       row.description or "",
                "couleur_exterieure": row.couleur_exterieure,
                "couleur_interieure": row.couleur_interieure,
                "sellerie":           row.sellerie,
                "nombre_places":      row.nombre_places,
                "nombre_portes":      row.nombre_portes,
                "cylindree":          row.cylindree,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Upload image ────────────────────────────────────────────────────
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        allowed = ["jpg", "jpeg", "png", "webp"]
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté. Utilisez: {', '.join(allowed)}"
            )
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "image_url": f"http://localhost:8000/static/images/{filename}",
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Auth Endpoints ────────────────────────────────────────────────
@app.post("/auth/register")
def register(user: UserRegister):
    try:
        with engine.connect() as conn:
            existing = conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user.email}
            ).fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
            result = conn.execute(text("""
                INSERT INTO users (nom, prenom, email, password_hash, telephone)
                VALUES (:nom, :prenom, :email, :password_hash, :telephone)
                RETURNING id, nom, prenom, email
            """), {
                "nom":           user.nom,
                "prenom":        user.prenom,
                "email":         user.email,
                "password_hash": hash_password(user.password),
                "telephone":     user.telephone,
            })
            conn.commit()
            row = result.fetchone()
            token = create_token({"sub": str(row.id), "email": row.email})
            return {
                "access_token": token,
                "token_type":   "bearer",
                "user": {
                    "id":     row.id,
                    "nom":    row.nom,
                    "prenom": row.prenom,
                    "email":  row.email,
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login")
def login(user: UserLogin):
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": user.email}
            ).fetchone()
            if not row or not verify_password(user.password, row.password_hash):
                raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
            token = create_token({"sub": str(row.id), "email": row.email})
            return {
                "access_token": token,
                "token_type":   "bearer",
                "user": {
                    "id":     row.id,
                    "nom":    row.nom,
                    "prenom": row.prenom,
                    "email":  row.email,
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/me")
def get_me(authorization: str = None):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token manquant")
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, nom, prenom, email FROM users WHERE id = :id"),
                {"id": int(user_id)}
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")

# ─── OAuth2 avec SQLAlchemy ────────────────────────────────────────
@app.post("/register", response_model=Token)
def register_oauth(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
    return {"access_token": token, "token_type": "bearer", "user": new_user}

@app.post("/login", response_model=Token)
def login_oauth(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user}

@app.get("/me", response_model=UserOut)
def get_me_oauth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

# ─── Run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)