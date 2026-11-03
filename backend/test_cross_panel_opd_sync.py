import urllib.request
import urllib.error
import json
import time

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
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            parsed = json.loads(content)
        except Exception:
            parsed = {"detail": content}
        return e.code, parsed

def main():
    print("=================================================================")
    print("CHIKITSA-X E2E Cross-Panel OPD Real-Time Synchronization Test")
    print("=================================================================")

    # 1. Authenticate Patient
    status, p_res = api_call("POST", "/auth/login", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    assert status == 200, f"Patient login failed: {p_res}"
    p_token = p_res["accessToken"]
    p_id = p_res["user"]["id"]
    print(f"✅ 1. Patient Authenticated (ID: {p_id})")

    # 2. Authenticate Doctor
    status, d_res = api_call("POST", "/auth/login", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    assert status == 200, f"Doctor login failed: {d_res}"
    d_token = d_res["accessToken"]
    d_id = d_res["user"]["id"]
    print(f"✅ 2. Doctor Authenticated (ID: {d_id})")

    # 3. Authenticate Hospital Staff
    status, h_res = api_call("POST", "/auth/login", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_STAFF"
    })
    assert status == 200, f"Hospital login failed: {h_res}"
    h_token = h_res["accessToken"]
    print("✅ 3. Hospital Staff Authenticated")

    # 4. Patient Books an OPD Appointment
    ts = int(time.time() * 1000)
    test_date = f"18 Dec 2026"
    test_time = f"{(ts // 1000) % 11 + 1}:{(ts % 50) + 10:02d} AM"

    booking_payload = {
        "patient_id": p_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": test_date,
        "appointment_time": test_time
    }
    status, appointment = api_call("POST", "/opd", booking_payload, token=p_token)
    assert status == 200, f"Booking failed: {appointment}"
    app_id = appointment["id"]
    ref_id = appointment["reference_id"]
    assert appointment["status"] == "CONFIRMED"
    print(f"✅ 4. Patient Booked Appointment: Ref {ref_id}, Slot: {test_date} at {test_time}")

    # 5. Doctor Panel Checks Queue
    status, doc_appointments = api_call("GET", "/opd?doctor_id=doc-1", token=d_token)
    assert status == 200, f"Doctor queue query failed: {doc_appointments}"
    matching_in_doc = next((a for a in doc_appointments if a["id"] == app_id), None)
    assert matching_in_doc is not None, "Appointment does not appear in Doctor queue!"
    assert matching_in_doc["status"] == "CONFIRMED"
    print(f"✅ 5. Doctor Panel verified: Found appointment in Doctor queue ({len(doc_appointments)} in queue)")

    # 6. Hospital Panel Checks Queue
    status, hosp_appointments = api_call("GET", "/opd?hospital_id=hosp-1", token=h_token)
    assert status == 200, f"Hospital queue query failed: {hosp_appointments}"
    matching_in_hosp = next((a for a in hosp_appointments if a["id"] == app_id), None)
    assert matching_in_hosp is not None, "Appointment does not appear in Hospital queue!"
    print(f"✅ 6. Hospital Panel verified: Found appointment in Hospital queue ({len(hosp_appointments)} in queue)")

    # 7. Slot Collision Prevention Test (Double Booking rejected)
    status, dup_res = api_call("POST", "/opd", booking_payload, token=p_token)
    assert status == 409, f"Double booking should return 409, got {status}: {dup_res}"
    print("✅ 7. Double-booking conflict prevented (409 Conflict returned)")

    # 8. Hospital Reception Scans & Verifies QR Pass Check-In
    status, verify_res = api_call("POST", "/hospital/verify", {
        "reference_id": ref_id,
        "staff_name": "Reception Desk Staff (Anil)"
    }, token=h_token)
    assert status == 200, f"QR verification failed: {verify_res}"
    assert verify_res["verified"] is True
    print(f"✅ 8. Hospital Reception verified QR Pass: Status is now VERIFIED")

    # 9. Verify Doctor Queue immediately shows VERIFIED
    status, doc_queue_after = api_call("GET", "/opd?doctor_id=doc-1", token=d_token)
    assert status == 200
    doc_app_after = next(a for a in doc_queue_after if a["id"] == app_id)
    assert doc_app_after["status"] == "VERIFIED", f"Expected VERIFIED, got {doc_app_after['status']}"
    print("✅ 9. Doctor Queue synchronization verified: Appointment status updated to VERIFIED")

    # 10. Reschedule Appointment by Patient
    now_ts = int(time.time() * 1000)
    resched_date = f"{(now_ts % 25) + 1} Nov 2028"
    resched_time = f"03:{(now_ts % 50) + 10:02d} PM"
    status, resched_data = api_call("PUT", f"/opd/{app_id}/reschedule", {
        "appointment_date": resched_date,
        "appointment_time": resched_time
    }, token=p_token)
    assert status == 200, f"Reschedule failed: {resched_data}"
    assert resched_data["appointment_date"] == resched_date
    assert resched_data["appointment_time"] == resched_time
    print(f"✅ 10. Patient Rescheduled Appointment to {resched_date} at {resched_time}")

    # 11. Verify Doctor Queue reflects the new slot
    status, doc_queue_resched = api_call("GET", "/opd?doctor_id=doc-1", token=d_token)
    assert status == 200
    doc_app_resched = next(a for a in doc_queue_resched if a["id"] == app_id)
    assert doc_app_resched["appointment_date"] == resched_date
    assert doc_app_resched["appointment_time"] == resched_time
    print(f"✅ 11. Doctor Panel verified: Rescheduled slot matches {resched_date} at {resched_time}")

    # 12. Patient Cancels Appointment
    status, cancel_res = api_call("PUT", f"/opd/{app_id}/cancel", token=p_token)
    assert status == 200, f"Cancel failed: {cancel_res}"
    assert cancel_res["status"] == "CANCELLED"
    print("✅ 12. Patient Cancelled Appointment: Status is CANCELLED")

    # 13. Verify Doctor Panel sees CANCELLED status and slot freed
    status, doc_queue_cancelled = api_call("GET", "/opd?doctor_id=doc-1", token=d_token)
    assert status == 200
    doc_app_cancelled = next(a for a in doc_queue_cancelled if a["id"] == app_id)
    assert doc_app_cancelled["status"] == "CANCELLED"
    print("✅ 13. Doctor Panel verified: Appointment updated to CANCELLED in real-time")

    # 14. Re-booking the freed slot succeeds (Slot lock was released upon cancellation)
    rebook_payload = {
        "patient_id": p_id,
        "hospital_id": "hosp-1",
        "doctor_id": "doc-1",
        "department": "Cardiology",
        "appointment_date": resched_date,
        "appointment_time": resched_time
    }
    status, rebook_res = api_call("POST", "/opd", rebook_payload, token=p_token)
    assert status == 200, f"Re-booking freed slot failed: {rebook_res}"
    print(f"✅ 14. Released slot re-booking confirmed (Ref: {rebook_res['reference_id']})")

    # 15. Verify Cross-Patient Isolation (Patient 2 cannot see Patient 1's appointments)
    status, p2_res = api_call("POST", "/auth/register", {
        "email": f"patient2_{ts}@demo.com",
        "password": "Password123!",
        "name": "Ananya Sharma",
        "phone": "+91 99999 88888",
        "role": "PATIENT"
    })
    assert status == 200, f"Patient 2 register failed: {p2_res}"
    p2_token = p2_res["accessToken"]

    status, p2_apps = api_call("GET", "/opd", token=p2_token)
    assert status == 200
    assert not any(a["id"] == app_id for a in p2_apps), "Patient 2 was able to see Patient 1's appointment!"
    print("✅ 15. Cross-Patient Isolation verified: Patient 2 cannot see Patient 1's appointments")

    print("\n🎉 ALL 15 CROSS-PANEL OPD SYNCHRONIZATION TESTS PASSED! 🎉")

if __name__ == "__main__":
    main()
