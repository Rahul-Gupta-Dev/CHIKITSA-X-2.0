import sys
import os
import json
import urllib.request
import urllib.error
import time

BASE_URL = "http://127.0.0.1:8000/api"

def http_req(endpoint, method="GET", data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"detail": content}
        return e.code, err_json
    except Exception as e:
        return 500, {"detail": str(e)}

def http_multipart_upload(endpoint, patient_id, category, filename, file_content, token=None):
    boundary = "----WebKitFormBoundary" + str(int(time.time() * 1000))
    url = f"{BASE_URL}{endpoint}"
    
    parts = []
    # patient_id
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"patient_id\"\r\n\r\n{patient_id}\r\n".encode("utf-8"))
    # category
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"category\"\r\n\r\n{category}\r\n".encode("utf-8"))
    # file
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: application/pdf\r\n\r\n".encode("utf-8"))
    parts.append(file_content)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    
    body = b"".join(parts)
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body))
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"detail": content}
        return e.code, err_json

def test_consent_and_records_group():
    print("\n--- [GROUP 3] Consent Lifecycle, Medical Records & Secure Document Storage ---")

    # 1. Login Patient 1
    _, p1_auth = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    p1_token = p1_auth["accessToken"]
    p1_id = p1_auth["user"]["id"]

    # 2. Login Doctor
    _, doc_auth = http_req("/auth/login", "POST", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    doc_token = doc_auth["accessToken"]
    doc_id = doc_auth["user"]["id"]

    # 3. Doctor Access WITHOUT Consent
    code_no_cst, _ = http_req(f"/medical-records/{p1_id}", "GET", token=doc_token)
    assert code_no_cst == 403, f"FAIL: Expected 403 for doctor without consent, got {code_no_cst}"
    print(f"  [PASS] 3.1 Doctor blocked from accessing medical records without active consent (Returned {code_no_cst} Forbidden).")

    # 4. Patient Grants Consent
    code_grant, grant_res = http_req("/consent", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "hospital_name": "CarePlus Hospital",
        "doctor_id": doc_id,
        "doctor_name": "Dr. Rajesh Kulkarni",
        "granted": True
    }, token=p1_token)
    assert code_grant == 200, f"FAIL: Consent grant returned {code_grant}"
    cst_id = grant_res["id"]
    assert grant_res.get("status") == "GRANTED"
    print(f"  [PASS] 3.2 Patient successfully granted clinical consent (ID: {cst_id}, Status: GRANTED).")

    # 5. Doctor Access WITH Active Consent
    code_with_cst, rec_list = http_req(f"/medical-records/{p1_id}", "GET", token=doc_token)
    assert code_with_cst == 200, f"FAIL: Expected 200 for doctor with active consent, got {code_with_cst}"
    print(f"  [PASS] 3.3 Doctor successfully accessed patient medical records with active consent (Returned {code_with_cst} OK).")

    # 6. Patient Revokes Consent
    code_revoke, revoke_res = http_req(f"/consent/{cst_id}/revoke", "PUT", token=p1_token)
    assert code_revoke == 200, f"FAIL: Consent revocation failed with {code_revoke}"
    assert revoke_res.get("status") == "REVOKED"
    print("  [PASS] 3.4 Patient revoked clinical consent (Status: REVOKED).")

    # 7. Doctor Access Immediately Blocked After Revocation
    code_post_revoke, _ = http_req(f"/medical-records/{p1_id}", "GET", token=doc_token)
    assert code_post_revoke == 403, f"FAIL: Expected 403 for doctor after consent revocation, got {code_post_revoke}"
    print(f"  [PASS] 3.5 Consent revocation immediately and securely blocks doctor access (Returned {code_post_revoke} Forbidden).")

    # 8. Multipart Document Upload and Disk Persistence
    pdf_sample = b"%PDF-1.4\n1 0 obj\n<< /Title (Confidential Echocardiogram) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    code_up, up_res = http_multipart_upload(
        "/medical-records/upload",
        patient_id=p1_id,
        category="Echocardiogram",
        filename="Echo_Cardiac_Report.pdf",
        file_content=pdf_sample,
        token=p1_token
    )
    assert code_up == 200, f"FAIL: Document upload failed with {code_up}: {up_res}"
    record_id = up_res.get("id")
    print(f"  [PASS] 3.6 Multipart medical document uploaded and saved to disk storage (Record ID: {record_id}).")

    # 9. Verify Secure Download
    download_url = f"{BASE_URL}/medical-records/file/{record_id}"
    req_dl = urllib.request.Request(download_url, headers={"Authorization": f"Bearer {p1_token}"})
    with urllib.request.urlopen(req_dl) as dl_resp:
        dl_bytes = dl_resp.read()
        assert dl_bytes == pdf_sample, "FAIL: Downloaded bytes do not match uploaded bytes"
    print("  [PASS] 3.7 Patient successfully downloaded persistent document from private storage with byte-for-byte fidelity.")

    # 9.1 Unauthenticated File Download Rejection
    code_anon_dl, _ = http_req(f"/medical-records/file/{record_id}", "GET")
    assert code_anon_dl == 401, f"SECURITY DEFECT: Anonymous file download allowed! Got {code_anon_dl}"
    print("  [PASS] 3.7.1 Anonymous file download blocked with 401 Unauthorized.")

    # 9.2 Doctor File Download Blocked Without Active Consent
    code_doc_dl, _ = http_req(f"/medical-records/file/{record_id}", "GET", token=doc_token)
    assert code_doc_dl == 403, f"SECURITY DEFECT: Doctor downloaded file without active consent! Got {code_doc_dl}"
    print("  [PASS] 3.7.2 Doctor document download blocked with 403 Forbidden when consent is revoked.")

    # 10. Path Traversal Protection
    code_trav, _ = http_multipart_upload(
        "/medical-records/upload",
        patient_id=p1_id,
        category="Prescription",
        filename="../../../etc/passwd",
        file_content=b"malicious file",
        token=p1_token
    )
    assert code_trav in [400, 422], f"FAIL: Path traversal filename was not rejected, got {code_trav}"
    print(f"  [PASS] 3.8 Path traversal filename injection rejected with {code_trav} Bad Request.")

    return True

if __name__ == "__main__":
    test_consent_and_records_group()
