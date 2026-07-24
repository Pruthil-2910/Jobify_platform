import jwt
import uuid
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from cryptography.fernet import Fernet

from app.core.config import settings

pwd_hash = PasswordHash.recommended()
_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


# ── Password hashing ──
def hash_password(plain_password: str) -> str:
    return pwd_hash.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_hash.verify(plain_password, hashed_password)




# ── API key encryption/decryption ──
def encrypt_api_key(plain_key: str) -> str:
    return _fernet.encrypt(plain_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    return _fernet.decrypt(encrypted_key.encode()).decode()




# ── JWT tokens (pyjwt) ──
def create_access_token(user_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "iat": now, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None