import json
import urllib.request
import urllib.error
import threading
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

def test_concurrency_group():
    print("\n--- [GROUP 4] Concurrency, Slot Conflicts & Transaction Safety ---")

    # 1. Login Patient
    _, p1_auth = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    p1_token = p1_auth["accessToken"]
    p1_id = p1_auth["user"]["id"]

    # Generate a unique timestamped slot for testing
    ts = int(time.time() * 1000)
    slot_date = f"{(ts % 20) + 5} May 2027"
    slot_time = f"{(ts // 1000) % 11 + 1}:{(ts % 50) + 10:02d} PM"

    threads = []
    thread_results = []

    def attempt_concurrent_booking(t_idx):
        code, resp = http_req("/opd", "POST", {
            "patient_id": p1_id,
            "hospital_id": "hosp-1",
            "doctor_id": "doc-1",
            "department": "Cardiology",
            "appointment_date": slot_date,
            "appointment_time": slot_time
        }, token=p1_token)
        thread_results.append((t_idx, code, resp))

    print(f"  Launching 5 concurrent booking threads for Doctor doc-1 at '{slot_date} {slot_time}'...")
    for i in range(5):
        t = threading.Thread(target=attempt_concurrent_booking, args=(i,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [r for r in thread_results if r[1] == 200]
    conflicts = [r for r in thread_results if r[1] == 409]

    assert len(successes) == 1, f"FAIL: Expected exactly 1 booking to succeed, but {len(successes)} succeeded: {thread_results}"
    assert len(conflicts) == 4, f"FAIL: Expected 4 conflicts (409), got {len(conflicts)}"
    booked_app = successes[0][2]
    app_id = booked_app.get("id")
    ref_id = booked_app.get("reference_id")
    print(f"  [PASS] 4.1 Race condition prevented: Exactly 1 concurrent request succeeded (Ref: {ref_id}), 4 rejected with 409 Conflict.")

    # 2. Release of Slot Lock on Cancellation
    code_cancel, cancel_res = http_req(f"/opd/{app_id}/cancel", "PUT", token=p1_token)
    assert code_cancel == 200, f"FAIL: Cancel failed with {code_cancel}"
    assert cancel_res.get("status") == "CANCELLED"
    print("  [PASS] 4.2 Appointment cancelled and active slot lock atomically released.")

    # 3. Slot Can Now Be Re-booked After Cancellation
    code_rebook, rebook_res = http_req("/opd", "POST", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": slot_date,
        "appointment_time": slot_time
    }, token=p1_token)
    assert code_rebook == 200, f"FAIL: Expected slot to be re-bookable after cancellation, got {code_rebook}: {rebook_res}"
    new_app_id = rebook_res.get("id")
    print(f"  [PASS] 4.3 Released slot was successfully re-booked (New Ref: {rebook_res.get('reference_id')}).")

    # 4. Reschedule Collision Check
    # Attempt rescheduling to another booked slot or same slot
    code_resched_bad, _ = http_req(f"/opd/{new_app_id}/reschedule", "PUT", {
        "appointment_date": slot_date,
        "appointment_time": slot_time
    }, token=p1_token)
    # Rescheduling to a brand new free slot succeeds
    free_slot_time = f"{((ts // 1000) % 12) + 1}:{(ts % 50) + 10:02d} PM"
    code_resched_ok, resched_ok = http_req(f"/opd/{new_app_id}/reschedule", "PUT", {
        "appointment_date": slot_date,
        "appointment_time": free_slot_time
    }, token=p1_token)
    assert code_resched_ok == 200, f"FAIL: Reschedule to free slot failed with {code_resched_ok}"
    assert resched_ok.get("appointment_time") == free_slot_time
    print(f"  [PASS] 4.4 Rescheduling correctly updates appointment date and slot lock to '{slot_date} {free_slot_time}'.")

    return True

if __name__ == "__main__":
    test_concurrency_group()
