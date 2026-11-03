import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.auth import get_current_user_optional
from app.models.user import UserModel
from app.models.hospital import HospitalModel, HospitalReviewModel
from app.schemas import (
    HospitalOut,
    HospitalRecommendRequest,
    HospitalRecommendationResponse,
    HospitalReviewCreateRequest,
    HospitalReviewOut
)
from app.services.hospital_service import HospitalRecommendationService

router = APIRouter(prefix="/api/hospitals", tags=["Hospitals"])

def hospital_to_dict(h: HospitalModel) -> Dict[str, Any]:
    return {
        "id": h.id,
        "name": h.name,
        "code": h.code,
        "tagline": h.tagline,
        "address": h.address,
        "city": h.city,
        "distanceKm": h.distance_km,
        "phone": h.phone,
        "emergencyPhone": h.emergency_phone,
        "rating": h.rating,
        "reviewCount": h.review_count,
        "emergencyAvailable": h.emergency_available,
        "emergencyBedsFree": h.emergency_beds_free,
        "icuBedsFree": h.icu_beds_free,
        "specialties": h.specialties or [],
        "clinicalFitScore": h.clinical_fit_score,
        "affordabilityScore": h.affordability_score,
        "availabilityScore": h.availability_score,
        "supportServicesScore": h.support_services_score,
        "chikitsaxCareScore": h.chikitsax_care_score,
        "estimatedCostRange": h.estimated_cost_range,
        "acceptedInsuranceProviders": h.accepted_insurance_providers or [],
        "acceptedGovSchemes": h.accepted_gov_schemes or [],
        "ngoPartnerships": h.ngo_partnerships or [],
        "accreditation": h.accreditation or [],
        "opdSlotAvailability": h.opd_slot_availability,
        "image": h.image,
        "whyRecommended": h.why_recommended
    }

@router.get("", response_model=List[HospitalOut])
def get_all_hospitals(db: Session = Depends(get_db)):
    hospitals = db.query(HospitalModel).all()
    return [hospital_to_dict(h) for h in hospitals]

@router.get("/{hospital_id}", response_model=HospitalOut)
def get_hospital(hospital_id: str, db: Session = Depends(get_db)):
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital_to_dict(h)

@router.post("/recommend", response_model=HospitalRecommendationResponse)
def recommend_hospitals(payload: HospitalRecommendRequest, db: Session = Depends(get_db)):
    hospitals = db.query(HospitalModel).all()
    h_dicts = [hospital_to_dict(h) for h in hospitals]
    ranked = HospitalRecommendationService.rank_hospitals(h_dicts, payload.budget_preference or "MEDIUM")
    return {"hospitals": ranked}

@router.get("/{hospital_id}/reviews", response_model=List[HospitalReviewOut])
def get_hospital_reviews(hospital_id: str, db: Session = Depends(get_db)):
    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    reviews = db.query(HospitalReviewModel).filter(HospitalReviewModel.hospital_id == hospital_id).order_by(HospitalReviewModel.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "hospitalId": r.hospital_id,
            "patientId": r.patient_id,
            "patientName": r.patient_name,
            "rating": r.rating,
            "reviewText": r.review_text,
            "createdAt": r.created_at.strftime("%d %b %Y, %I:%M %p") if r.created_at else ""
        }
        for r in reviews
    ]

@router.post("/{hospital_id}/reviews", response_model=HospitalReviewOut)
def create_hospital_review(
    hospital_id: str,
    payload: HospitalReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to submit a hospital review."
        )

    if current_user.role != "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only patients can review hospitals."
        )

    h = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not h:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    clean_text = payload.review_text.strip()
    if not clean_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review text cannot be empty.")

    # Check for existing review by this patient for this hospital
    existing = db.query(HospitalReviewModel).filter(
        HospitalReviewModel.hospital_id == hospital_id,
        HospitalReviewModel.patient_id == current_user.id
    ).first()

    if existing:
        existing.rating = round(float(payload.rating), 1)
        existing.review_text = clean_text
        rev = existing
    else:
        rev = HospitalReviewModel(
            id=f"rev-{uuid.uuid4().hex[:8]}",
            hospital_id=hospital_id,
            patient_id=current_user.id,
            patient_name=current_user.name,
            rating=round(float(payload.rating), 1),
            review_text=clean_text
        )
        db.add(rev)

    db.commit()

    # Recalculate hospital average rating and review count
    all_revs = db.query(HospitalReviewModel).filter(HospitalReviewModel.hospital_id == hospital_id).all()
    if all_revs:
        h.review_count = len(all_revs)
        h.rating = round(sum(r.rating for r in all_revs) / len(all_revs), 1)
        db.commit()

    db.refresh(rev)

    return {
        "id": rev.id,
        "hospitalId": rev.hospital_id,
        "patientId": rev.patient_id,
        "patientName": rev.patient_name,
        "rating": rev.rating,
        "reviewText": rev.review_text,
        "createdAt": rev.created_at.strftime("%d %b %Y, %I:%M %p") if rev.created_at else ""
    }
