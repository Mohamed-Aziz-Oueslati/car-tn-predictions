from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from api.security import get_user_id_from_token
from api.services.cars import parse_images
from api.state import BASE_URL, engine

router = APIRouter()

@router.get("/favorites")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/favorites/{car_id}")
def add_favorite(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            if not conn.execute(text("SELECT id FROM favorites WHERE user_id = :uid AND car_id = :car"), {"uid": user_id, "car": car_id}).fetchone():
                conn.execute(text("INSERT INTO favorites (user_id, car_id) VALUES (:uid, :car)"), {"uid": user_id, "car": car_id})
                conn.commit()
                return {"success": True, "message": "Ajouté aux favoris"}
            return {"success": True, "message": "Déjà en favori"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/favorites/{car_id}")
def remove_favorite(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM favorites WHERE user_id = :uid AND car_id = :car"), {"uid": user_id, "car": car_id})
            conn.commit()
            return {"success": True, "message": "Retiré des favoris"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/favorites/ids")
def get_favorite_ids(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            return {"ids": [r.car_id for r in conn.execute(text("SELECT car_id FROM favorites WHERE user_id = :uid"), {"uid": user_id}).fetchall()]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
