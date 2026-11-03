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

def test_qr_security_group():
    print("\n--- [GROUP 5] QR Pass Verification, Replay & Cross-Hospital Security ---")

    # 1. Login Patient
    _, p1_auth = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    p1_token = p1_auth["accessToken"]
    p1_id = p1_auth["user"]["id"]

    # 1.5 Login Hospital 1 Admin
    _, h1_auth = http_req("/auth/login", "POST", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_ADMIN"
    })
    h1_token = h1_auth["accessToken"]

    # 2. Book appointment at Hospital 1 (CarePlus Super Specialty Hospital, hosp-1)
    ts = int(time.time() * 1000)
    slot_date = f"{(ts % 25) + 1} Jun 2027"
    slot_time = f"{((ts // 1000) % 12) + 1}:{(ts % 50) + 10:02d} AM"
    code_book, opd = http_req("/opd", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": slot_date,
        "appointment_time": slot_time
    }, token=p1_token)
    assert code_book == 200, f"FAIL: Booking failed with {code_book}"
    ref_id = opd.get("reference_id")
    app_id = opd.get("id")
    assert opd.get("status") == "CONFIRMED"
    print(f"  Booked test appointment at hosp-1: Ref: {ref_id}, ID: {app_id}, Status: CONFIRMED")

    # 3. Cross-Hospital Verification Attack: Hospital 2 / unauthenticated tries to verify Hospital 1's appointment
    code_wrong, wrong_res = http_req("/hospital/verify", "POST", {
        "reference_id": ref_id,
        "hospital_id": "hosp-2",
        "staff_name": "Receptionist at Metro City Hospital"
    })
    assert code_wrong in [401, 403] or wrong_res.get("verified") is False, f"SECURITY DEFECT: Unauthorized hospital verified appointment! {wrong_res}"
    print("  [PASS] 5.1 Cross-hospital verification blocked: Hospital 2 rejected when attempting to verify Hospital 1 pass.")

    # 4. Legitimate Verification by Hospital 1 Desk
    code_legit, legit_res = http_req("/hospital/verify", "POST", {
        "reference_id": ref_id,
        "hospital_id": "hosp-1",
        "staff_name": "CarePlus Reception Desk"
    }, token=h1_token)
    assert legit_res.get("verified") is True, f"FAIL: Legitimate check-in failed: {legit_res}"
    assert legit_res.get("status") == "VERIFIED"
    print(f"  [PASS] 5.2 Legitimate QR check-in verified by Hospital 1 (Status: {legit_res.get('status')}).")

    # 5. QR Token Replay / Double Check-in Attack
    code_replay, replay_res = http_req("/hospital/verify", "POST", {
        "reference_id": ref_id,
        "hospital_id": "hosp-1",
        "staff_name": "CarePlus Reception Desk"
    }, token=h1_token)
    assert replay_res.get("verified") is False, f"SECURITY DEFECT: Replayed QR pass was accepted! {replay_res}"
    print("  [PASS] 5.3 Replay protection enforced: Already-verified QR pass rejected on re-use attempt.")

    # 6. Cancellation Status Transition & Cancelled QR Pass Verification
    # Book another appointment and cancel it
    _, cancel_target = http_req("/opd", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": f"{(ts % 25) + 1} Jul 2027",
        "appointment_time": f"{((ts // 1000) % 12) + 1}:{(ts % 40) + 20:02d} PM"
    }, token=p1_token)
    ref_cancelled = cancel_target.get("reference_id")
    app_cancelled = cancel_target.get("id")

    # Patient cancels appointment
    code_cancel, cancel_res = http_req(f"/opd/{app_cancelled}/cancel", "PUT", token=p1_token)
    assert code_cancel == 200 and cancel_res.get("status") == "CANCELLED"

    # Attempt to verify cancelled appointment pass at hospital desk
    code_cancel_check, cancel_verify_res = http_req("/hospital/verify", "POST", {
        "reference_id": ref_cancelled,
        "hospital_id": "hosp-1",
        "staff_name": "CarePlus Reception Desk"
    }, token=h1_token)
    assert cancel_verify_res.get("verified") is False, f"SECURITY DEFECT: Cancelled pass was accepted! {cancel_verify_res}"
    print("  [PASS] 5.4 Cancelled pass rejection enforced: Cancelled appointment cannot be checked in.")

    return True

if __name__ == "__main__":
    test_qr_security_group()
