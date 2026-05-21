from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from api.schemas import NotifPreferences, UserPreferences
from api.security import get_user_id_from_token
from api.state import engine

router = APIRouter()

@router.get("/preferences")
def get_preferences(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM user_preferences WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            if not row:
                return {"marques": [], "carrosseries": [], "energies": [], "gouvernorats": [], "budget_min": 0, "budget_max": 999999, "km_max": 999999, "age_max": 20, "notify_enabled": True, "has_preferences": False}
            return {"marques": list(row.marques) if row.marques else [], "carrosseries": list(row.carrosseries) if row.carrosseries else [], "energies": list(row.energies) if row.energies else [], "gouvernorats": list(row.gouvernorats) if row.gouvernorats else [], "budget_min": row.budget_min or 0, "budget_max": row.budget_max or 999999, "km_max": row.km_max or 999999, "age_max": row.age_max or 20, "notify_enabled": row.notify_enabled, "has_preferences": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notification-preferences")
def get_notif_preferences(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM notification_preferences WHERE user_id = :uid"), {"uid": user_id}).fetchone()
            if not row:
                return {"budget_min": 0, "budget_max": 9999999, "marques": [], "energies": [], "carrosseries": [], "gouvernorats": [], "kilometrage_max": 999999, "annee_min": 0, "notifications_actives": True}
            return {"budget_min": row.budget_min or 0, "budget_max": row.budget_max or 9999999, "marques": list(row.marques) if row.marques else [], "energies": list(row.energies) if row.energies else [], "carrosseries": list(row.carrosseries) if row.carrosseries else [], "gouvernorats": list(row.gouvernorats) if row.gouvernorats else [], "kilometrage_max": row.kilometrage_max or 999999, "annee_min": row.annee_min or 0, "notifications_actives": row.notifications_actives}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notification-preferences")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
