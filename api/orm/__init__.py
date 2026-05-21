ORM_AVAILABLE = False

try:
    from .database import get_db, engine as orm_engine
    from .models import Base, User
    from .schemas import UserCreate, UserLogin, UserOut, Token
    from .auth import hash_password, verify_password, create_access_token, decode_token

    Base.metadata.create_all(bind=orm_engine)
    ORM_AVAILABLE = True
except ImportError:
    ORM_AVAILABLE = False
