import shutil
import uuid

from fastapi import APIRouter, File, Header, HTTPException, Request, UploadFile
from sqlalchemy import text

from api.schemas import CarAnnonce, CarStatut
from api.security import get_user_id_from_token
from api.services.cars import create_notifications_new_car, parse_images
from api.state import BASE_URL, engine

router = APIRouter()

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        allowed = ["jpg", "jpeg", "png", "webp"]
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail="Format non supporté.")
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"static/images/{filename}"
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"image_url": f"{BASE_URL}/static/images/{filename}", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cars")
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cars")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cars/{car_id}")
def get_car(car_id: int):
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT c.*, u.email AS vendeur_email FROM cars c LEFT JOIN users u ON c.user_id = u.id WHERE c.id = :id"), {"id": car_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Annonce introuvable")
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-cars")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/cars/{car_id}/statut")
def update_car_statut(car_id: int, data: CarStatut, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT user_id FROM cars WHERE id = :id"), {"id": car_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Annonce introuvable")
            if row.user_id != user_id:
                raise HTTPException(status_code=403, detail="Non autorisé")
            if data.statut not in ["disponible", "vendue"]:
                raise HTTPException(status_code=400, detail="Statut invalide")
            conn.execute(text("UPDATE cars SET statut = :statut WHERE id = :id"), {"statut": data.statut, "id": car_id})
            conn.commit()
            return {"success": True, "statut": data.statut}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cars/{car_id}")
def delete_car(car_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT user_id FROM cars WHERE id = :id"), {"id": car_id}).fetchone()
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

@router.post("/cars/{car_id}/view")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
