from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from api.security import get_user_id_from_token
from api.state import BASE_URL, engine

router = APIRouter()

@router.get("/notifications")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/unread-count")
def get_notif_unread_count(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            return {"unread": conn.execute(text("SELECT COUNT(*) AS count FROM notifications WHERE user_id = :uid AND is_read = FALSE"), {"uid": user_id}).fetchone().count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notifications/{notif_id}/read")
def mark_notification_read(notif_id: int, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE notifications SET is_read = TRUE WHERE id = :id AND user_id = :uid"), {"id": notif_id, "uid": user_id})
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notifications/read-all")
def mark_all_notifications_read(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("UPDATE notifications SET is_read = TRUE WHERE user_id = :uid AND is_read = FALSE"), {"uid": user_id})
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notifications")
def delete_all_notifications(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM notifications WHERE user_id = :uid"), {"uid": user_id})
            conn.commit()
            return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
