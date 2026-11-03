import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.auth import get_current_user
from app.models.user import UserModel
from app.models.audit import AuditLogModel
from app.schemas import AuditLogCreate, AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logging"])

@router.get("", response_model=List[AuditLogOut])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role not in ["HOSPITAL_ADMIN", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Audit logs can only be viewed by hospital administrators."
        )

    logs = db.query(AuditLogModel).order_by(AuditLogModel.created_at.desc()).limit(50).all()
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp,
            "actorRole": l.actor_role,
            "actorId": l.actor_id,
            "action": l.action,
            "details": l.details
        }
        for l in logs
    ]

@router.post("", response_model=AuditLogOut)
def create_audit_log(
    payload: AuditLogCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Enforce authenticated actor to prevent spoofing
    now_str = datetime.datetime.utcnow().strftime("%I:%M:%S %p")
    log_id = f"log-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    log = AuditLogModel(
        id=log_id,
        timestamp=now_str,
        actor_role=current_user.role,
        actor_id=current_user.id,
        action=payload.action,
        details=payload.details
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "id": log.id,
        "timestamp": log.timestamp,
        "actorRole": log.actor_role,
        "actorId": log.actor_id,
        "action": log.action,
        "details": log.details
    }
