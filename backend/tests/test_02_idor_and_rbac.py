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

def test_idor_and_rbac_group():
    print("\n--- [GROUP 2] IDOR Vulnerabilities & Role-Based Authorization ---")

    # 1. Login Patient 1 (Legitimate Owner)
    _, p1_auth = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    p1_token = p1_auth["accessToken"]
    p1_id = p1_auth["user"]["id"]

    # 2. Register Patient 2 (Attacker / Different Patient)
    p2_email = f"attacker_{int(time.time()*1000)}@test.com"
    _, p2_auth = http_req("/auth/register", "POST", {
        "email": p2_email,
        "password": "AttackerPass123!",
        "name": "Attacker Patient",
        "role": "PATIENT"
    })
    p2_token = p2_auth["accessToken"]
    p2_id = p2_auth["user"]["id"]

    # 2.0 Unauthenticated Profile & Records Access Rejection
    code_anon_get, _ = http_req(f"/patients/{p1_id}", "GET")
    assert code_anon_get == 401, f"SECURITY DEFECT: Unauthenticated profile read returned {code_anon_get}"
    code_anon_put, _ = http_req(f"/patients/{p1_id}", "PUT", {"fullName": "Hacker Name"})
    assert code_anon_put == 401, f"SECURITY DEFECT: Unauthenticated profile modify returned {code_anon_put}"
    code_anon_prof, _ = http_req(f"/patients/{p1_id}/profile", "GET")
    assert code_anon_prof == 401, f"SECURITY DEFECT: Unauthenticated unified profile read returned {code_anon_prof}"
    code_anon_rec, _ = http_req(f"/medical-records/{p1_id}", "GET")
    assert code_anon_rec == 401, f"SECURITY DEFECT: Unauthenticated medical records read returned {code_anon_rec}"
    print("  [PASS] 2.0 Mandatory Authentication: Unauthenticated requests to patient profile and records strictly rejected with 401 Unauthorized.")

    # 2.1 IDOR Profile Read
    code_read, _ = http_req(f"/patients/{p1_id}", "GET", token=p2_token)
    assert code_read == 403, f"FAIL: Expected 403 Forbidden on IDOR profile read, got {code_read}"
    print(f"  [PASS] 2.1 IDOR Protected: Patient 2 cannot access Patient 1's profile (Returned {code_read} Forbidden).")

    # 2.2 IDOR Profile Tamper
    code_tamper, _ = http_req(f"/patients/{p1_id}", "PUT", {"fullName": "Attacker Injected Name"}, token=p2_token)
    assert code_tamper == 403, f"FAIL: Expected 403 Forbidden on IDOR profile tamper, got {code_tamper}"
    print(f"  [PASS] 2.2 IDOR Protected: Patient 2 cannot modify Patient 1's profile (Returned {code_tamper} Forbidden).")

    # 2.3 IDOR Medical Records Read
    code_records, _ = http_req(f"/medical-records/{p1_id}", "GET", token=p2_token)
    assert code_records == 403, f"FAIL: Expected 403 Forbidden on IDOR medical records access, got {code_records}"
    print(f"  [PASS] 2.3 IDOR Protected: Patient 2 cannot access Patient 1's medical records (Returned {code_records} Forbidden).")

    # 2.4 IDOR Appointment Cancellation & Rescheduling
    # Book appointment for Patient 1
    ts = int(time.time() * 1000)
    slot_date = f"{(ts % 25) + 1} Apr 2027"
    slot_time = f"09:15 AM"
    code_app, app_data = http_req("/opd", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": slot_date,
        "appointment_time": slot_time
    }, token=p1_token)
    assert code_app == 200, f"FAIL: Booking failed: {app_data}"
    app_id = app_data["id"]

    # Patient 2 attempts cancelling Patient 1's appointment
    code_cancel, err_cancel = http_req(f"/opd/{app_id}/cancel", "PUT", token=p2_token)
    assert code_cancel == 403, f"FAIL: Expected 403 Forbidden on cancelling other patient's appointment, got {code_cancel}"
    print(f"  [PASS] 2.4 IDOR Protected: Patient 2 cannot cancel Patient 1's appointment (Returned {code_cancel} Forbidden).")

    # Patient 2 attempts rescheduling Patient 1's appointment
    code_resched, _ = http_req(f"/opd/{app_id}/reschedule", "PUT", {
        "appointment_date": "28 Apr 2027",
        "appointment_time": "11:00 AM"
    }, token=p2_token)
    assert code_resched == 403, f"FAIL: Expected 403 Forbidden on rescheduling other patient's appointment, got {code_resched}"
    print(f"  [PASS] 2.5 IDOR Protected: Patient 2 cannot reschedule Patient 1's appointment (Returned {code_resched} Forbidden).")

    # Patient 1 (legitimate owner) cancels their own appointment
    code_own_cancel, own_res = http_req(f"/opd/{app_id}/cancel", "PUT", token=p1_token)
    assert code_own_cancel == 200, f"FAIL: Legitimate owner cancel failed with {code_own_cancel}"
    assert own_res.get("status") == "CANCELLED"
    print("  [PASS] 2.6 Legitimate owner authorized: Patient 1 successfully cancelled their own appointment.")

    return True

if __name__ == "__main__":
    test_idor_and_rbac_group()
