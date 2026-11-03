import datetime
from sqlalchemy.orm import Session
from app.models.user import UserModel
from app.models.patient import PatientModel
from app.models.hospital import HospitalModel
from app.models.doctor import DoctorModel
from app.models.opd import OPDAppointmentModel
from app.models.qr import QRReferenceModel
from app.models.financial import (
    InsurancePolicyModel,
    GovernmentSchemeModel,
    NGOSupportModel
)
from app.models.audit import AuditLogModel
from app.auth import hash_password

def seed_database(db: Session):
    demo_pw = hash_password("demo123")
    # Check if database is already seeded
    existing_users = db.query(UserModel).all()
    if existing_users:
        for u in existing_users:
            if not u.password_hash:
                u.password_hash = demo_pw
        db.commit()
        return

    print("Seeding CHIKITSAX database with stable demo dataset...")

    # 1. Seed Users
    users = [
        UserModel(
            id="usr-patient-1",
            email="patient@chikitsax.demo",
            name="Ramesh Sharma",
            role="PATIENT",
            password_hash=demo_pw,
            phone="+91 98765 43210",
            avatar="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80"
        ),
        UserModel(
            id="usr-doctor-1",
            email="doctor@chikitsax.demo",
            name="Dr. Rajesh Kulkarni",
            role="DOCTOR",
            password_hash=demo_pw,
            phone="+91 98220 11223",
            hospital_id="hosp-1",
            avatar="https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=200&q=80"
        ),
        UserModel(
            id="usr-hospital-1",
            email="hospital@chikitsax.demo",
            name="CarePlus Hospital Admin",
            role="HOSPITAL_ADMIN",
            password_hash=demo_pw,
            phone="+91 020 6789 0000",
            hospital_id="hosp-1",
            avatar="https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=200&q=80"
        )
    ]
    db.add_all(users)
    db.flush()

    # 2. Seed Patient Profile
    patient = PatientModel(
        id="pat-sharma-1",
        user_id="usr-patient-1",
        full_name="Ramesh Sharma",
        age=48,
        gender="Male",
        blood_group="B+",
        phone="+91 98765 43210",
        email="patient@chikitsax.demo",
        address="Flat 402, Green Acres, Shivajinagar",
        city="Pune",
        pincode="411005",
        emergency_contact={"name": "Sunita Sharma", "relationship": "Spouse", "phone": "+91 98765 43211"},
        symptoms=["Chest Tightness", "Mild Shortness of Breath", "Fatigue on Walking"],
        medical_history=["Type 2 Diabetes Mellitus (5 yrs)", "Mild Hypertension"],
        medications=["Metformin 500mg BD", "Telmisartan 40mg OD"],
        allergies=["Penicillin"],
        vital_signs={"bp": "138/88 mmHg", "pulse": "84 bpm", "spo2": "97%", "temp": "98.4 °F"},
        care_stage=6,
        financial_budget_preference="MEDIUM",
        has_insurance=True,
        insurance_provider="Star Health Care Policy",
        policy_number="SH-2024-998124",
        has_government_card=True,
        ration_card_type="BPL",
        income_category="< ₹2.5 Lakh / annum"
    )
    db.add(patient)
    db.flush()

    # 3. Seed Hospitals
    hospitals = [
        HospitalModel(
            id="hosp-1",
            name="CarePlus Super Specialty Hospital",
            code="CPH-PUNE",
            tagline="Excellence in Cardiology & Tertiary Emergency Care",
            address="Plot 14, Senapati Bapat Road, Shivajinagar",
            city="Pune",
            distance_km=3.2,
            phone="+91 020 6789 0000",
            emergency_phone="+91 020 6789 9999",
            rating=4.8,
            review_count=1240,
            emergency_available=True,
            emergency_beds_free=6,
            icu_beds_free=4,
            specialties=["Cardiology", "General Medicine", "Neurology", "Orthopedics", "Emergency Trauma"],
            clinical_fit_score=96.0,
            affordability_score=88.0,
            availability_score=92.0,
            support_services_score=95.0,
            chikitsax_care_score=93.0,
            estimated_cost_range={"min": 70000, "max": 110000},
            accepted_insurance_providers=["Star Health", "HDFC ERGO", "Niva Bupa", "Care Insurance"],
            accepted_gov_schemes=["Ayushman Bharat (PM-JAY)", "MJPJAY Maharashtra"],
            ngo_partnerships=["Tata Trusts Healthcare Fund", "Being Human Foundation"],
            accreditation=["NABH Accredited", "JCI Certified"],
            opd_slot_availability="HIGH",
            image="https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?auto=format&fit=crop&w=600&q=80",
            why_recommended={
                "specialtyMatch": "Top-ranked Cardiology & Cardiac Emergency department within 4 km",
                "costFeasibility": "Full PM-JAY & Star Health cashless coverage bringing out-of-pocket close to ₹0",
                "proximityReason": "Only 3.2 km (approx 10 mins drive)",
                "availabilityReason": "Immediate OPD slots available today with 6 free Emergency Trauma beds"
            }
        ),
        HospitalModel(
            id="hosp-2",
            name="Apollo Health City & Emergency Care",
            code="APO-PUNE",
            tagline="Advanced Cardiac & Multi-Organ Specialty Center",
            address="Viman Nagar Main Road, Near Airport Road",
            city="Pune",
            distance_km=7.8,
            phone="+91 020 4911 2000",
            emergency_phone="+91 020 4911 9111",
            rating=4.9,
            review_count=2150,
            emergency_available=True,
            emergency_beds_free=8,
            icu_beds_free=5,
            specialties=["Cardiology", "Cardiac Surgery", "Pulmonology", "Oncology"],
            clinical_fit_score=98.0,
            affordability_score=72.0,
            availability_score=85.0,
            support_services_score=90.0,
            chikitsax_care_score=89.0,
            estimated_cost_range={"min": 95000, "max": 150000},
            accepted_insurance_providers=["Star Health", "HDFC ERGO", "Niva Bupa"],
            accepted_gov_schemes=["Ayushman Bharat (PM-JAY)"],
            ngo_partnerships=["Apollo CSR Health Initiative"],
            accreditation=["JCI Accredited", "NABH Gold"],
            opd_slot_availability="MEDIUM",
            image="https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=600&q=80"
        ),
        HospitalModel(
            id="hosp-3",
            name="AIIMS Regional Referral & Emergency Center",
            code="AIIMS-REG",
            tagline="Premier Public Tertiary Care & Research Institute",
            address="University Circle Campus, Ganeshkhind Road",
            city="Pune",
            distance_km=2.1,
            phone="+91 020 2567 1111",
            emergency_phone="+91 020 2567 9999",
            rating=4.6,
            review_count=3400,
            emergency_available=True,
            emergency_beds_free=12,
            icu_beds_free=2,
            specialties=["General Medicine", "Cardiology", "Emergency Trauma"],
            clinical_fit_score=94.0,
            affordability_score=98.0,
            availability_score=78.0,
            support_services_score=85.0,
            chikitsax_care_score=91.0,
            estimated_cost_range={"min": 12000, "max": 35000},
            accepted_insurance_providers=["All National Insurance Policies"],
            accepted_gov_schemes=["Ayushman Bharat (PM-JAY)", "MJPJAY"],
            ngo_partnerships=["Prime Minister Relief Fund", "Tata Trusts"],
            accreditation=["Government Super Specialty Center"],
            opd_slot_availability="HIGH",
            image="https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=600&q=80"
        )
    ]
    db.add_all(hospitals)
    db.flush()

    # 4. Seed Doctors
    doctors = [
        DoctorModel(
            id="doc-1",
            hospital_id="hosp-1",
            hospital_name="CarePlus Super Specialty Hospital",
            name="Dr. Rajesh Kulkarni",
            specialty="Senior Interventional Cardiologist",
            qualification="MBBS, MD (Med), DM (Cardiology), FACC",
            experience_years=18,
            rating=4.9,
            consultation_fee=800,
            available_days=["Today", "Tomorrow", "Thursday", "Friday"],
            available_slots=["10:00 AM", "11:30 AM", "02:00 PM", "04:30 PM"],
            weekly_schedule=[
                {"day": "Monday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Tuesday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Wednesday", "time": "02:00 PM - 06:00 PM", "slots": 10, "isBlocked": False},
                {"day": "Thursday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Friday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Saturday", "time": "10:00 AM - 02:00 PM", "slots": 8, "isBlocked": True}
            ],
            blocked_slots=[],
            avatar="https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=200&q=80"
        ),
        DoctorModel(
            id="doc-2",
            hospital_id="hosp-1",
            hospital_name="CarePlus Super Specialty Hospital",
            name="Dr. Ananya Roy",
            specialty="Consultant Physician & Diabetologist",
            qualification="MBBS, MD (Internal Medicine)",
            experience_years=12,
            rating=4.8,
            consultation_fee=600,
            available_days=["Today", "Tomorrow", "Wednesday"],
            available_slots=["09:30 AM", "11:00 AM", "03:00 PM"],
            weekly_schedule=[
                {"day": "Monday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Tuesday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Wednesday", "time": "02:00 PM - 06:00 PM", "slots": 10, "isBlocked": False},
                {"day": "Thursday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Friday", "time": "09:00 AM - 01:00 PM", "slots": 12, "isBlocked": False},
                {"day": "Saturday", "time": "10:00 AM - 02:00 PM", "slots": 8, "isBlocked": True}
            ],
            blocked_slots=[],
            avatar="https://images.unsplash.com/photo-1594824813566-88855ce78905?auto=format&fit=crop&w=200&q=80"
        )
    ]
    db.add_all(doctors)
    db.flush()

    # 5. Seed OPD Appointment & QR Reference
    opd = OPDAppointmentModel(
        id="opd-seed-1",
        reference_id="CHX-2026-8A92F",
        patient_id="usr-patient-1",
        patient_name="Ramesh Sharma",
        patient_phone="+91 98765 43210",
        hospital_id="hosp-1",
        hospital_name="CarePlus Super Specialty Hospital",
        department="Cardiology",
        doctor_id="doc-1",
        doctor_name="Dr. Rajesh Kulkarni",
        appointment_date="Today (09 Sep 2026)",
        appointment_time="11:30 AM",
        consultation_fee=800,
        status="CONFIRMED",
        qr_token="TOKEN_SECURE_CHX-2026-8A92F_1725900000000"
    )
    db.add(opd)
    db.flush()

    qr = QRReferenceModel(
        id="qr-opd-seed-1",
        reference_id="CHX-2026-8A92F",
        token="TOKEN_SECURE_CHX-2026-8A92F_1725900000000",
        patient_id="usr-patient-1",
        hospital_id="hosp-1",
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1),
        is_verified=False
    )
    db.add(qr)
    db.flush()

    # 6. Seed Insurance Policy
    policy = InsurancePolicyModel(
        id="pol-star-1",
        patient_id="pat-sharma-1",
        provider_name="Star Health Comprehensive Policy",
        policy_number="SH-2024-998124",
        sum_insured=500000.0,
        available_balance=420000.0,
        co_pay_percentage=10.0,
        is_cashless_available=True,
        status="ACTIVE"
    )
    db.add(policy)

    # 7. Seed Gov Schemes
    schemes = [
        GovernmentSchemeModel(
            id="sch-pmjay",
            scheme_code="PM-JAY",
            scheme_name="Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
            description="National public health insurance scheme providing free coverage up to ₹5 Lakh per family per year.",
            max_benefit_amount=500000.0,
            eligibility_criteria={"rationCardTypes": ["AAY", "BPL"], "maxAnnualIncome": 250000},
            required_documents=["Ayushman Card", "Aadhaar Card", "BPL Ration Card"],
            contact_helpline="14555"
        ),
        GovernmentSchemeModel(
            id="sch-mjpjay",
            scheme_code="MJPJAY",
            scheme_name="Mahatma Jyotirao Phule Jan Arogya Yojana (Maharashtra)",
            description="State government scheme providing cashless medical quality care up to ₹3 Lakh.",
            max_benefit_amount=300000.0,
            eligibility_criteria={"rationCardTypes": ["Yellow", "Orange", "BPL"], "maxAnnualIncome": 300000},
            required_documents=["Yellow/Orange Ration Card", "Aadhaar Card"],
            contact_helpline="155388"
        )
    ]
    db.add_all(schemes)

    # 8. Seed NGO Support
    ngos = [
        NGOSupportModel(
            id="ngo-tata",
            organization_name="Tata Trusts Healthcare Assistance Fund",
            support_type="Direct Medical Bill Grant",
            max_assistance_amount=30000.0,
            eligibility_description="Provides financial gap funding for cardiac patients with income below ₹3 Lakh.",
            required_documents=["Hospital Cost Estimate", "Income Certificate"],
            application_status="AVAILABLE"
        ),
        NGOSupportModel(
            id="ngo-beinghuman",
            organization_name="Being Human Healthcare Relief Initiative",
            support_type="Specialty Surgery Aid",
            max_assistance_amount=25000.0,
            eligibility_description="Special fund for urgent cardiac procedures.",
            required_documents=["Doctor Recommendation Letter"],
            application_status="AVAILABLE"
        )
    ]
    db.add_all(ngos)

    # 9. Seed Initial Audit Log
    log = AuditLogModel(
        id="log-init-1",
        timestamp=datetime.datetime.utcnow().strftime("%I:%M:%S %p"),
        actor_role="PATIENT",
        actor_id="usr-patient-1",
        action="SYSTEM_INIT",
        details="SQLite database seeded with stable CHIKITSAX dataset."
    )
    db.add(log)

    db.commit()
    print("Database seeding completed successfully.")
