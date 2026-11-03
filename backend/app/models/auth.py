import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from app.database import Base

class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    family_id = Column(String(64), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    replaced_by = Column(String(64), nullable=True)

class PasswordResetTokenModel(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class HospitalInvitationModel(Base):
    __tablename__ = "hospital_invitations"

    id = Column(String(64), primary_key=True, index=True)
    hospital_id = Column(String(64), ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(64), unique=True, nullable=False, index=True)
    role = Column(String(32), nullable=False) # 'DOCTOR', 'HOSPITAL_STAFF', 'RECEPTIONIST'
    email = Column(String(128), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    used_by_user_id = Column(String(64), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    created_by = Column(String(64), nullable=True)

class AuthAuditLogModel(Base):
    __tablename__ = "auth_audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    identifier = Column(String(128), nullable=False) # masked email, public_id or phone
    event = Column(String(64), nullable=False, index=True) # e.g. 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'TOKEN_REFRESH', 'LOGOUT'
    status = Column(String(32), nullable=False) # 'SUCCESS', 'FAILURE', 'WARNING', 'BLOCKED'
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    details = Column(String(512), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
