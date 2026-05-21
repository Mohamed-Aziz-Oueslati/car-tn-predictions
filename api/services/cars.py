import json

from sqlalchemy import text

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
