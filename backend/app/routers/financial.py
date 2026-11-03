import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.auth import get_current_user_optional
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.models.consultation import ConsultationModel
from app.models.consent import ConsentLogModel
from app.models.financial import (
    InsurancePolicyModel,
    GovernmentSchemeModel,
    NGOSupportModel,
    CareToCostAssessmentModel,
    TreatmentCostEstimateModel
)
from app.schemas import (
    FinancialAssessmentRequest,
    FinancialAssessmentResponse,
    FinancePlanRequest,
    FinancePlanResponse,
    TreatmentEstimateCreateRequest
)
from app.services.finance_service import FinanceService

router = APIRouter(prefix="/api/financial", tags=["Care-to-Cost Financial Assistance"])

def get_patient_valid_ids(patient_id: str, db: Session) -> set:
    valid_ids = {patient_id}
    pat = db.query(PatientModel).filter(
        (PatientModel.id == patient_id) | (PatientModel.user_id == patient_id)
    ).first()
    if pat:
        valid_ids.add(pat.id)
        if pat.user_id:
            valid_ids.add(pat.user_id)
    user_pat = db.query(UserModel).filter(UserModel.id == patient_id).first()
    if user_pat:
        valid_ids.add(user_pat.id)
    return valid_ids

def check_doctor_authorization_for_patient(current_user: UserModel, valid_patient_ids: set, db: Session) -> bool:
    valid_doctor_ids = {current_user.id}
    matching_docs = db.query(DoctorModel).filter(
        (DoctorModel.id == current_user.id) | (DoctorModel.name == current_user.name)
    ).all()
    for md in matching_docs:
        valid_doctor_ids.add(md.id)

    # 1. Appointment
    has_opd = db.query(OPDAppointmentModel).filter(
        OPDAppointmentModel.patient_id.in_(list(valid_patient_ids)),
        (OPDAppointmentModel.doctor_id.in_(list(valid_doctor_ids)) | (OPDAppointmentModel.doctor_name == current_user.name))
    ).first()
    if has_opd:
        return True

    # 2. Consultation
    has_cons = db.query(ConsultationModel).filter(
        ConsultationModel.patient_id.in_(list(valid_patient_ids)),
        (ConsultationModel.doctor_id.in_(list(valid_doctor_ids)) | (ConsultationModel.doctor_name == current_user.name))
    ).first()
    if has_cons:
        return True

    # 3. Active Consent
    has_cst = db.query(ConsentLogModel).filter(
        ConsentLogModel.patient_id.in_(list(valid_patient_ids)),
        (ConsentLogModel.doctor_id.in_(list(valid_doctor_ids)) | (ConsentLogModel.doctor_name == current_user.name)),
        ConsentLogModel.status == "GRANTED"
    ).first()
    if has_cst:
        return True

    return False

@router.get("/insurance/{patient_id}")
def get_patient_insurance(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view insurance policies."
        )

    resolved_pid = current_user.id if patient_id == "me" else patient_id
    valid_pids = get_patient_valid_ids(resolved_pid, db)

    # Enforce RBAC
    if current_user.role == "PATIENT":
        if current_user.id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access insurance records of another patient."
            )
    elif current_user.role == "DOCTOR":
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized to access this patient's insurance details without an active appointment, consultation, or patient consent."
            )

    policies = db.query(InsurancePolicyModel).filter(
        InsurancePolicyModel.patient_id.in_(list(valid_pids))
    ).all()

    return [
        {
            "id": p.id,
            "patientId": p.patient_id,
            "providerName": p.provider_name,
            "policyNumber": p.policy_number,
            "sumInsured": p.sum_insured,
            "availableBalance": p.available_balance,
            "coPayPercentage": p.co_pay_percentage,
            "isCashlessAvailable": p.is_cashless_available,
            "status": p.status
        }
        for p in policies
    ]

@router.get("/schemes/{patient_id}")
def get_gov_schemes(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view government schemes."
        )

    schemes = db.query(GovernmentSchemeModel).all()
    return [
        {
            "id": s.id,
            "schemeCode": s.scheme_code,
            "schemeName": s.scheme_name,
            "description": s.description,
            "maxBenefitAmount": s.max_benefit_amount,
            "eligibilityCriteria": s.eligibility_criteria,
            "requiredDocuments": s.required_documents,
            "contactHelpline": s.contact_helpline
        }
        for s in schemes
    ]

@router.get("/ngo-support/{patient_id}")
def get_ngo_support(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view NGO support listings."
        )

    ngos = db.query(NGOSupportModel).all()
    return [
        {
            "id": n.id,
            "organizationName": n.organization_name,
            "supportType": n.support_type,
            "maxAssistanceAmount": n.max_assistance_amount,
            "eligibilityDescription": n.eligibility_description,
            "requiredDocuments": n.required_documents,
            "applicationStatus": n.application_status
        }
        for n in ngos
    ]

@router.post("/assess", response_model=FinancialAssessmentResponse)
def assess_care_to_cost(
    payload: FinancialAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to run financial assessment."
        )

    raw_pid = payload.patient_id or payload.patientId or current_user.id
    resolved_pid = current_user.id if raw_pid == "me" else raw_pid
    valid_pids = get_patient_valid_ids(resolved_pid, db)

    if current_user.role == "PATIENT":
        if current_user.id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access or modify financial assessments for another patient."
            )
    elif current_user.role == "DOCTOR":
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized to assess finances for this patient."
            )

    # Validate treatment cost
    raw_cost = payload.treatment_cost if payload.treatment_cost is not None else payload.treatmentCost
    if raw_cost is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="treatment_cost is required.")

    try:
        treatment_cost = float(raw_cost)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="treatment_cost must be a valid number.")

    if treatment_cost < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Treatment cost cannot be negative.")

    # Validate optional amounts
    ins_cov = payload.insurance_coverage if payload.insurance_coverage is not None else payload.insuranceCoverage
    gov_sup = payload.government_support if payload.government_support is not None else payload.governmentSupport
    ngo_aid = payload.ngo_assistance if payload.ngo_assistance is not None else payload.ngoAssistance
    self_pay = payload.patient_self_contribution if payload.patient_self_contribution is not None else payload.patientSelfContribution

    for name, val in [("insurance_coverage", ins_cov), ("government_support", gov_sup), ("ngo_assistance", ngo_aid), ("patient_self_contribution", self_pay)]:
        if val is not None and float(val) < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{name} cannot be negative.")

    patient = db.query(PatientModel).filter(
        (PatientModel.id == resolved_pid) | (PatientModel.user_id == resolved_pid)
    ).first()

    # If explicit amounts are passed from patient form, use actual submitted inputs
    if any(v is not None for v in [ins_cov, gov_sup, ngo_aid, self_pay]):
        insurance_support = float(ins_cov or 0.0)
        government_support = float(gov_sup or 0.0)
        ngo_support = float(ngo_aid or 0.0)
        patient_self = float(self_pay or 0.0)
        total_aid = insurance_support + government_support + ngo_support + patient_self
        financial_gap = max(0.0, treatment_cost - total_aid)
        is_funding_complete = (financial_gap == 0.0)
    else:
        # Rule-based calculation from patient profile
        has_insurance = payload.has_insurance if payload.has_insurance is not None else (patient.has_insurance if patient else True)
        has_gov = payload.has_government_card if payload.has_government_card is not None else (patient.has_government_card if patient else True)
        ration_type = payload.ration_card_type or (patient.ration_card_type if patient else "BPL")

        assessment = FinanceService.calculate_assessment(
            treatment_cost=treatment_cost,
            has_insurance=has_insurance,
            insurance_balance=420000.0,
            has_gov_card=has_gov,
            ration_card_type=ration_type
        )
        insurance_support = assessment["insurance_support"]
        government_support = assessment["government_support"]
        ngo_support = assessment["ngo_support"]
        financial_gap = assessment["estimated_patient_gap"]
        patient_self = financial_gap
        is_funding_complete = assessment["is_funding_complete"]

    # Persist assessment record
    ass_id = f"ass-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    db_assessment = CareToCostAssessmentModel(
        id=ass_id,
        patient_id=patient.user_id if (patient and patient.user_id) else (patient.id if patient else resolved_pid),
        hospital_name=payload.hospital_name or payload.hospitalName or "CarePlus Hospital",
        estimated_treatment_cost=treatment_cost,
        insurance_coverage=insurance_support,
        government_support=government_support,
        ngo_assistance=ngo_support,
        patient_self_contribution=patient_self,
        financial_gap=financial_gap,
        is_funding_complete=is_funding_complete
    )
    db.add(db_assessment)

    if patient and (patient.care_stage is None or patient.care_stage < 11):
        patient.care_stage = 11

    db.commit()
    db.refresh(db_assessment)

    return {
        "id": db_assessment.id,
        "patient_id": db_assessment.patient_id,
        "patientId": db_assessment.patient_id,
        "hospital_name": db_assessment.hospital_name,
        "hospitalName": db_assessment.hospital_name,
        "estimated_treatment_cost": db_assessment.estimated_treatment_cost,
        "estimatedTreatmentCost": db_assessment.estimated_treatment_cost,
        "insurance_support": db_assessment.insurance_coverage,
        "insuranceCoverage": db_assessment.insurance_coverage,
        "government_support": db_assessment.government_support,
        "governmentSupport": db_assessment.government_support,
        "ngo_support": db_assessment.ngo_assistance,
        "ngoAssistance": db_assessment.ngo_assistance,
        "patient_self_contribution": db_assessment.patient_self_contribution,
        "patientSelfContribution": db_assessment.patient_self_contribution,
        "estimated_patient_gap": db_assessment.financial_gap,
        "financialGap": db_assessment.financial_gap,
        "is_funding_complete": db_assessment.is_funding_complete,
        "isFundingComplete": db_assessment.is_funding_complete,
        "calculated_at": db_assessment.calculated_at.isoformat() if db_assessment.calculated_at else None,
        "calculatedAt": db_assessment.calculated_at.isoformat() if db_assessment.calculated_at else None,
        "disclaimer": "Indicative financial assistance estimate. Final claim approval subject to insurer, government scheme nodal office, and hospital billing verification."
    }

@router.get("/assessments/patient/{patient_id}")
def get_patient_assessments(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view financial assessments."
        )

    resolved_pid = current_user.id if patient_id == "me" else patient_id
    valid_pids = get_patient_valid_ids(resolved_pid, db)

    if current_user.role == "PATIENT":
        if current_user.id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access financial assessments of another patient."
            )
    elif current_user.role == "DOCTOR":
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized to view financial assessments for this patient."
            )

    assessments = db.query(CareToCostAssessmentModel).filter(
        CareToCostAssessmentModel.patient_id.in_(list(valid_pids))
    ).order_by(CareToCostAssessmentModel.calculated_at.desc()).all()

    return [
        {
            "id": a.id,
            "patientId": a.patient_id,
            "hospitalName": a.hospital_name,
            "estimatedTreatmentCost": a.estimated_treatment_cost,
            "insuranceCoverage": a.insurance_coverage,
            "governmentSupport": a.government_support,
            "ngoAssistance": a.ngo_assistance,
            "patientSelfContribution": a.patient_self_contribution,
            "financialGap": a.financial_gap,
            "isFundingComplete": a.is_funding_complete,
            "calculatedAt": a.calculated_at.isoformat() if a.calculated_at else None
        }
        for a in assessments
    ]

@router.post("/finance-plan", response_model=FinancePlanResponse)
def generate_finance_plan(
    payload: FinancePlanRequest,
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to generate financial plan."
        )

    raw_cost = payload.treatment_cost if payload.treatment_cost is not None else payload.treatmentCost
    if raw_cost is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="treatment_cost is required.")

    try:
        cost = float(raw_cost)
        ins = float(payload.insurance_coverage if payload.insurance_coverage is not None else (payload.insuranceCoverage or 0.0))
        gov = float(payload.government_support if payload.government_support is not None else (payload.governmentSupport or 0.0))
        ngo = float(payload.ngo_support if payload.ngo_support is not None else (payload.ngoSupport or 0.0))
        sav = float(payload.additional_savings if payload.additional_savings is not None else (payload.additionalSavings or 0.0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amounts must be valid numeric values.")

    if cost < 0 or ins < 0 or gov < 0 or ngo < 0 or sav < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amounts cannot be negative.")

    out_of_pocket = max(0.0, cost - (ins + gov + ngo))
    rem_gap = max(0.0, out_of_pocket - sav)

    if rem_gap <= 0.0:
        tag = "RECOMMENDED: 100% COVERED (ZERO OUT-OF-POCKET GAP)"
    elif rem_gap <= 15000.0:
        tag = "FEASIBLE: LOW GAP COVERED BY NGO & SAVINGS"
    else:
        tag = "FINANCING REQUIRED: HIGH GAP — APPLY FOR CSR GRANT"

    return {
        "estimated_cost": cost,
        "estimatedCost": cost,
        "insurance_benefit": ins,
        "insuranceBenefit": ins,
        "government_benefit": gov,
        "governmentBenefit": gov,
        "ngo_benefit": ngo,
        "ngoBenefit": ngo,
        "patient_out_of_pocket": out_of_pocket,
        "patientOutOfPocket": out_of_pocket,
        "remaining_gap": rem_gap,
        "remainingGap": rem_gap,
        "recommendation_tag": tag,
        "recommendationTag": tag,
        "disclaimer": "Indicative affordability plan only. Final figures subject to hospital and provider billing verification."
    }

@router.post("/treatment-estimates")
def create_treatment_cost_estimate(
    payload: TreatmentEstimateCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    """Allow authorized doctors or hospital staff to generate and record indicative treatment cost estimates."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to create treatment cost estimates."
        )

    if current_user.role == "PATIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Patients cannot create treatment cost estimates."
        )

    patient_id = payload.patient_id or payload.patientId
    if not patient_id or not patient_id.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required.")

    valid_pids = get_patient_valid_ids(patient_id.strip(), db)
    patient = db.query(PatientModel).filter(
        (PatientModel.id.in_(list(valid_pids))) | (PatientModel.user_id.in_(list(valid_pids)))
    ).first()
    user_pat = db.query(UserModel).filter(UserModel.id.in_(list(valid_pids))).first()

    if not patient and not user_pat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient record not found.")

    # Doctor authorization check
    if current_user.role == "DOCTOR":
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized to create treatment estimates for this patient without an active appointment, consultation, or patient consent."
            )

    # Optional consultation ID validation
    cons_id = payload.consultation_id or payload.consultationId
    if cons_id:
        cons = db.query(ConsultationModel).filter(ConsultationModel.id == cons_id).first()
        if not cons:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced consultation record not found.")
        if cons.patient_id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conflicting consultation: consultation patient does not match estimate patient."
            )

    procedure_name = payload.procedure_name or payload.procedureName
    if not procedure_name or not str(procedure_name).strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="procedure_name is required.")

    min_cost = payload.estimated_cost_min if payload.estimated_cost_min is not None else payload.estimatedCostMin
    max_cost = payload.estimated_cost_max if payload.estimated_cost_max is not None else payload.estimatedCostMax

    if min_cost is None or max_cost is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="estimated_cost_min and estimated_cost_max are required.")

    try:
        min_cost = float(min_cost)
        max_cost = float(max_cost)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cost amounts must be valid numbers.")

    if min_cost < 0 or max_cost < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cost amounts cannot be negative.")

    if max_cost < min_cost:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="estimated_cost_max cannot be less than estimated_cost_min.")

    breakdown = payload.breakdown
    if breakdown and isinstance(breakdown, dict):
        for k, v in breakdown.items():
            if isinstance(v, (int, float)) and v < 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Breakdown item '{k}' cannot be negative.")
    else:
        breakdown = {
            "bedCharges": min_cost * 0.25,
            "surgeonFee": min_cost * 0.35,
            "medications": min_cost * 0.20,
            "diagnostics": min_cost * 0.20
        }

    est_id = f"est-{int(datetime.datetime.utcnow().timestamp()*1000)}"
    estimate = TreatmentCostEstimateModel(
        id=est_id,
        consultation_id=cons_id,
        patient_id=patient.user_id if (patient and patient.user_id) else (patient.id if patient else patient_id.strip()),
        hospital_id=payload.hospital_id or payload.hospitalId or (current_user.hospital_id or "hosp-1"),
        hospital_name=payload.hospital_name or payload.hospitalName or "CarePlus Hospital",
        procedure_name=procedure_name.strip(),
        room_category=payload.room_category or payload.roomCategory or "General Ward",
        estimated_cost_range={
            "min": min_cost,
            "max": max_cost
        },
        breakdown=breakdown,
        confidence_level="INDICATIVE"
    )
    db.add(estimate)
    # Monotonically advance patient care stage to Stage 9 (Treatment Cost Estimate)
    if patient and (patient.care_stage is None or patient.care_stage < 9):
        patient.care_stage = 9
    db.commit()
    db.refresh(estimate)
    return {
        "id": estimate.id,
        "patientId": estimate.patient_id,
        "hospitalId": estimate.hospital_id,
        "hospitalName": estimate.hospital_name,
        "procedureName": estimate.procedure_name,
        "roomCategory": estimate.room_category,
        "estimatedCostRange": estimate.estimated_cost_range,
        "breakdown": estimate.breakdown,
        "confidenceLevel": estimate.confidence_level,
        "createdAt": estimate.created_at.isoformat() if estimate.created_at else None
    }

@router.get("/treatment-estimates/patient/{patient_id}")
def get_treatment_cost_estimates_for_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view treatment cost estimates."
        )

    resolved_pid = current_user.id if patient_id == "me" else patient_id
    valid_pids = get_patient_valid_ids(resolved_pid, db)

    if current_user.role == "PATIENT":
        if current_user.id not in valid_pids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot access financial estimates of another patient."
            )
    elif current_user.role == "DOCTOR":
        if not check_doctor_authorization_for_patient(current_user, valid_pids, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Doctor is not authorized to view financial records for this patient without an active appointment, consultation, or patient consent."
            )

    estimates = db.query(TreatmentCostEstimateModel).filter(
        TreatmentCostEstimateModel.patient_id.in_(list(valid_pids))
    ).order_by(TreatmentCostEstimateModel.created_at.desc()).all()

    return [
        {
            "id": e.id,
            "patientId": e.patient_id,
            "hospitalId": e.hospital_id,
            "hospitalName": e.hospital_name,
            "procedureName": e.procedure_name,
            "roomCategory": e.room_category,
            "estimatedCostRange": e.estimated_cost_range,
            "breakdown": e.breakdown,
            "confidenceLevel": e.confidence_level,
            "createdAt": e.created_at.isoformat() if e.created_at else None
        }
        for e in estimates
    ]
