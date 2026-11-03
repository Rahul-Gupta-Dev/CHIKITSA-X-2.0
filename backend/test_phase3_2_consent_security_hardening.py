import urllib.request
import urllib.error
import json
import time
import sqlite3
import os

BASE_URL = "http://127.0.0.1:8000/api"
DB_PATH = os.path.join(os.path.dirname(__file__), "chikitsax.db")

def api_call(method: str, endpoint: str, data=None, token: str = None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            try:
                parsed = json.loads(content.decode("utf-8"))
            except Exception:
                parsed = content
            return resp.status, parsed
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

def query_db(query: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        return rows
    finally:
        conn.close()

def main():
    print("=========================================================================")
    print("CHIKITSA-X Phase 3.2: Patient Consent Hardening & DB Persistence Tests")
    print("=========================================================================")

    ts = int(time.time())

    # --- Setup Actors ---
    # 1. Register Patient 4
    p4_email = f"patient4_{ts}@chikitsax.test"
    st, reg_res = api_call("POST", "/auth/register", {
        "name": f"Pooja Patil {ts}",
        "fullName": f"Pooja Patil {ts}",
        "email": p4_email,
        "phone": "+91 91234 56789",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200, f"Registration failed: {reg_res}"
    p4_token = reg_res["accessToken"]
    p4_id = reg_res["user"]["id"]

    # 2. Authenticate Patient 1 (Demo)
    st, p1_res = api_call("POST", "/auth/login", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    assert st == 200, f"Patient 1 login failed: {p1_res}"
    p1_token = p1_res["accessToken"]
    p1_id = p1_res["user"]["id"]

    # 3. Authenticate Doctor
    st, d_res = api_call("POST", "/auth/login", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    assert st == 200, f"Doctor login failed: {d_res}"
    d_token = d_res["accessToken"]

    # 4. Authenticate Hospital Staff
    st, h_res = api_call("POST", "/auth/login", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_STAFF"
    })
    assert st == 200, f"Hospital login failed: {h_res}"
    h_token = h_res["accessToken"]

    print("✅ Actors authenticated successfully (Patient 4, Patient 1, Doctor, Hospital Staff)")

    # -------------------------------------------------------------------------
    # TEST 8: Authorized doctor/hospital consent requests create PENDING status only
    # -------------------------------------------------------------------------
    st, req_res = api_call("POST", "/consent", {
        "patientId": p4_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "doctorName": "Dr. Rajesh Kulkarni",
        "granted": False
    }, token=d_token)
    assert st == 200, f"Doctor consent request failed: {req_res}"
    assert req_res["status"] == "PENDING"
    cst_id = req_res["id"]

    # Direct SQLite Inspection:
    rows = query_db("SELECT id, patient_id, status, granted_at FROM consent_logs WHERE id = ?", (cst_id,))
    assert len(rows) == 1, f"Consent record {cst_id} not found in database!"
    assert rows[0][2] == "PENDING", f"DB Status expected PENDING, got {rows[0][2]}"
    assert rows[0][3] is None, f"DB granted_at should be NULL for pending consent, got {rows[0][3]}"
    print(f"✅ TEST 8 PASSED: Authorized doctor consent request creates PENDING record in SQLite (DB Status: {rows[0][2]})")

    # -------------------------------------------------------------------------
    # TEST 2: A doctor sending granted: true cannot grant consent (403 Forbidden)
    # -------------------------------------------------------------------------
    st, doc_grant_res = api_call("POST", "/consent", {
        "patientId": p4_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "doctorName": "Dr. Rajesh Kulkarni",
        "granted": True
    }, token=d_token)
    assert st == 403, f"Expected 403 when doctor tries to grant consent, got {st} ({doc_grant_res})"

    # Verify DB status is NOT granted
    rows = query_db("SELECT status, granted_at FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "PENDING", f"DB status should still be PENDING after doctor grant attempt, got {rows[0][0]}"
    assert rows[0][1] is None, f"DB granted_at must remain NULL, got {rows[0][1]}"
    print("✅ TEST 2 PASSED: Doctor sending granted: true strictly rejected with 403 (DB Status remains PENDING)")

    # -------------------------------------------------------------------------
    # TEST 3: Hospital staff/admin sending granted: true cannot grant consent (403 Forbidden)
    # -------------------------------------------------------------------------
    st, hosp_grant_res = api_call("POST", "/consent", {
        "patientId": p4_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "doctorName": "Dr. Rajesh Kulkarni",
        "granted": True
    }, token=h_token)
    assert st == 403, f"Expected 403 when hospital staff tries to grant consent, got {st} ({hosp_grant_res})"

    # Verify DB status is NOT granted
    rows = query_db("SELECT status FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "PENDING", f"DB status should still be PENDING after hospital grant attempt, got {rows[0][0]}"
    print("✅ TEST 3 PASSED: Hospital staff sending granted: true strictly rejected with 403 (DB Status remains PENDING)")

    # -------------------------------------------------------------------------
    # TEST 4: Unauthorized users cannot grant consent for another patient (403 Forbidden)
    # -------------------------------------------------------------------------
    st, idor_grant_res = api_call("POST", "/consent", {
        "patientId": p4_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "granted": True
    }, token=p1_token)
    assert st == 403, f"Expected 403 when Patient 1 tries to grant Patient 4's consent, got {st} ({idor_grant_res})"

    # Verify DB status is NOT granted
    rows = query_db("SELECT status FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "PENDING", f"DB status must remain PENDING, got {rows[0][0]}"
    print("✅ TEST 4 PASSED: Cross-patient consent grant rejected with 403 (DB Status remains PENDING)")

    # -------------------------------------------------------------------------
    # TEST 5: Doctor or hospital cannot change existing PENDING consent to GRANTED
    # -------------------------------------------------------------------------
    # Re-verify that doctor trying to approve existing pending consent gets 403 and status stays PENDING
    st, doc_flip_res = api_call("POST", "/consent", {
        "patientId": p4_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "granted": True
    }, token=d_token)
    assert st == 403, f"Expected 403 on flip attempt, got {st}"
    rows = query_db("SELECT status FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "PENDING", f"Existing consent flipped to {rows[0][0]}!"
    print("✅ TEST 5 PASSED: Doctor/Hospital cannot flip existing PENDING consent to GRANTED (DB Status remains PENDING)")

    # -------------------------------------------------------------------------
    # TEST 1: A patient can grant consent for their own valid request
    # -------------------------------------------------------------------------
    st, p4_grant_res = api_call("POST", "/consent", {
        "patientId": p4_id,
        "hospitalId": "hosp-1",
        "hospitalName": "CarePlus Super Specialty Hospital",
        "doctorId": "doc-1",
        "doctorName": "Dr. Rajesh Kulkarni",
        "granted": True
    }, token=p4_token)
    assert st == 200, f"Patient 4 consent grant failed: {p4_grant_res}"
    assert p4_grant_res["status"] == "GRANTED"

    # Direct SQLite Inspection:
    rows = query_db("SELECT status, granted_at FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "GRANTED", f"DB status expected GRANTED, got {rows[0][0]}"
    assert rows[0][1] is not None, f"DB granted_at should be populated, got {rows[0][1]}"
    print(f"✅ TEST 1 PASSED: Patient 4 granted consent; SQLite verified (DB Status: {rows[0][0]}, GrantedAt: {rows[0][1]})")

    # -------------------------------------------------------------------------
    # TEST 7: A patient cannot revoke another patient's consent (403 Forbidden)
    # -------------------------------------------------------------------------
    st, p1_revoke_p4 = api_call("PUT", f"/consent/{cst_id}/revoke", token=p1_token)
    assert st == 403, f"Expected 403 when Patient 1 tries to revoke Patient 4's consent, got {st}"

    # Verify DB status is STILL GRANTED
    rows = query_db("SELECT status FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "GRANTED", f"DB status should still be GRANTED, got {rows[0][0]}"
    print("✅ TEST 7 PASSED: Cross-patient revocation blocked with 403 (DB Status remains GRANTED)")

    # Non-patient (Doctor) also cannot revoke
    st, doc_revoke_p4 = api_call("PUT", f"/consent/{cst_id}/revoke", token=d_token)
    assert st == 403, f"Expected 403 when Doctor tries to revoke Patient 4's consent, got {st}"
    rows = query_db("SELECT status FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "GRANTED", f"DB status should still be GRANTED, got {rows[0][0]}"
    print("✅ TEST 7B PASSED: Doctor revocation blocked with 403 (DB Status remains GRANTED)")

    # -------------------------------------------------------------------------
    # Setup Document Upload for Patient 4 to test Document Access & Downloads
    # -------------------------------------------------------------------------
    pdf_bytes = b"%PDF-1.4 Hardened Test Medical Document Content for Patient 4\nRx: Cardiology Consultation Active."
    st, up_res = multipart_upload(
        "/medical-records/upload",
        fields={"patient_id": p4_id, "category": "Prescription"},
        file_field="file",
        filename="patient4_records.pdf",
        file_bytes=pdf_bytes,
        token=p4_token
    )
    assert st == 200, f"Upload failed: {up_res}"
    rec_id = up_res["id"]

    # -------------------------------------------------------------------------
    # TEST 9: Protected document downloads work with valid auth & remain blocked without it
    # -------------------------------------------------------------------------
    # 9A: Anonymous download rejected
    st, anon_dl = api_call("GET", f"/medical-records/file/{rec_id}")
    assert st == 401, f"Expected 401 for unauthenticated file download, got {st}"

    # 9B: Unauthorized patient (Patient 1) download rejected
    st, p1_dl = api_call("GET", f"/medical-records/file/{rec_id}", token=p1_token)
    assert st == 403, f"Expected 403 for unauthorized patient download, got {st}"

    # 9C: Owner (Patient 4) download succeeds
    st, p4_dl = api_call("GET", f"/medical-records/file/{rec_id}", token=p4_token)
    assert st == 200, f"Expected 200 for owner download, got {st}"
    assert p4_dl == pdf_bytes, "Downloaded document bytes do not match uploaded bytes!"

    # 9D: Doctor with active consent download succeeds
    st, doc_dl = api_call("GET", f"/medical-records/file/{rec_id}", token=d_token)
    assert st == 200, f"Expected 200 for doctor with active consent, got {st}"
    assert doc_dl == pdf_bytes, "Doctor downloaded document bytes mismatch!"
    print("✅ TEST 9 PASSED: Document download securely authenticated: 401 for anonymous, 403 for cross-patient, 200 for owner & authorized doctor")

    # -------------------------------------------------------------------------
    # TEST 6: Patient revocation immediately blocks subsequent medical-record listing and downloading
    # -------------------------------------------------------------------------
    st, rev_res = api_call("PUT", f"/consent/{cst_id}/revoke", token=p4_token)
    assert st == 200, f"Patient 4 revocation failed: {rev_res}"
    assert rev_res["status"] == "REVOKED"

    # Direct SQLite Inspection:
    rows = query_db("SELECT status FROM consent_logs WHERE id = ?", (cst_id,))
    assert rows[0][0] == "REVOKED", f"DB status expected REVOKED, got {rows[0][0]}"

    # Doctor access to medical records is immediately blocked (403)
    st, doc_recs_rev = api_call("GET", f"/medical-records/{p4_id}", token=d_token)
    assert st == 403, f"Doctor should be blocked from listing records after revocation, got {st}"

    # Doctor download of file is immediately blocked (403)
    st, doc_dl_rev = api_call("GET", f"/medical-records/file/{rec_id}", token=d_token)
    assert st == 403, f"Doctor should be blocked from downloading file after revocation, got {st}"
    print(f"✅ TEST 6 PASSED: Patient 4 revoked consent (DB Status: {rows[0][0]}); Doctor listing and file downloads immediately blocked with 403")

    print("\n=========================================================================")
    print("ALL 9 PHASE 3.2 CONSENT SECURITY HARDENING REGRESSION TESTS PASSED!")
    print("=========================================================================")

if __name__ == "__main__":
    main()
