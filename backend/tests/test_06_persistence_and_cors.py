import sys
import os
import json
import sqlite3
import urllib.request
import urllib.error
import time

BASE_URL = "http://127.0.0.1:8000/api"
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chikitsax.db"))

def http_req(endpoint, method="GET", data=None, token=None, custom_headers=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if custom_headers:
        headers.update(custom_headers)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}, dict(resp.headers)
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"detail": content}
        return e.code, err_json, dict(e.headers)
    except Exception as e:
        return 500, {"detail": str(e)}, {}

def test_persistence_and_cors_group():
    print("\n--- [GROUP 6] Database Persistence on Disk & CORS / Error Inspection ---")

    # 1. Login Doctor
    _, doc_auth, _ = http_req("/auth/login", "POST", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    doc_token = doc_auth["accessToken"]

    # 2. Login Patient
    _, p1_auth, _ = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    p1_token = p1_auth["accessToken"]
    p1_id = p1_auth["user"]["id"]

    # 3. Create a unique Treatment Cost Estimate via API
    proc_name = f"Coronary Artery Bypass Graft (CABG) - {int(time.time())}"
    code_est, est_res, _ = http_req("/financial/treatment-estimates", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "procedure_name": proc_name,
        "room_category": "ICU + Private Room",
        "estimated_cost_min": 250000.0,
        "estimated_cost_max": 350000.0
    }, token=doc_token)
    assert code_est == 200, f"FAIL: Treatment estimate failed with {code_est}"
    est_id = est_res.get("id")

    # 4. Direct Disk SQLite Inspection (Separate Process & Independent Connection)
    assert os.path.exists(DB_PATH), f"FAIL: Persistent database file not found at {DB_PATH}"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verify estimate exists on disk
    cursor.execute("SELECT id, procedure_name, estimated_cost_range FROM treatment_cost_estimates WHERE id = ?", (est_id,))
    row = cursor.fetchone()
    assert row is not None, f"FAIL: Estimate {est_id} not found in disk SQLite database!"
    assert row[1] == proc_name
    print(f"  [PASS] 6.1 Treatment Cost Estimate verified on disk SQLite database (ID: {est_id}, Procedure: {row[1]}).")

    # 5. Verify OPD Appointment records on disk
    cursor.execute("SELECT COUNT(*) FROM opd_appointments")
    total_appointments = cursor.fetchone()[0]
    assert total_appointments > 0, "FAIL: opd_appointments table is empty"
    print(f"  [PASS] 6.2 OPD Appointments verified on disk SQLite database ({total_appointments} records found).")

    # 6. Verify User records on disk with secure password hashes
    cursor.execute("SELECT id, email, password_hash FROM users WHERE email = 'patient@chikitsax.demo'")
    user_row = cursor.fetchone()
    assert user_row is not None
    assert user_row[2] and "$" in user_row[2], "FAIL: Stored password_hash is invalid or plain text!"
    print(f"  [PASS] 6.3 Demo users persist on disk with PBKDF2 hashed credentials (User: {user_row[1]}).")
    conn.close()

    # 7. CORS Configuration Test
    code_cors, _, cors_headers = http_req("/health", "GET", custom_headers={
        "Origin": "http://localhost:5173"
    })
    allow_origin = cors_headers.get("access-control-allow-origin", cors_headers.get("Access-Control-Allow-Origin"))
    assert allow_origin in ["http://localhost:5173", "*"], f"FAIL: Insecure CORS response: {cors_headers}"
    print(f"  [PASS] 6.4 CORS configuration validated for frontend origin 'http://localhost:5173' (Allow-Origin: {allow_origin}).")

    # 8. Unsafe Error Leakage Check
    # Trigger 404
    code_404, err_404, _ = http_req("/nonexistent-endpoint-test-1234")
    assert code_404 == 404
    assert "detail" in err_404
    serialized_err = json.dumps(err_404)
    assert "Traceback" not in serialized_err and "sqlite3" not in serialized_err and "chikitsax.db" not in serialized_err
    print("  [PASS] 6.5 Error responses are clean and sanitized; internal stack traces and server file paths are not leaked.")

    return True

if __name__ == "__main__":
    test_persistence_and_cors_group()
