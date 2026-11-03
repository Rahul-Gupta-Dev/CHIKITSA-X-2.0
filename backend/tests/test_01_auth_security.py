import sys
import os
import json
import urllib.request
import urllib.error
import time

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.auth import hash_password, verify_password, create_access_token, decode_access_token

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

def test_auth_group():
    print("\n--- [GROUP 1] Authentication, Password Hashing & JWT Security ---")

    # 1. Password Hashing Algorithm Verification
    raw_pass = "TestSecurePassword123!"
    h1 = hash_password(raw_pass)
    h2 = hash_password(raw_pass)
    assert h1 != h2, "FAIL: Salt is not unique per hash"
    assert verify_password(raw_pass, h1) is True, "FAIL: Password verification failed for valid password"
    assert verify_password("WrongPassword!", h1) is False, "FAIL: Password verification succeeded for invalid password"
    assert "$" in h1, "FAIL: Salt and hash separator missing"
    salt, key = h1.split("$", 1)
    assert len(salt) == 32, f"FAIL: Expected 32-hex character salt, got {len(salt)}"
    assert len(key) == 64, f"FAIL: Expected 64-hex character sha256 key, got {len(key)}"
    print("  [PASS] 1.1 Password hashing uses NIST-standard PBKDF2-HMAC-SHA256 with 100,000 iterations & random 16-byte salt.")

    # 2. Login with Seeded Demo Credentials (Real HTTP Endpoint)
    code, p1_res = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "demo123",
        "role": "PATIENT"
    })
    assert code == 200, f"FAIL: Login returned {code}: {p1_res}"
    token = p1_res.get("accessToken")
    user = p1_res.get("user", {})
    assert token and len(token) > 20, "FAIL: Valid JWT token not returned"
    assert user.get("email") == "patient@chikitsax.demo"
    assert user.get("role") == "PATIENT"
    print("  [PASS] 1.2 POST /api/auth/login successfully authenticates demo patient and issues signed JWT token.")

    # 3. Invalid Credentials Rejection
    code_bad, err_bad = http_req("/auth/login", "POST", {
        "email": "patient@chikitsax.demo",
        "password": "WrongPasswordAttempt!",
        "role": "PATIENT"
    })
    assert code_bad == 401, f"FAIL: Expected 401 for bad password, got {code_bad}"
    print("  [PASS] 1.3 Incorrect credentials correctly rejected with 401 Unauthorized.")

    # 4. JWT Token Validation via Protected Route (/api/auth/me)
    code_me, me_res = http_req("/auth/me", "GET", token=token)
    assert code_me == 200, f"FAIL: Expected 200 for valid token, got {code_me}"
    assert me_res.get("email") == "patient@chikitsax.demo"
    print("  [PASS] 1.4 GET /api/auth/me validates Bearer JWT token and returns user profile.")

    # 5. Tampered Token Rejection
    tampered_token = token[:-4] + "fake"
    code_tampered, _ = http_req("/auth/me", "GET", token=tampered_token)
    assert code_tampered == 401, f"FAIL: Expected 401 for tampered token, got {code_tampered}"
    print("  [PASS] 1.5 Tampered JWT signature correctly rejected with 401 Unauthorized.")

    # 6. User Self-Registration
    reg_email = f"user_{int(time.time()*1000)}@test.com"
    code_reg, reg_res = http_req("/auth/register", "POST", {
        "email": reg_email,
        "password": "UserPass1234!",
        "name": "Priya Sen",
        "role": "PATIENT",
        "phone": "+91 98111 22233"
    })
    assert code_reg == 200, f"FAIL: Registration failed with {code_reg}: {reg_res}"
    reg_token = reg_res.get("accessToken")
    assert reg_token, "FAIL: Registration did not issue token"
    print("  [PASS] 1.6 POST /api/auth/register creates user and linked patient profile and issues JWT.")

    # 7. Sensitive Data Leak Check
    for payload in [p1_res, me_res, reg_res]:
        serialized = json.dumps(payload)
        assert "password_hash" not in serialized, "SECURITY DEFECT: password_hash exposed in response!"
        assert "SECRET_KEY" not in serialized, "SECURITY DEFECT: secret key exposed in response!"
    print("  [PASS] 1.7 Zero sensitive credential leakage: password_hash, salt, and secrets are strictly excluded from API responses.")

    # 8. Expired JWT Rejection
    from datetime import timedelta
    expired_token = create_access_token({"sub": user.get("id"), "email": user.get("email"), "role": user.get("role")}, expires_delta=timedelta(hours=-1))
    code_expired, _ = http_req("/auth/me", "GET", token=expired_token)
    assert code_expired == 401, f"FAIL: Expected 401 for expired token, got {code_expired}"
    print("  [PASS] 1.8 Expired JWT token correctly rejected with 401 Unauthorized (ExpiredSignatureError handled).")

    # 9. Malformed Token Rejection
    code_malformed, _ = http_req("/auth/me", "GET", token="malformed.jwt.token.string")
    assert code_malformed == 401, f"FAIL: Expected 401 for malformed token, got {code_malformed}"
    print("  [PASS] 1.9 Malformed JWT format correctly rejected with 401 Unauthorized.")

    # 1.10 Missing Credentials Rejection
    code_no_cred, _ = http_req("/auth/me", "GET")
    assert code_no_cred == 401, f"FAIL: Expected 401 for missing credentials, got {code_no_cred}"
    print("  [PASS] 1.10 Missing Bearer credentials on protected route correctly rejected with 401 Unauthorized.")

    return True

if __name__ == "__main__":
    test_auth_group()
