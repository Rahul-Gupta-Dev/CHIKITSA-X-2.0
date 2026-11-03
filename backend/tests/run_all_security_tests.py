import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from test_01_auth_security import test_auth_group
from test_02_idor_and_rbac import test_idor_and_rbac_group
from test_03_consent_and_medical_records import test_consent_and_records_group
from test_04_concurrency_and_slot_conflicts import test_concurrency_group
from test_05_qr_and_hospital_security import test_qr_security_group
from test_06_persistence_and_cors import test_persistence_and_cors_group
from test_07_staging_and_rate_limiting import test_staging_and_production_readiness_group

def main():
    print("================================================================================")
    print("CHIKITSA-X Complete Post-Integration Security, RBAC & Persistence Test Runner")
    print("================================================================================")

    suites = [
        ("Group 1: Authentication, Password Hashing & JWT Security", test_auth_group),
        ("Group 2: IDOR Vulnerabilities & Role-Based Authorization", test_idor_and_rbac_group),
        ("Group 3: Consent Lifecycle, Records Access & Document Storage", test_consent_and_records_group),
        ("Group 4: Concurrency, Slot Conflicts & Transaction Safety", test_concurrency_group),
        ("Group 5: QR Pass Verification, Replay & Hospital Scoping", test_qr_security_group),
        ("Group 6: Database Persistence on Disk & CORS / Sanitization", test_persistence_and_cors_group),
        ("Group 7: Staging Readiness, Fail-Safe Configuration & Rate Limiting", test_staging_and_production_readiness_group),
    ]

    results = []
    for name, suite_func in suites:
        try:
            passed = suite_func()
            results.append((name, "PASS", None))
        except AssertionError as e:
            results.append((name, "FAIL", str(e)))
            print(f"❌ {name} FAILED: {e}")
        except Exception as e:
            results.append((name, "BLOCKED / ERROR", str(e)))
            print(f"⚠️ {name} ENCOUNTERED ERROR: {e}")

    print("\n================================================================================")
    print("FINAL TEST RUNNER SUMMARY")
    print("================================================================================")
    passed_count = sum(1 for _, status, _ in results if status == "PASS")
    total_count = len(results)

    for name, status, err in results:
        status_icon = "✅" if status == "PASS" else "❌"
        err_msg = f" -> {err}" if err else ""
        print(f"{status_icon} [{status}] {name}{err_msg}")

    print(f"\nScore: {passed_count}/{total_count} Suites Passed ({(passed_count/total_count)*100:.1f}%)")
    print("================================================================================")
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
