import urllib.request
import urllib.error
import json
import time
import datetime
import sqlite3
import threading
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
    print("CHIKITSA-X Phase 4.4: Doctor Scheduling & OPD Slot Sync Tests")
    print("=========================================================================")

    ts = int(time.time())
    passed_tests = 0
    total_tests = 12

    # --- Setup Actors ---
    # 0. Login Hospital Admin (CarePlus - hosp-1)
    st, h1_res = api_call("POST", "/auth/login", {
        "email": "hospital@chikitsax.demo",
        "password": "demo123",
        "role": "HOSPITAL_ADMIN"
    })
    assert st == 200, f"Hospital admin login failed: {h1_res}"
    h1_token = h1_res["accessToken"]

    # 1. Login Doctor 1 (Dr. Rajesh Kulkarni - doc-1)
    st, d1_res = api_call("POST", "/auth/login", {
        "email": "doctor@chikitsax.demo",
        "password": "demo123",
        "role": "DOCTOR"
    })
    assert st == 200, f"Doctor 1 login failed: {d1_res}"
    d1_token = d1_res["accessToken"]
    d1_user_id = d1_res["user"]["id"]
    d1_doc_id = "doc-1"

    # 2. Register Doctor 2 (Dr. Ananya Roy - doc-2) via authorized Hospital Admin
    d2_email = f"doctor2_sched_{ts}@chikitsax.test"
    st, d2_res = api_call("POST", "/auth/register", {
        "name": f"Dr. Ananya Roy {ts}",
        "fullName": f"Dr. Ananya Roy {ts}",
        "email": d2_email,
        "phone": "+91 97888 11111",
        "password": "Password123!",
        "role": "DOCTOR",
        "hospitalId": "hosp-1"
    }, token=h1_token)
    assert st == 200, f"Doctor 2 registration failed: {d2_res}"
    d2_token = d2_res["accessToken"]
    d2_user_id = d2_res["user"]["id"]

    # 3. Register Patient 1
    p1_email = f"patient1_sched_{ts}@chikitsax.test"
    st, p1_res = api_call("POST", "/auth/register", {
        "name": f"Kavita Verma {ts}",
        "fullName": f"Kavita Verma {ts}",
        "email": p1_email,
        "phone": "+91 97999 22222",
        "password": "Password123!",
        "role": "PATIENT"
    })
    assert st == 200, f"Patient 1 registration failed: {p1_res}"
    p1_token = p1_res["accessToken"]
    p1_id = p1_res["user"]["id"]

    print("Actors setup complete:")
    print(f"  - Doctor 1 (doc-1): {d1_user_id}")
    print(f"  - Doctor 2: {d2_user_id}")
    print(f"  - Patient 1: {p1_id}")

    # -------------------------------------------------------------------------
    # TEST 1: Authenticated doctor can retrieve their own schedule
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Doctor Retrieves Own Schedule (GET /api/doctors/me/schedule) ---")
    st, sched_me = api_call("GET", "/doctors/me/schedule", token=d1_token)
    assert st == 200, f"Expected 200 for doctor me schedule, got {st}: {sched_me}"
    assert "weeklySchedule" in sched_me or "weekly_schedule" in sched_me, "Missing weekly schedule in response"
    weekly = sched_me.get("weeklySchedule") or sched_me.get("weekly_schedule")
    assert isinstance(weekly, list) and len(weekly) >= 5, f"Expected weekly timetable, got {weekly}"
    print(f"  ✓ Doctor retrieved {len(weekly)} schedule days. First day: {weekly[0]['day']} ({weekly[0]['time']})")

    st2, sched_d1 = api_call("GET", f"/doctors/{d1_doc_id}/schedule", token=d1_token)
    assert st2 == 200, f"Expected 200 for /doctors/{d1_doc_id}/schedule, got {st2}: {sched_d1}"

    passed_tests += 1
    print("✓ PASS: Authenticated doctor successfully retrieved their own schedule.")

    # -------------------------------------------------------------------------
    # TEST 2: Unauthenticated user cannot modify schedule (401 Unauthorized)
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Unauthenticated Modification Rejection (401 Unauthorized) ---")
    st, res = api_call("PUT", f"/doctors/{d1_doc_id}/schedule", {
        "weeklySchedule": [{"day": "Monday", "time": "09:00 AM - 01:00 PM", "slots": 10, "isBlocked": True}]
    })
    assert st == 401, f"Expected 401 for unauthenticated PUT schedule, got {st}: {res}"

    st, res = api_call("POST", f"/doctors/{d1_doc_id}/block-slot", {
        "day": "Monday"
    })
    assert st == 401, f"Expected 401 for unauthenticated block-slot, got {st}: {res}"

    passed_tests += 1
    print("✓ PASS: Unauthenticated schedule modifications rejected with 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # TEST 3: Doctor cannot modify another doctor's schedule (403 Forbidden)
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Cross-Doctor Schedule Tampering Prevention (403 Forbidden) ---")
    st, res = api_call("PUT", f"/doctors/{d1_doc_id}/schedule", {
        "weeklySchedule": [{"day": "Monday", "time": "09:00 AM - 01:00 PM", "slots": 10, "isBlocked": True}]
    }, token=d2_token)
    assert st == 403, f"Expected 403 when Doctor 2 updates Doctor 1 schedule, got {st}: {res}"

    st, res = api_call("POST", f"/doctors/{d1_doc_id}/block-slot", {
        "day": "Monday"
    }, token=d2_token)
    assert st == 403, f"Expected 403 when Doctor 2 blocks Doctor 1 slot, got {st}: {res}"

    passed_tests += 1
    print("✓ PASS: Doctor attempting to modify another doctor's schedule strictly rejected with 403.")

    # -------------------------------------------------------------------------
    # TEST 4: Patient cannot block or unblock doctor slots (403 Forbidden)
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Patient Role Access Gate (403 Forbidden) ---")
    st, res = api_call("PUT", f"/doctors/{d1_doc_id}/schedule", {
        "weeklySchedule": [{"day": "Monday", "time": "09:00 AM - 01:00 PM", "slots": 10, "isBlocked": True}]
    }, token=p1_token)
    assert st == 403, f"Expected 403 when Patient modifies doctor schedule, got {st}: {res}"

    st, res = api_call("POST", f"/doctors/{d1_doc_id}/block-slot", {
        "day": "Tuesday"
    }, token=p1_token)
    assert st == 403, f"Expected 403 when Patient blocks doctor slot, got {st}: {res}"

    passed_tests += 1
    print("✓ PASS: Patient attempting to modify doctor schedule rejected with 403 Forbidden.")

    # Helper for generating future dates that are strictly on unblocked weekdays (Mon/Tue/Thu/Fri)
    def get_future_working_date(day_offset: int) -> str:
        # 2028-11-13 is Monday. Adding full weeks keeps it aligned.
        base_monday = datetime.date(2028, 11, 13) + datetime.timedelta(weeks=(int(ts) % 50) + 1)
        # Select among Mon (0), Tue (1), Thu (3), Fri (4)
        valid_offsets = [0, 1, 3, 4]
        day = base_monday + datetime.timedelta(days=valid_offsets[day_offset % len(valid_offsets)])
        return day.isoformat()

    # -------------------------------------------------------------------------
    # TEST 5: Blocking an available slot persists to SQLite
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Doctor Blocks Available Slot & Persists to SQLite ---")
    test_block_date = get_future_working_date(0)
    test_block_time = "10:00 AM"

    st, block_res = api_call("POST", "/doctors/me/block-slot", {
        "date": test_block_date,
        "time": test_block_time,
        "reason": "Cardiology Conference & Cath Lab Training"
    }, token=d1_token)
    assert st == 200, f"Expected 200 for block-slot, got {st}: {block_res}"

    # Verify SQLite database contains the blocked slot
    db_row = query_db("SELECT blocked_slots FROM doctors WHERE id = ?", (d1_doc_id,))
    assert len(db_row) == 1, f"Doctor row not found in SQLite: {db_row}"
    blocked_json = json.loads(db_row[0][0]) if db_row[0][0] else []
    found_block = any(
        (b.get("date") == test_block_date and b.get("time") == test_block_time) or
        b.get("slot") == f"{test_block_date}#{test_block_time}"
        for b in blocked_json if isinstance(b, dict)
    )
    assert found_block, f"Blocked slot {test_block_date} {test_block_time} not found in SQLite blocked_slots: {blocked_json}"
    print(f"  ✓ Confirmed in SQLite: {test_block_date} {test_block_time} is persisted in doctors.blocked_slots")

    # Verify patient availability API marks it as blocked
    st, avail_res = api_call("GET", f"/doctors/{d1_doc_id}/availability?date={test_block_date}")
    assert st == 200, f"Expected 200 for availability check, got {st}: {avail_res}"
    matched_slot = next((s for s in avail_res["slots"] if s["time"] == test_block_time), None)
    assert matched_slot is not None, f"Slot {test_block_time} not in availability slots: {avail_res}"
    assert matched_slot["is_blocked"] is True or matched_slot["isBlocked"] is True, f"Expected isBlocked=True, got {matched_slot}"
    assert matched_slot["is_available"] is False or matched_slot["isAvailable"] is False, f"Expected isAvailable=False, got {matched_slot}"

    passed_tests += 1
    print(f"✓ PASS: Slot {test_block_date} at {test_block_time} persisted to SQLite and reflected in availability.")

    # -------------------------------------------------------------------------
    # TEST 6: A blocked slot is rejected during booking (409 Conflict)
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Booking Blocked Slot Rejection (409 Conflict) ---")
    st, book_err = api_call("POST", "/opd", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": d1_doc_id,
        "department": "Cardiology",
        "appointment_date": test_block_date,
        "appointment_time": test_block_time
    }, token=p1_token)
    assert st == 409, f"Expected 409 when booking blocked slot, got {st}: {book_err}"
    assert "blocked" in str(book_err.get("detail", "")).lower(), f"Expected blocked message, got: {book_err}"

    passed_tests += 1
    print("✓ PASS: Patient booking into blocked slot correctly rejected with 409 Conflict.")

    # -------------------------------------------------------------------------
    # TEST 7: A blocked slot is rejected during rescheduling (409 Conflict)
    # -------------------------------------------------------------------------
    print("\n--- TEST 7: Rescheduling Into Blocked Slot Rejection (409 Conflict) ---")
    # Patient books a valid free slot first
    valid_date = get_future_working_date(1)
    valid_time = "11:00 AM"
    st, app_res = api_call("POST", "/opd", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": d1_doc_id,
        "department": "Cardiology",
        "appointment_date": valid_date,
        "appointment_time": valid_time
    }, token=p1_token)
    assert st == 200, f"Booking valid appointment failed: {app_res}"
    app_id = app_res["id"]

    # Now attempt to reschedule into the blocked slot
    st, resched_err = api_call("PUT", f"/opd/{app_id}/reschedule", {
        "appointment_date": test_block_date,
        "appointment_time": test_block_time
    }, token=p1_token)
    assert st == 409, f"Expected 409 when rescheduling to blocked slot, got {st}: {resched_err}"
    assert "blocked" in str(resched_err.get("detail", "")).lower(), f"Expected blocked message, got: {resched_err}"

    passed_tests += 1
    print("✓ PASS: Rescheduling into blocked slot strictly prevented with 409 Conflict.")

    # -------------------------------------------------------------------------
    # TEST 8: Blocking slot with existing confirmed appointment returns conflict
    # -------------------------------------------------------------------------
    print("\n--- TEST 8: Conflict When Blocking Slot With Active Confirmed Appointment ---")
    # app_id is confirmed at valid_date, valid_time ("02:00 PM")
    st, block_conflict = api_call("POST", "/doctors/me/block-slot", {
        "date": valid_date,
        "time": valid_time,
        "reason": "Attempting to block occupied slot"
    }, token=d1_token)
    assert st == 409, f"Expected 409 conflict when blocking slot with confirmed appointment, got {st}: {block_conflict}"
    print(f"  ✓ Block rejected with 409: {block_conflict.get('detail')}")

    # Verify existing appointment is NOT deleted or cancelled
    db_app = query_db("SELECT id, status, reference_id FROM opd_appointments WHERE id = ?", (app_id,))
    assert len(db_app) == 1, "Appointment was deleted or lost"
    assert db_app[0][1] == "CONFIRMED", f"Appointment status modified unexpectedly: {db_app[0][1]}"

    passed_tests += 1
    print("✓ PASS: Blocking occupied slot rejected with 409; confirmed appointment preserved intact.")

    # -------------------------------------------------------------------------
    # TEST 9: Unblocking a slot restores availability when no other conflict exists
    # -------------------------------------------------------------------------
    print("\n--- TEST 9: Unblocking Restores Slot Availability ---")
    st, unblock_res = api_call("POST", "/doctors/me/unblock-slot", {
        "date": test_block_date,
        "time": test_block_time
    }, token=d1_token)
    assert st == 200, f"Expected 200 for unblock-slot, got {st}: {unblock_res}"

    # Verify SQLite database no longer contains the blocked slot
    db_row = query_db("SELECT blocked_slots FROM doctors WHERE id = ?", (d1_doc_id,))
    blocked_json = json.loads(db_row[0][0]) if db_row[0][0] else []
    still_blocked = any(
        (b.get("date") == test_block_date and b.get("time") == test_block_time) or
        b.get("slot") == f"{test_block_date}#{test_block_time}"
        for b in blocked_json if isinstance(b, dict)
    )
    assert not still_blocked, f"Slot still present in blocked_slots after unblock: {blocked_json}"

    # Patient can now successfully book the unblocked slot
    st, rebook_res = api_call("POST", "/opd", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": d1_doc_id,
        "department": "Cardiology",
        "appointment_date": test_block_date,
        "appointment_time": test_block_time
    }, token=p1_token)
    assert st == 200, f"Booking unblocked slot failed: {rebook_res}"
    print(f"  ✓ Successfully booked previously unblocked slot: Ref {rebook_res['reference_id']}")

    passed_tests += 1
    print("✓ PASS: Unblocking restored availability and enabled patient booking.")

    # -------------------------------------------------------------------------
    # TEST 10: Concurrent booking attempts cannot create duplicate appointments
    # -------------------------------------------------------------------------
    print("\n--- TEST 10: Concurrency Race Condition Safety ---")
    concurrent_date = get_future_working_date(2)
    concurrent_time = "11:30 AM"

    threads = []
    results = []

    def make_booking(idx):
        st, res = api_call("POST", "/opd", {
            "patient_id": p1_id,
            "hospital_id": "hosp-1",
            "doctor_id": d1_doc_id,
            "department": "Cardiology",
            "appointment_date": concurrent_date,
            "appointment_time": concurrent_time
        }, token=p1_token)
        results.append((idx, st, res))

    print(f"  Firing 5 simultaneous booking threads for {concurrent_date} at {concurrent_time}...")
    for i in range(5):
        t = threading.Thread(target=make_booking, args=(i,))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = [r for r in results if r[1] == 200]
    conflicts = [r for r in results if r[1] == 409]
    assert len(successes) == 1, f"Expected exactly 1 booking to succeed, but {len(successes)} succeeded: {results}"
    assert len(conflicts) == 4, f"Expected 4 conflicts (409), got {len(conflicts)}"

    passed_tests += 1
    print(f"✓ PASS: Exactly 1 concurrent booking succeeded (Ref: {successes[0][2]['reference_id']}), 4 rejected with 409.")

    # -------------------------------------------------------------------------
    # TEST 11: Concurrent schedule update and booking safety
    # -------------------------------------------------------------------------
    print("\n--- TEST 11: Schedule Update & Booking Concurrency Safety ---")
    race_date = get_future_working_date(3)
    race_time = "10:30 AM"
    race_results = []

    def client_book():
        st, res = api_call("POST", "/opd", {
            "patient_id": p1_id,
            "hospital_id": "hosp-1",
            "doctor_id": d1_doc_id,
            "department": "Cardiology",
            "appointment_date": race_date,
            "appointment_time": race_time
        }, token=p1_token)
        race_results.append(("BOOK", st, res))

    def doctor_block():
        st, res = api_call("POST", "/doctors/me/block-slot", {
            "date": race_date,
            "time": race_time,
            "reason": "Immediate emergency block"
        }, token=d1_token)
        race_results.append(("BLOCK", st, res))

    t_book = threading.Thread(target=client_book)
    t_block = threading.Thread(target=doctor_block)

    t_book.start()
    t_block.start()
    t_book.join()
    t_block.join()

    # Either booking succeeds first (and block gets 409), or block succeeds first (and booking gets 409).
    # Never can BOTH succeed!
    statuses = [r[1] for r in race_results]
    assert 200 in statuses, f"Expected at least one operation to succeed, got {statuses}"
    assert 409 in statuses, f"Expected conflicting operation to receive 409 Conflict, got {statuses}"
    print(f"  ✓ Handled correctly: Operations resolved with statuses: {race_results}")

    passed_tests += 1
    print("✓ PASS: Schedule updates and bookings safely serialized by database transactions.")

    # -------------------------------------------------------------------------
    # TEST 12: Cancellation & Completed Appointment Immutability
    # -------------------------------------------------------------------------
    print("\n--- TEST 12: Cancellation & Completed Appointment Immutability ---")
    # Book a test appointment to finalize as completed
    comp_date = get_future_working_date(0)
    comp_time = "12:00 PM"
    st, comp_app = api_call("POST", "/opd", {
        "patient_id": p1_id,
        "hospital_id": "hosp-1",
        "doctor_id": d1_doc_id,
        "department": "Cardiology",
        "appointment_date": comp_date,
        "appointment_time": comp_time
    }, token=p1_token)
    assert st == 200, f"Booking appointment failed: {comp_app}"
    comp_app_id = comp_app["id"]

    # Finalize consultation to mark appointment as COMPLETED
    st, cons_res = api_call("POST", "/consultations", {
        "appointment_id": comp_app_id,
        "patient_id": p1_id,
        "clinical_notes": "Routine scheduled cardiac evaluation completed.",
        "diagnosis": "Normal Sinus Rhythm",
        "treatment_plan": "Routine follow-up in 6 months."
    }, token=d1_token)
    assert st == 200, f"Finalizing consultation failed: {cons_res}"

    # Attempt to cancel a COMPLETED appointment -> Must be rejected with 400
    st, cancel_err = api_call("PUT", f"/opd/{comp_app_id}/cancel", token=p1_token)
    assert st == 400, f"Expected 400 when cancelling completed appointment, got {st}: {cancel_err}"
    print("  ✓ Completed appointment cannot be cancelled (HTTP 400)")

    # Attempt to reschedule a COMPLETED appointment -> Must be rejected with 400
    st, resched_comp_err = api_call("PUT", f"/opd/{comp_app_id}/reschedule", {
        "appointment_date": comp_date,
        "appointment_time": "11:30 AM"
    }, token=p1_token)
    assert st == 400, f"Expected 400 when rescheduling completed appointment, got {st}: {resched_comp_err}"
    print("  ✓ Completed appointment cannot be rescheduled (HTTP 400)")

    passed_tests += 1
    print("✓ PASS: Completed appointments remain immutable historical records.")

    print("\n=========================================================================")
    print(f"RESULTS: {passed_tests}/{total_tests} Phase 4.4 Doctor Scheduling Tests Passed Successfully.")
    print("=========================================================================")

if __name__ == "__main__":
    main()
