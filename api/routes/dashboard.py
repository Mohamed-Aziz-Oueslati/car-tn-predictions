from fastapi import APIRouter, Header, HTTPException
import traceback
from sqlalchemy import text

from api.security import get_user_id_from_token
from api.state import BASE_URL, engine

router = APIRouter()

@router.get("/dashboard/stats")
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
