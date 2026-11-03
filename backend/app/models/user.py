import datetime
from sqlalchemy import Column, String, DateTime
from app.database import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'PATIENT', 'DOCTOR', 'HOSPITAL_ADMIN'
    avatar = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    hospital_id = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
