from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import text

from api.schemas import MessageCreate
from api.security import get_user_id_from_token
from api.state import BASE_URL, engine

router = APIRouter()

@router.post("/messages")
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
            else:
                conv_id = conv[0]
            conn.execute(text("""
                INSERT INTO messages (sender_id, receiver_id, car_id, content) 
                VALUES (:s, :r, :c, :content)
            """), {"s": sender_id, "r": msg.receiver_id, "c": msg.car_id, "content": msg.content})
            conn.commit()
            return {"success": True, "conversation_id": conv_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{other_id}/{car_id}")
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
def get_unread_count(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            return {"unread": conn.execute(text("SELECT COUNT(*) AS count FROM messages WHERE receiver_id = :uid AND is_read = FALSE"), {"uid": user_id}).fetchone().count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
