import json
import shutil
import uuid

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.orm import ORM_AVAILABLE
from api.schemas import ChangePassword, UserUpdate
from api.security import create_token, get_user_id_from_token, hash_password, verify_password
from api.state import BASE_URL, engine

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

if ORM_AVAILABLE:
    from api.orm import (
        Token as OrmToken,
        User as OrmUser,
        UserCreate as OrmUserCreate,
        UserLogin as OrmUserLogin,
        UserOut as OrmUserOut,
        create_access_token,
        decode_token,
        get_db,
        hash_password as orm_hash_password,
        verify_password as orm_verify_password,
    )

@router.post("/auth/register")
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
        if not all([nom, prenom, email, password]):
            raise HTTPException(status_code=400, detail="Tous les champs sont requis")

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.post("/auth/login")
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
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email et mot de passe requis")

        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
            if not row or not verify_password(password, row.password_hash):
                raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
            token = create_token({"sub": str(row.id), "email": row.email})
            return {"access_token": token, "token_type": "bearer", "user": {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email, "avatar_url": row.avatar_url or ""}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")

@router.get("/auth/me")
def get_me(authorization: str = Header(None)):
    try:
        user_id = get_user_id_from_token(authorization)
        with engine.connect() as conn:
            row = conn.execute(text("SELECT id, nom, prenom, email FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")

@router.get("/auth/profile")
def get_profile(authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            return {"id": row.id, "nom": row.nom, "prenom": row.prenom, "email": row.email, "telephone": row.telephone or "", "avatar_url": row.avatar_url or "", "gouvernorat": row.gouvernorat or "", "bio": row.bio or "", "created_at": str(row.created_at)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/auth/profile")
def update_profile(data: UserUpdate, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            user = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auth/avatar")
async def update_avatar(file: UploadFile = File(...), authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            raise HTTPException(status_code=400, detail="Format invalide")
        filename = f"avatar_{user_id}_{uuid.uuid4()}.{ext}"
        with open(f"static/images/{filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        url = f"{BASE_URL}/static/images/{filename}"
        with engine.connect() as conn:
            conn.execute(text("UPDATE users SET avatar_url = :url WHERE id = :id"), {"url": url, "id": user_id})
            conn.commit()
        return {"success": True, "avatar_url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/auth/password")
def change_password(data: ChangePassword, authorization: str = Header(None)):
    user_id = get_user_id_from_token(authorization)
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT password_hash FROM users WHERE id = :id"), {"id": user_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur introuvable")
            if not verify_password(data.current_password, row.password_hash):
                raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
            conn.execute(text("UPDATE users SET password_hash = :hash WHERE id = :id"), {"hash": hash_password(data.new_password), "id": user_id})
            conn.commit()
            return {"success": True, "message": "Mot de passe mis à jour"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if ORM_AVAILABLE:
    @router.post("/register", response_model=OrmToken)
    def register_oauth(user: OrmUserCreate, db: Session = Depends(get_db)):
        if db.query(OrmUser).filter(OrmUser.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
        new_user = OrmUser(full_name=user.full_name, email=user.email, password=orm_hash_password(user.password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"access_token": create_access_token({"sub": str(new_user.id), "email": new_user.email}), "token_type": "bearer", "user": new_user}

    @router.post("/login", response_model=OrmToken)
    def login_oauth(credentials: OrmUserLogin, db: Session = Depends(get_db)):
        user = db.query(OrmUser).filter(OrmUser.email == credentials.email).first()
        if not user or not orm_verify_password(credentials.password, user.password):
            raise HTTPException(status_code=401, detail="Incorrect")
        return {"access_token": create_access_token({"sub": str(user.id), "email": user.email}), "token_type": "bearer", "user": user}

    @router.get("/me", response_model=OrmUserOut)
    def get_me_oauth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        try:
            user_id = int(decode_token(token).get("sub"))
        except Exception:
            raise HTTPException(status_code=401, detail="Invalide")
        user = db.query(OrmUser).filter(OrmUser.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Non trouvé")
        return user
