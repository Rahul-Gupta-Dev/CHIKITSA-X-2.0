import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import UserModel

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
DEV_FALLBACK_SECRET = "chikitsax-dev-secret-key-2026-sih"

def resolve_secret_key() -> str:
    """Validate and resolve SECRET_KEY with strict security enforcement in staging/production."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    raw_secret = os.getenv("SECRET_KEY", "").strip()
    if env in ["production", "staging"]:
        if not raw_secret or raw_secret in [DEV_FALLBACK_SECRET, "secret", "password", "changeme", "admin"]:
            raise RuntimeError(
                f"CRITICAL PRODUCTION SECURITY ERROR: Insecure or default SECRET_KEY in '{env}' environment. "
                "A unique, high-entropy SECRET_KEY of at least 32 characters must be provided via environment variables."
            )
        if len(raw_secret) < 32:
            raise RuntimeError(
                f"CRITICAL PRODUCTION SECURITY ERROR: SECRET_KEY in '{env}' environment is too short ({len(raw_secret)} chars). "
                "Must be at least 32 characters (256-bit entropy)."
            )
        return raw_secret
    return raw_secret if raw_secret else DEV_FALLBACK_SECRET

SECRET_KEY = resolve_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24))) # 24 hours default

security = HTTPBearer(auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()
    return f"{salt}${key}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored salt$hash format."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        salt, expected_key = hashed_password.split("$", 1)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()
        return secrets.compare_digest(key, expected_key)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[UserModel]:
    """Extract current user if valid Bearer token provided, otherwise return None."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("sub")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    return user

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> UserModel:
    """Require valid authenticated user from Bearer token."""
    user = get_current_user_optional(credentials, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_role(allowed_roles: List[str]):
    """Dependency factory ensuring current user has one of the required roles."""
    def role_checker(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, your role is '{user.role}'."
            )
        return user
    return role_checker
