import urllib.request
import urllib.error
import json
import time
import os

BASE_URL = "http://127.0.0.1:8000/api"

def api_call(method: str, endpoint: str, data=None, token: str = None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read()
            try:
                parsed = json.loads(content.decode("utf-8"))
            except Exception:
                parsed = content
            return status, parsed
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            parsed = json.loads(content.decode("utf-8"))
        except Exception:
            parsed = {"detail": content.decode("utf-8", errors="ignore")}
        return e.code, parsed

def multipart_upload(endpoint: str, fields: dict, file_field: str, filename: str, file_bytes: bytes, token: str = None):
    boundary = f"----FormBoundary{int(time.time()*1000)}"
    body = bytearray()
    for k, v in fields.items():
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\nContent-Type: application/pdf\r\n\r\n".encode("utf-8"))
    body.extend(file_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(f"{BASE_URL}{endpoint}", data=bytes(body), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return resp.status, json.loads(content.decode("utf-8"))
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            parsed = json.loads(content.decode("utf-8"))
        except Exception:
            parsed = {"detail": content.decode("utf-8", errors="ignore")}
        return e.code, parsed

def main():
    print("=================================================================")
    print("CHIKITSA-X Phase 3: Identity, Consent & Records Integration Test")
    print("=================================================================")

    # 1. Register a fresh new patient
    timestamp = int(time.time())
    new_patient_email = f"patient3_{timestamp}@chikitsax.test"
    reg_status, reg_res = api_call("POST", "/auth/register", {
        "name": f"Rohan Deshmukh {timestamp}",
        "fullName": f"Rohan Deshmukh {timestamp}",
        "email": new_patient_email,
        "phone": "+91 99887 76655",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert reg_status == 200, f"Patient registration failed: {reg_res}"
    p3_token = reg_res["accessToken"]
    p3_user_id = reg_res["user"]["id"]
    print(f"✅ 1. Registered New Patient (ID: {p3_user_id}, Email: {new_patient_email})")

    # 2. Get Profile with 'me' alias
    status, p3_profile = api_call("GET", "/patients/me", token=p3_token)
    assert status == 200, f"GET /patients/me failed: {p3_profile}"
    assert p3_profile["email"] == new_patient_email, f"Profile email mismatch: {p3_profile}"
    p3_profile_id = p3_profile["id"]
    print(f"✅ 2. GET /patients/me correctly resolved profile (Profile ID: {p3_profile_id})")

    # 3. Update Profile with emergency contact, blood group, city, pincode
    update_payload = {
        "fullName": f"Rohan Deshmukh {timestamp}",
        "bloodGroup": "B+",
        "phone": "9988776655",
        "city": "Pune",
        "pincode": "411001",
        "emergencyContact": {
            "name": "Sunita Deshmukh",
            "relation": "Spouse",
            "phone": "9988776650"
        }
    }
    status, updated_res = api_call("PUT", "/patients/me", update_payload, token=p3_token)
    assert status == 200, f"PUT /patients/me failed: {updated_res}"
    assert updated_res.get("bloodGroup") == "B+", f"bloodGroup not updated: {updated_res}"
    assert updated_res.get("city") == "Pune", f"city not updated: {updated_res}"
    assert updated_res.get("emergencyContact", {}).get("name") == "Sunita Deshmukh", f"emergencyContact not updated: {updated_res}"
    print("✅ 3. PUT /patients/me persisted profile updates to SQLite")

    # 4. Authenticate Demo Patient 1
    status, p1_res = api_call("POST", "/auth/login", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    assert status == 200, f"Patient 1 login failed: {p1_res}"
    p1_token = p1_res["accessToken"]
    p1_user_id = p1_res["user"]["id"]
    print(f"✅ 4. Authenticated Demo Patient 1 (ID: {p1_user_id})")

    # 5. IDOR Profile Protection: Patient 3 attempts to view/modify Patient 1's profile
    status, idor_view = api_call("GET", f"/patients/{p1_user_id}", token=p3_token)
    assert status == 403, f"Expected 403 for cross-patient profile view, got: {status} ({idor_view})"

    status, idor_update = api_call("PUT", f"/patients/{p1_user_id}", {"phone": "1111111111"}, token=p3_token)
    assert status == 403, f"Expected 403 for cross-patient profile edit, got: {status} ({idor_update})"
    print("✅ 5. IDOR Protection: Patient 3 blocked from accessing/modifying Patient 1's profile (403 Forbidden)")

    # 6. Medical Record Upload by Patient 3 (Testing server-side identity override)
    fake_pdf_content = b"%PDF-1.4 Phase 3 Test Medical Prescription Content \nRx: Metformin 500mg, Atorvastatin 10mg."
    status, upload_res = multipart_upload(
        "/medical-records/upload",
        fields={"patient_id": "usr-patient-1", "category": "Prescription"},
        file_field="file",
        filename="rohan_prescription.pdf",
        file_bytes=fake_pdf_content,
        token=p3_token
    )
    assert status == 200, f"Upload failed: {upload_res}"
    rec_id = upload_res["id"]
    # Verify server derived patient identity from authenticated session, ignoring client-supplied "usr-patient-1"
    assert upload_res["patient_id"] == p3_user_id, f"Identity spoofing allowed! Expected {p3_user_id}, got {upload_res['patient_id']}"
    print(f"✅ 6. Medical record uploaded securely (Record ID: {rec_id}, Patient: {upload_res['patient_id']})")

    # 7. Patient 3 lists records and downloads document
    status, p3_records = api_call("GET", "/medical-records/me", token=p3_token)
    assert status == 200, f"GET /medical-records/me failed: {p3_records}"
    found = any(r["id"] == rec_id for r in p3_records)
    assert found, f"Uploaded record {rec_id} not found in patient's records list"

    # Download file
    status, dl_content = api_call("GET", f"/medical-records/file/{rec_id}", token=p3_token)
    assert status == 200, f"GET /medical-records/file/{rec_id} failed: {status}"
    assert dl_content == fake_pdf_content, "Downloaded file content does not match uploaded content!"
    print("✅ 7. Patient 3 listed and downloaded their own medical record document")

    # 8. IDOR Medical Record Protection: Patient 1 tries to access Patient 3's records and file
    status, p1_cross_recs = api_call("GET", f"/medical-records/{p3_user_id}", token=p1_token)
    assert status == 403, f"Expected 403 for Patient 1 viewing Patient 3's records, got {status}"

    status, p1_cross_file = api_call("GET", f"/medical-records/file/{rec_id}", token=p1_token)
    assert status == 403, f"Expected 403 for Patient 1 downloading Patient 3's file, got {status}"
    print("✅ 8. IDOR Protection: Patient 1 blocked from listing or downloading Patient 3's records (403 Forbidden)")

    # 9. Authenticate Doctor
    status, d_res = api_call("POST", "/auth/login", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    assert status == 200, f"Doctor login failed: {d_res}"
    d_token = d_res["accessToken"]
    d_id = d_res["user"]["id"]
    print(f"✅ 9. Authenticated Doctor (ID: {d_id})")

    # 10. Doctor attempts to access Patient 3's records before consent is granted
    status, doc_recs_pre = api_call("GET", f"/medical-records/{p3_user_id}", token=d_token)
    assert status == 403, f"Expected 403 for doctor without consent, got: {status} ({doc_recs_pre})"

    status, doc_dl_pre = api_call("GET", f"/medical-records/file/{rec_id}", token=d_token)
    assert status == 403, f"Expected 403 for doctor downloading file without consent, got: {status} ({doc_dl_pre})"
    print("✅ 10. Privacy Guard: Doctor blocked from reading/downloading records without consent (403 Forbidden)")

    # 11. Doctor / Hospital sends Consent Request (granted=False)
    status, req_res = api_call("POST", "/consent", {
        "patientId": p3_user_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "doctorName": "Dr. Rajesh Kulkarni",
        "granted": False
    }, token=d_token)
    assert status == 200, f"Consent request failed: {req_res}"
    assert req_res["status"] == "PENDING", f"Expected PENDING status, got {req_res['status']}"
    consent_id = req_res["id"]
    print(f"✅ 11. Consent request dispatched to Patient 3 (Consent ID: {consent_id}, Status: PENDING)")

    # Doctor still cannot access records while status is PENDING
    status, doc_recs_pending = api_call("GET", f"/medical-records/{p3_user_id}", token=d_token)
    assert status == 403, f"Doctor should still be blocked when consent is PENDING, got {status}"

    # 12. Patient 3 inspects pending consents
    status, p3_consents = api_call("GET", "/consent/me", token=p3_token)
    assert status == 200, f"GET /consent/me failed: {p3_consents}"
    c_entry = next((c for c in p3_consents if c["id"] == consent_id), None)
    assert c_entry is not None, f"Consent {consent_id} not found in Patient 3's consent list"
    assert c_entry["status"] == "PENDING"
    print("✅ 12. Patient 3 retrieved active consent request from backend (Status: PENDING)")

    # 13. Patient 3 grants consent
    status, grant_res = api_call("POST", "/consent", {
        "patientId": p3_user_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "doctorName": "Dr. Rajesh Kulkarni",
        "granted": True
    }, token=p3_token)
    assert status == 200, f"Consent grant failed: {grant_res}"
    assert grant_res["status"] == "GRANTED", f"Expected GRANTED status, got {grant_res['status']}"
    print(f"✅ 13. Patient 3 approved digital consent (Status: GRANTED)")

    # 14. Doctor now has clinical access to Patient 3's records and files
    status, doc_recs_post = api_call("GET", f"/medical-records/{p3_user_id}", token=d_token)
    assert status == 200, f"Doctor should have access after consent, got: {status} ({doc_recs_post})"
    assert len(doc_recs_post) >= 1, "Doctor received empty records list"

    status, doc_dl_post = api_call("GET", f"/medical-records/file/{rec_id}", token=d_token)
    assert status == 200, f"Doctor should be able to download file after consent, got: {status}"
    assert doc_dl_post == fake_pdf_content, "Doctor downloaded content mismatch"
    print("✅ 14. Doctor successfully accessed and downloaded records with active consent")

    # 15. Cross-Patient Revocation Attempt: Patient 1 tries to revoke Patient 3's consent
    status, idor_revoke = api_call("PUT", f"/consent/{consent_id}/revoke", token=p1_token)
    assert status == 403, f"Expected 403 for unauthorized consent revocation, got: {status} ({idor_revoke})"
    print("✅ 15. IDOR Protection: Patient 1 blocked from revoking Patient 3's consent (403 Forbidden)")

    # 16. Patient 3 revokes consent
    status, revoke_res = api_call("PUT", f"/consent/{consent_id}/revoke", token=p3_token)
    assert status == 200, f"Revocation failed: {revoke_res}"
    assert revoke_res["status"] == "REVOKED", f"Expected REVOKED, got {revoke_res['status']}"
    print(f"✅ 16. Patient 3 revoked consent (Status: REVOKED)")

    # 17. Doctor is immediately locked out upon revocation
    status, doc_recs_revoked = api_call("GET", f"/medical-records/{p3_user_id}", token=d_token)
    assert status == 403, f"Doctor must be blocked after revocation, got: {status}"

    status, doc_dl_revoked = api_call("GET", f"/medical-records/file/{rec_id}", token=d_token)
    assert status == 403, f"Doctor file download must be blocked after revocation, got: {status}"
    print("✅ 17. Access Gate: Doctor immediately blocked from viewing or downloading records after revocation (403 Forbidden)")

    print("\n=================================================================")
    print("ALL 17 PHASE 3 IDENTITY, CONSENT & RECORD VERIFICATIONS PASSED!")
    print("=================================================================")

if __name__ == "__main__":
    main()
