import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db, SLOT_MUTATION_LOCK
from app.auth import get_current_user, get_current_user_optional
from app.models.user import UserModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.schemas import (
    DoctorOut,
    DoctorScheduleUpdate,
    BlockSlotRequest,
    DoctorScheduleResponse,
    DoctorAvailabilityResponse
)

router = APIRouter(prefix="/api/doctors", tags=["Doctors & Scheduling"])

DEFAULT_WEEKLY_SCHEDULE = [
    {"day": "Monday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
    {"day": "Tuesday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
    {"day": "Wednesday", "time": "02:00 PM - 06:00 PM", "slots": 10, "isBlocked": False},
    {"day": "Thursday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
    {"day": "Friday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
    {"day": "Saturday", "time": "10:00 AM - 02:00 PM", "slots": 8, "isBlocked": True}
]

VALID_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def parse_weekday(date_str: str) -> Optional[str]:
    """Extract standard weekday name from multiple date string formats."""
    if not date_str:
        return None
    s = date_str.strip()
    for d in VALID_WEEKDAYS:
        if d.lower() in s.lower():
            return d
    try:
        return datetime.date.fromisoformat(s).strftime("%A")
    except Exception:
        pass
    for fmt in ["%d %b %Y", "%d %B %Y", "%Y/%m/%d", "%Y-%m-%d"]:
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%A")
        except Exception:
            pass
    if "today" in s.lower():
        return datetime.datetime.now().strftime("%A")
    if "tomorrow" in s.lower():
        return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%A")
    return None

def is_time_in_range(time_str: str, range_str: str) -> bool:
    """Check if a 12-hour formatted time falls inside an 'HH:MM AM - HH:MM PM' range."""
    try:
        t = datetime.datetime.strptime(time_str.strip(), "%I:%M %p").time()
        parts = [p.strip() for p in range_str.split("-")]
        if len(parts) == 2:
            t1 = datetime.datetime.strptime(parts[0], "%I:%M %p").time()
            t2 = datetime.datetime.strptime(parts[1], "%I:%M %p").time()
            return t1 <= t <= t2
    except Exception:
        pass
    return False

def validate_time_range(time_str: str):
    """Validate format and ensure start time strictly precedes end time."""
    parts = [p.strip() for p in time_str.split("-")]
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time range format: '{time_str}'. Expected 'HH:MM AM/PM - HH:MM AM/PM'."
        )
    try:
        t1 = datetime.datetime.strptime(parts[0], "%I:%M %p").time()
        t2 = datetime.datetime.strptime(parts[1], "%I:%M %p").time()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time format in '{time_str}'. Must be standard 12-hour AM/PM format (e.g. '09:00 AM - 01:00 PM')."
        )
    if t1 >= t2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid time range '{time_str}': start time ({parts[0]}) must precede end time ({parts[1]})."
        )

def is_slot_blocked_by_doctor(doctor: DoctorModel, app_date: str, app_time: str) -> bool:
    """Determine whether a specific date and time slot is currently blocked by the doctor."""
    if not doctor:
        return False

    norm_date = app_date.strip()
    norm_time = app_time.strip()
    slot_key = f"{norm_date}#{norm_time}"

    # 1. Check specific blocked slots
    blocked_slots = doctor.blocked_slots or []
    for b in blocked_slots:
        if isinstance(b, dict):
            b_slot = b.get("slot")
            b_date = b.get("date")
            b_time = b.get("time")
            if b_slot == slot_key or (b_date == norm_date and b_time == norm_time):
                return True
            # Also check if blocked by weekday + time
            b_day = b.get("day")
            app_day = parse_weekday(norm_date)
            if b_day and app_day and b_day.lower() == app_day.lower():
                if b_time == norm_time or (b.get("range") and is_time_in_range(norm_time, b.get("range"))):
                    return True
        elif isinstance(b, str):
            if b == slot_key or b == f"{doctor.id}#{slot_key}":
                return True

    # 2. Check weekly recurring schedule
    app_day = parse_weekday(norm_date)
    weekly = doctor.weekly_schedule or DEFAULT_WEEKLY_SCHEDULE
    if app_day and weekly:
        for item in weekly:
            item_day = item.get("day", "")
            if item_day.lower() == app_day.lower():
                is_blocked = bool(item.get("isBlocked", item.get("is_blocked", False)))
                if is_blocked:
                    # If whole day blocked or time falls within operating hours
                    op_time = item.get("time")
                    if not op_time or is_time_in_range(norm_time, op_time):
                        return True

    return False

def resolve_doctor_for_user(current_user: UserModel, db: Session) -> Optional[DoctorModel]:
    if not current_user:
        return None
    # 1. By ID match
    doc = db.query(DoctorModel).filter(DoctorModel.id == current_user.id).first()
    if doc:
        return doc
    # 2. By Name match
    doc = db.query(DoctorModel).filter(DoctorModel.name == current_user.name).first()
    if doc:
        return doc
    # 3. If doctor user has hospital_id
    if current_user.role == "DOCTOR":
        doc = db.query(DoctorModel).filter(
            DoctorModel.name == current_user.name,
            DoctorModel.hospital_id == current_user.hospital_id
        ).first()
        if doc:
            return doc
    return None

def get_or_create_doctor_for_user(current_user: UserModel, db: Session) -> DoctorModel:
    doc = resolve_doctor_for_user(current_user, db)
    if not doc:
        doc = DoctorModel(
            id=current_user.id,
            hospital_id=current_user.hospital_id or "hosp-1",
            hospital_name="CarePlus Super Specialty Hospital",
            name=current_user.name,
            specialty="General Medicine",
            qualification="MBBS, MD",
            experience_years=5,
            rating=4.8,
            consultation_fee=500,
            available_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            available_slots=["09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "02:00 PM", "02:30 PM", "03:00 PM", "04:00 PM", "05:00 PM"],
            weekly_schedule=DEFAULT_WEEKLY_SCHEDULE,
            blocked_slots=[]
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
    return doc

def doctor_to_dict(d: DoctorModel) -> Dict[str, Any]:
    return {
        "id": d.id,
        "hospitalId": d.hospital_id,
        "hospitalName": d.hospital_name,
        "name": d.name,
        "specialty": d.specialty,
        "qualification": d.qualification,
        "experienceYears": d.experience_years,
        "rating": d.rating,
        "consultationFee": d.consultation_fee,
        "availableDays": d.available_days or [],
        "availableSlots": d.available_slots or [],
        "weeklySchedule": d.weekly_schedule or DEFAULT_WEEKLY_SCHEDULE,
        "blockedSlots": d.blocked_slots or [],
        "avatar": d.avatar
    }

def format_schedule_response(doc: DoctorModel) -> Dict[str, Any]:
    weekly = doc.weekly_schedule if doc.weekly_schedule else DEFAULT_WEEKLY_SCHEDULE
    blocked = doc.blocked_slots if doc.blocked_slots else []
    return {
        "doctor_id": doc.id,
        "doctorId": doc.id,
        "doctor_name": doc.name,
        "doctorName": doc.name,
        "hospital_id": doc.hospital_id,
        "hospitalId": doc.hospital_id,
        "hospital_name": doc.hospital_name,
        "hospitalName": doc.hospital_name,
        "weekly_schedule": weekly,
        "weeklySchedule": weekly,
        "blocked_slots": blocked,
        "blockedSlots": blocked,
        "available_days": doc.available_days or [],
        "availableDays": doc.available_days or [],
        "available_slots": doc.available_slots or [],
        "availableSlots": doc.available_slots or []
    }

def validate_and_sanitize_weekly_schedule(weekly_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(weekly_items, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="weekly_schedule must be a list.")

    seen_days = set()
    sanitized = []
    for item in weekly_items:
        if not isinstance(item, dict):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Schedule items must be objects.")

        day = item.get("day", "").strip()
        matched_day = None
        for vd in VALID_WEEKDAYS:
            if vd.lower() == day.lower():
                matched_day = vd
                break

        if not matched_day:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid weekday: '{day}'. Must be one of Monday through Sunday."
            )

        if matched_day in seen_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate schedule entry for weekday '{matched_day}'."
            )
        seen_days.add(matched_day)

        time_val = item.get("time", "").strip()
        if not time_val:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Time range is required for {matched_day}.")

        validate_time_range(time_val)

        slots = item.get("slots", 12)
        try:
            slots_int = int(slots)
            if slots_int <= 0:
                raise ValueError()
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Slot quota for {matched_day} must be a positive integer.")

        is_blocked = bool(item.get("isBlocked", item.get("is_blocked", False)))

        sanitized.append({
            "day": matched_day,
            "time": time_val,
            "slots": slots_int,
            "isBlocked": is_blocked
        })

    return sanitized

# -----------------------------------------------------------------------------
# Doctor Schedule & Slot Endpoints
# -----------------------------------------------------------------------------

@router.get("/me/schedule", response_model=DoctorScheduleResponse)
def get_my_schedule(
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve the authenticated doctor's full schedule and blocked slots."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view doctor schedule."
        )

    if current_user.role != "DOCTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only doctors can access their personal clinical schedule."
        )

    doc = get_or_create_doctor_for_user(current_user, db)
    return format_schedule_response(doc)

@router.put("/me/schedule", response_model=DoctorScheduleResponse)
def update_my_schedule(
    payload: DoctorScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Update the authenticated doctor's schedule and blocked slots."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to update doctor schedule."
        )

    if current_user.role != "DOCTOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only doctors may update clinical schedules."
        )

    doc = get_or_create_doctor_for_user(current_user, db)
    return apply_doctor_schedule_update(doc, payload, db)

@router.post("/me/block-slot", response_model=DoctorScheduleResponse)
def block_my_slot(
    payload: BlockSlotRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Block a specific appointment slot for the authenticated doctor."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    if current_user.role != "DOCTOR":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Doctor role required.")

    doc = get_or_create_doctor_for_user(current_user, db)
    return apply_block_slot(doc, payload, True, db)

@router.post("/me/unblock-slot", response_model=DoctorScheduleResponse)
def unblock_my_slot(
    payload: BlockSlotRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Unblock a specific appointment slot for the authenticated doctor."""
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    if current_user.role != "DOCTOR":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Doctor role required.")

    doc = get_or_create_doctor_for_user(current_user, db)
    return apply_block_slot(doc, payload, False, db)

@router.get("/{doctor_id}/schedule", response_model=DoctorScheduleResponse)
def get_doctor_schedule(
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Retrieve doctor schedule with RBAC: Doctor owns schedule, Hospital Admin views scoped, Patient reads public."""
    doc = db.query(DoctorModel).filter(
        (DoctorModel.id == doctor_id) | (DoctorModel.name == doctor_id)
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor '{doctor_id}' not found.")

    if current_user:
        if current_user.role == "DOCTOR":
            matching_docs = db.query(DoctorModel).filter(
                (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
            ).all()
            allowed_ids = {current_user.id}.union({md.id for md in matching_docs})
            if doc.id not in allowed_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You cannot access another doctor's clinical schedule."
                )
        elif current_user.role in ("HOSPITAL_ADMIN", "HOSPITAL_STAFF"):
            if current_user.hospital_id and doc.hospital_id != current_user.hospital_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Hospital administrators can only view schedules for doctors within their hospital scope."
                )

    return format_schedule_response(doc)

@router.put("/{doctor_id}/schedule", response_model=DoctorScheduleResponse)
def update_doctor_schedule(
    doctor_id: str,
    payload: DoctorScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Update doctor schedule by doctor_id. Only the doctor owning the schedule may update it."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to modify doctor schedule."
        )

    if current_user.role == "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Patients cannot modify doctor schedules."
        )

    if current_user.role in ("HOSPITAL_ADMIN", "HOSPITAL_STAFF"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Hospital administrators cannot modify doctor schedules; only the rostered physician may modify their timetable."
        )

    doc = db.query(DoctorModel).filter(
        (DoctorModel.id == doctor_id) | (DoctorModel.name == doctor_id)
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor '{doctor_id}' not found.")

    matching_docs = db.query(DoctorModel).filter(
        (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
    ).all()
    allowed_ids = {current_user.id}.union({md.id for md in matching_docs})

    if doc.id not in allowed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You cannot modify another doctor's schedule."
        )

    return apply_doctor_schedule_update(doc, payload, db)

@router.post("/{doctor_id}/block-slot", response_model=DoctorScheduleResponse)
def block_doctor_slot(
    doctor_id: str,
    payload: BlockSlotRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    if current_user.role == "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Patients cannot block slots.")

    doc = db.query(DoctorModel).filter((DoctorModel.id == doctor_id) | (DoctorModel.name == doctor_id)).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor '{doctor_id}' not found.")

    matching_docs = db.query(DoctorModel).filter((DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)).all()
    allowed_ids = {current_user.id}.union({md.id for md in matching_docs})
    if doc.id not in allowed_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot block another doctor's slots.")

    return apply_block_slot(doc, payload, True, db)

@router.post("/{doctor_id}/unblock-slot", response_model=DoctorScheduleResponse)
def unblock_doctor_slot(
    doctor_id: str,
    payload: BlockSlotRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    if current_user.role == "PATIENT":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Patients cannot unblock slots.")

    doc = db.query(DoctorModel).filter((DoctorModel.id == doctor_id) | (DoctorModel.name == doctor_id)).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor '{doctor_id}' not found.")

    matching_docs = db.query(DoctorModel).filter((DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)).all()
    allowed_ids = {current_user.id}.union({md.id for md in matching_docs})
    if doc.id not in allowed_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: You cannot unblock another doctor's slots.")

    return apply_block_slot(doc, payload, False, db)

@router.get("/{doctor_id}/availability", response_model=DoctorAvailabilityResponse)
def get_doctor_availability(
    doctor_id: str,
    date: str,
    db: Session = Depends(get_db)
):
    """Public patient-facing availability calculation indicating active vs blocked vs booked slots."""
    doc = db.query(DoctorModel).filter(
        (DoctorModel.id == doctor_id) | (DoctorModel.name == doctor_id)
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Doctor '{doctor_id}' not found.")

    clean_date = date.strip()
    weekday = parse_weekday(clean_date)

    # Check weekly schedule to see if the entire day is blocked
    is_day_blocked = False
    weekly = doc.weekly_schedule or DEFAULT_WEEKLY_SCHEDULE
    if weekday:
        for item in weekly:
            if item.get("day", "").lower() == weekday.lower():
                is_day_blocked = bool(item.get("isBlocked", item.get("is_blocked", False)))

    # Fetch active booked appointments on this date
    booked_appointments = db.query(OPDAppointmentModel).filter(
        (OPDAppointmentModel.doctor_id == doc.id) | (OPDAppointmentModel.doctor_name == doc.name),
        OPDAppointmentModel.appointment_date == clean_date,
        OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"])
    ).all()
    booked_times = {a.appointment_time.strip().upper() for a in booked_appointments}

    slots_to_check = doc.available_slots or [
        "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
        "02:00 PM", "02:30 PM", "03:00 PM", "04:00 PM", "05:00 PM"
    ]

    availability_slots = []
    for slot_time in slots_to_check:
        slot_clean = slot_time.strip()
        is_blocked = is_day_blocked or is_slot_blocked_by_doctor(doc, clean_date, slot_clean)
        is_booked = slot_clean.upper() in booked_times
        is_available = (not is_blocked) and (not is_booked)

        availability_slots.append({
            "time": slot_clean,
            "is_available": is_available,
            "isAvailable": is_available,
            "is_blocked": is_blocked,
            "isBlocked": is_blocked,
            "is_booked": is_booked,
            "isBooked": is_booked
        })

    return {
        "doctor_id": doc.id,
        "doctorId": doc.id,
        "date": clean_date,
        "day": weekday,
        "is_day_blocked": is_day_blocked,
        "isDayBlocked": is_day_blocked,
        "slots": availability_slots
    }

# -----------------------------------------------------------------------------
# Internal Execution Helpers
# -----------------------------------------------------------------------------

def apply_doctor_schedule_update(
    doc: DoctorModel,
    payload: DoctorScheduleUpdate,
    db: Session
) -> Dict[str, Any]:
    with SLOT_MUTATION_LOCK:
        db.expire_all()
        doc = db.query(DoctorModel).filter(DoctorModel.id == doc.id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
        weekly_input = payload.weekly_schedule if payload.weekly_schedule is not None else payload.weeklySchedule
        blocked_input = payload.blocked_slots if payload.blocked_slots is not None else payload.blockedSlots
        days_input = payload.available_days if payload.available_days is not None else payload.availableDays
        slots_input = payload.available_slots if payload.available_slots is not None else payload.availableSlots

        if weekly_input is not None:
            sanitized_weekly = validate_and_sanitize_weekly_schedule(weekly_input)

            # Check if doctor is attempting to block a day with active confirmed appointments
            for item in sanitized_weekly:
                if item["isBlocked"]:
                    conflicts = db.query(OPDAppointmentModel).filter(
                        (OPDAppointmentModel.doctor_id == doc.id) | (OPDAppointmentModel.doctor_name == doc.name),
                        OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"])
                    ).all()
                    day_conflicts = [
                        c for c in conflicts
                        if parse_weekday(c.appointment_date) and parse_weekday(c.appointment_date).lower() == item["day"].lower()
                    ]
                    if day_conflicts:
                        first = day_conflicts[0]
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Cannot block {item['day']} schedule: Doctor {doc.name} has an active confirmed appointment (Ref: {first.reference_id}) with patient {first.patient_name} on {first.appointment_date} at {first.appointment_time}. Please reschedule or cancel existing appointments first."
                        )

            doc.weekly_schedule = sanitized_weekly

        if blocked_input is not None:
            if not isinstance(blocked_input, list):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="blocked_slots must be a list.")

            sanitized_blocked = []
            for b in blocked_input:
                if isinstance(b, dict):
                    b_date = (b.get("date") or "").strip()
                    b_time = (b.get("time") or "").strip()
                    b_slot = (b.get("slot") or "").strip()
                    if not b_slot and b_date and b_time:
                        b_slot = f"{b_date}#{b_time}"

                    if b_date and b_time:
                        conflict = db.query(OPDAppointmentModel).filter(
                            (OPDAppointmentModel.doctor_id == doc.id) | (OPDAppointmentModel.doctor_name == doc.name),
                            OPDAppointmentModel.appointment_date == b_date,
                            OPDAppointmentModel.appointment_time == b_time,
                            OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"])
                        ).first()
                        if conflict:
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail=f"Cannot block slot: Doctor {doc.name} has an active confirmed appointment (Ref: {conflict.reference_id}) with patient {conflict.patient_name} on {b_date} at {b_time}. Please reschedule or cancel the appointment before blocking."
                            )

                    sanitized_blocked.append({
                        "slot": b_slot,
                        "date": b_date,
                        "time": b_time,
                        "day": b.get("day") or parse_weekday(b_date),
                        "reason": b.get("reason", "Doctor unavailable / Clinical duties"),
                        "blockedAt": datetime.datetime.utcnow().isoformat()
                    })
                elif isinstance(b, str) and b.strip():
                    clean_b = b.strip()
                    parts = clean_b.split("#")
                    if len(parts) >= 2:
                        d_part, t_part = parts[-2], parts[-1]
                        conflict = db.query(OPDAppointmentModel).filter(
                            (OPDAppointmentModel.doctor_id == doc.id) | (OPDAppointmentModel.doctor_name == doc.name),
                            OPDAppointmentModel.appointment_date == d_part,
                            OPDAppointmentModel.appointment_time == t_part,
                            OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"])
                        ).first()
                        if conflict:
                            raise HTTPException(
                                status_code=status.HTTP_409_CONFLICT,
                                detail=f"Cannot block slot: Doctor {doc.name} has an active confirmed appointment (Ref: {conflict.reference_id}) on {d_part} at {t_part}."
                            )
                    sanitized_blocked.append(clean_b)

            doc.blocked_slots = sanitized_blocked

        if days_input is not None:
            doc.available_days = days_input

        if slots_input is not None:
            doc.available_slots = slots_input

        db.commit()
        db.refresh(doc)
        return format_schedule_response(doc)

def apply_block_slot(
    doc: DoctorModel,
    payload: BlockSlotRequest,
    is_blocking: bool,
    db: Session
) -> Dict[str, Any]:
    with SLOT_MUTATION_LOCK:
        db.expire_all()
        doc = db.query(DoctorModel).filter(DoctorModel.id == doc.id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

        slot_date = (payload.date or "").strip()
        slot_time = (payload.time or "").strip()
        slot_day = (payload.day or "").strip()
        target_slot = (payload.slot or "").strip()

        if not target_slot and slot_date and slot_time:
            target_slot = f"{slot_date}#{slot_time}"

        if not target_slot and not slot_day and not slot_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'date' and 'time', or 'day', or 'slot' must be provided."
            )

        # 1. Day-level schedule toggle
        if slot_day and not slot_time:
            matched_day = None
            for vd in VALID_WEEKDAYS:
                if vd.lower() == slot_day.lower():
                    matched_day = vd
                    break
            if not matched_day:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid weekday: '{slot_day}'.")

            if is_blocking:
                conflicts = db.query(OPDAppointmentModel).filter(
                    (OPDAppointmentModel.doctor_id == doc.id) | (OPDAppointmentModel.doctor_name == doc.name),
                    OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"])
                ).all()
                day_conflicts = [
                    c for c in conflicts
                    if parse_weekday(c.appointment_date) and parse_weekday(c.appointment_date).lower() == matched_day.lower()
                ]
                if day_conflicts:
                    first = day_conflicts[0]
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Cannot block {matched_day} OPD schedule: Doctor {doc.name} has an active confirmed appointment (Ref: {first.reference_id}) with patient {first.patient_name} on {first.appointment_date} at {first.appointment_time}. Please reschedule or cancel the appointment before blocking."
                    )

            weekly = list(doc.weekly_schedule or DEFAULT_WEEKLY_SCHEDULE)
            updated_weekly = []
            found = False
            for item in weekly:
                if item.get("day", "").lower() == matched_day.lower():
                    updated_weekly.append({**item, "isBlocked": is_blocking})
                    found = True
                else:
                    updated_weekly.append(item)
            if not found:
                updated_weekly.append({"day": matched_day, "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": is_blocking})
            doc.weekly_schedule = updated_weekly

        # 2. Date/Time specific slot toggle
        if target_slot or (slot_date and slot_time):
            current_blocked = list(doc.blocked_slots or [])
            if is_blocking:
                # Check for conflict with existing confirmed appointment
                conflict = db.query(OPDAppointmentModel).filter(
                    (OPDAppointmentModel.doctor_id == doc.id) | (OPDAppointmentModel.doctor_name == doc.name),
                    OPDAppointmentModel.appointment_date == slot_date,
                    OPDAppointmentModel.appointment_time == slot_time,
                    OPDAppointmentModel.status.in_(["CONFIRMED", "VERIFIED"])
                ).first()
                if conflict:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Cannot block slot: Doctor {doc.name} has an active confirmed appointment (Ref: {conflict.reference_id}) with patient {conflict.patient_name} on {slot_date} at {slot_time}. Please reschedule or cancel the appointment before blocking."
                    )

                # Avoid duplicate block entries
                exists = False
                for b in current_blocked:
                    if isinstance(b, dict):
                        if b.get("slot") == target_slot or (b.get("date") == slot_date and b.get("time") == slot_time):
                            exists = True
                            break
                    elif isinstance(b, str) and b == target_slot:
                        exists = True
                        break

                if not exists:
                    current_blocked.append({
                        "slot": target_slot,
                        "date": slot_date,
                        "time": slot_time,
                        "day": slot_day or parse_weekday(slot_date),
                        "reason": payload.reason or "Doctor unavailable / Clinical duties",
                        "blockedAt": datetime.datetime.utcnow().isoformat()
                    })
            else:
                # Unblocking: remove from blocked_slots
                new_blocked = []
                for b in current_blocked:
                    if isinstance(b, dict):
                        if b.get("slot") == target_slot or (b.get("date") == slot_date and b.get("time") == slot_time):
                            continue
                        new_blocked.append(b)
                    elif isinstance(b, str):
                        if b == target_slot:
                            continue
                        new_blocked.append(b)
                current_blocked = new_blocked

            doc.blocked_slots = current_blocked

        db.commit()
        db.refresh(doc)
        return format_schedule_response(doc)

# -----------------------------------------------------------------------------
# Base Doctor Listing & Query Endpoints
# -----------------------------------------------------------------------------

@router.get("", response_model=List[DoctorOut])
def get_doctors(hospital_id: str = None, db: Session = Depends(get_db)):
    query = db.query(DoctorModel)
    if hospital_id:
        query = query.filter(DoctorModel.hospital_id == hospital_id)
    doctors = query.all()
    return [doctor_to_dict(d) for d in doctors]

@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doc = db.query(DoctorModel).filter(DoctorModel.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return doctor_to_dict(doc)

@router.get("/{doctor_id}/appointments")
def get_doctor_appointments(
    doctor_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    target_doc = db.query(DoctorModel).filter(
        (DoctorModel.id == doctor_id) | (DoctorModel.id == doctor_id.strip())
    ).first()
    if not target_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    is_authorized = False

    # 1. Doctor themselves
    if current_user.role == "DOCTOR":
        valid_doctor_ids = {current_user.id}
        matching_docs = db.query(DoctorModel).filter(
            (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
        ).all()
        for md in matching_docs:
            valid_doctor_ids.add(md.id)
        if doctor_id in valid_doctor_ids or (current_user.name and target_doc.name and current_user.name.strip().lower() == target_doc.name.strip().lower()):
            is_authorized = True

    # 2. Hospital staff/admin for this doctor's hospital
    elif current_user.role in ["HOSPITAL_ADMIN", "HOSPITAL_STAFF"]:
        if not current_user.hospital_id or current_user.hospital_id == target_doc.hospital_id:
            is_authorized = True

    elif current_user.role == "ADMIN":
        is_authorized = True

    if not is_authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You are not authorized to view this doctor's appointments."
        )

    appointments = db.query(OPDAppointmentModel).filter(
        OPDAppointmentModel.doctor_id == doctor_id
    ).order_by(OPDAppointmentModel.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "referenceId": a.reference_id,
            "patientId": a.patient_id,
            "patientName": a.patient_name,
            "patientPhone": a.patient_phone,
            "department": a.department,
            "appointmentDate": a.appointment_date,
            "appointmentTime": a.appointment_time,
            "status": a.status
        }
        for a in appointments
    ]
