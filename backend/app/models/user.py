import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from app.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    public_id = Column(String(32), unique=True, index=True, nullable=True) # e.g. 'CHX-P-XXXXXXXX'
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'PATIENT', 'DOCTOR', 'HOSPITAL_ADMIN', 'HOSPITAL_STAFF', 'SUPER_ADMIN'
    account_status = Column(String(32), nullable=True, default="PENDING_APPROVAL", index=True) # 'PENDING_VERIFICATION', 'PENDING_APPROVAL', 'ACTIVE', 'SUSPENDED', 'REJECTED'
    email_verified = Column(Boolean, nullable=False, default=False)
    phone_verified = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(32), nullable=True) # 'APPROVED', 'PENDING', 'REJECTED'
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(256), nullable=True)
    avatar = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    hospital_id = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
