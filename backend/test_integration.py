import sys
from app.database import SessionLocal, apply_safe_migrations
from app.seed import seed_database
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    OPDCreateRequest,
    OPDRescheduleRequest,
    HospitalVerifyRequest,
    ConsentCreateRequest,
    TreatmentEstimateCreateRequest
)
from app.routers.auth import login, register
from app.models.user import UserModel
from app.routers.opd import (
    create_opd_appointment,
    list_opd_appointments,
    reschedule_opd_appointment,
    cancel_opd_appointment
)
from app.routers.qr import hospital_staff_verify
from app.routers.consent import record_consent, revoke_consent
from app.routers.financial import (
    create_treatment_cost_estimate,
    get_treatment_cost_estimates_for_patient
)
from app.routers.hospitals import get_all_hospitals
from app.routers.doctors import get_doctors
from fastapi import HTTPException

def run_tests():
    print("==================================================")
    print("CHIKITSA-X Backend Direct Router & Database Test")
    print("==================================================")

    apply_safe_migrations()
    db = SessionLocal()

    try:
        # Seed database if needed
        seed_database(db)

        # 1. Hospital Directory
        hospitals = get_all_hospitals(db=db)
        assert len(hospitals) > 0, "No hospitals found"
        hosp = hospitals[0]
        hosp_id = hosp["id"]
        print(f"✅ 1. Hospitals loaded: {len(hospitals)} found. Selected: {hosp['name']} ({hosp_id})")

        # 2. Doctor Directory
        doctors = get_doctors(hospital_id=hosp_id, db=db)
        assert len(doctors) > 0, "No doctors found"
        doc = doctors[0]
        doc_id = doc["id"]
        print(f"✅ 2. Doctors loaded: {len(doctors)} found for hospital. Selected: {doc['name']} ({doc_id})")

        # 3. Patient Login
        login_req = LoginRequest(
            email="patient@chikitsax.demo",
            password="demo123",
            role="PATIENT"
        )
        auth_res = login(login_req, db=db)
        assert auth_res.accessToken, "No access token issued"
        patient_id = auth_res.user.id
        patient_user = db.query(UserModel).filter(UserModel.id == patient_id).first()
        print(f"✅ 3. Patient Login verified! User: {auth_res.user.name}, Role: {auth_res.user.role}")

        # 4. Doctor Login
        doc_login = login(LoginRequest(email="doctor@chikitsax.demo", password="demo123", role="DOCTOR"), db=db)
        assert doc_login.accessToken
        doc_user = db.query(UserModel).filter(UserModel.id == doc_login.user.id).first()
        print(f"✅ 4. Doctor Login verified! User: {doc_login.user.name}, Role: {doc_login.user.role}")

        # 5. Book OPD Appointment
        import time
        unique_slot = f"{int(time.time()) % 12 + 1}:00 PM"
        unique_date = f"2{(int(time.time()) % 8) + 1} Nov 2026"
        booking_payload = OPDCreateRequest(
            patient_id=patient_id,
            hospital_id=hosp_id,
            doctor_id=doc_id,
            department="Cardiology",
            appointment_date=unique_date,
            appointment_time=unique_slot
        )
        app_res = create_opd_appointment(booking_payload, db=db, current_user=patient_user)
        app_id = app_res["id"]
        ref_id = app_res["reference_id"]
        qr_token = app_res["qr_token"]
        assert app_res["status"] == "CONFIRMED"
        print(f"✅ 5. Appointment booked! Ref: {ref_id}, ID: {app_id}, Slot: {unique_date} {unique_slot}, Status: {app_res['status']}")

        # 6. Slot Conflict Guard (Try booking same doctor at same date & time)
        conflict_detected = False
        try:
            create_opd_appointment(booking_payload, db=db, current_user=patient_user)
        except HTTPException as e:
            if e.status_code == 409:
                conflict_detected = True
        assert conflict_detected, "Double booking was not rejected!"
        print("✅ 6. Slot conflict guard verified! Duplicate booking rejected with 409 Conflict.")

        # 7. List appointments for patient
        patient_apps = list_opd_appointments(patient_id=patient_id, db=db)
        assert any(a["id"] == app_id for a in patient_apps)
        print(f"✅ 7. Appointment list query verified! Patient has {len(patient_apps)} appointment(s).")

        # 8. Reschedule Appointment
        t_ms = int(time.time() * 1000)
        resched_slot = f"{(t_ms // 1000) % 12 + 1}:{(t_ms % 50) + 10:02d} AM"
        resched_req = OPDRescheduleRequest(
            appointment_date=f"{(t_ms % 25) + 1} Dec 2027",
            appointment_time=resched_slot
        )
        resched_res = reschedule_opd_appointment(app_id, resched_req, db=db, current_user=patient_user)
        assert resched_res["appointment_date"] == resched_req.appointment_date
        assert resched_res["appointment_time"] == resched_req.appointment_time
        print(f"✅ 8. Appointment rescheduled! New slot: {resched_res['appointment_date']} at {resched_res['appointment_time']}")

        # 9. QR Verification Check-in
        hosp_user = db.query(UserModel).filter(UserModel.role == "HOSPITAL_ADMIN").first()
        verify_req = HospitalVerifyRequest(reference_id=ref_id, staff_name="CarePlus Desk Admin")
        qr_res = hospital_staff_verify(verify_req, db=db, current_user=hosp_user)
        assert qr_res["verified"] is True
        print(f"✅ 9. QR Check-in verified at hospital desk! Status: {qr_res['status']}, Message: {qr_res['message']}")

        # 10. Cancel Appointment
        cancel_res = cancel_opd_appointment(app_id, db=db, current_user=patient_user)
        assert cancel_res["status"] == "CANCELLED"
        print(f"✅ 10. Appointment cancelled! Status: {cancel_res['status']}")

        # 11. Consent Grant & Revocation
        cst_req = ConsentCreateRequest(
            patient_id=patient_id,
            hospital_id=hosp_id,
            hospital_name="CarePlus Hospital",
            doctor_id=doc_id,
            doctor_name="Dr. Rajesh",
            granted=True
        )
        cst = record_consent(cst_req, db=db, current_user=patient_user)
        cst_id = cst["id"]
        assert cst["status"] == "GRANTED"
        print(f"✅ 11. Consent granted! ID: {cst_id}, Status: {cst['status']}")

        revoked = revoke_consent(cst_id, db=db, current_user=patient_user)
        assert revoked["status"] == "REVOKED"
        print(f"✅ 12. Consent revoked! ID: {cst_id}, Status: {revoked['status']}")

        # 12. Treatment Cost Estimate creation by Doctor
        est_req = TreatmentEstimateCreateRequest(
            patient_id=patient_id,
            hospital_id=hosp_id,
            procedure_name="Coronary Angiography",
            room_category="Semi-Private",
            estimated_cost_min=45000.0,
            estimated_cost_max=65000.0
        )
        est = create_treatment_cost_estimate(est_req, db=db, current_user=doc_user)
        assert est["id"]
        print(f"✅ 13. Treatment cost estimate created! Procedure: {est['procedureName']}, ID: {est['id']}")

        patient_estimates = get_treatment_cost_estimates_for_patient(patient_id, db=db, current_user=patient_user)
        assert len(patient_estimates) > 0
        print(f"✅ 14. Retrieved {len(patient_estimates)} treatment cost estimate(s) for patient.")

        print("\n🎉 ALL 14 BACKEND INTEGRATION & LOGIC TESTS PASSED WITHOUT ERROR! 🎉")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
