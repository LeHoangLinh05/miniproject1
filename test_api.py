import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

API_URL = "http://127.0.0.1:8000"


def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}

    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{API_URL}{url}", data=req_data, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            body = response.read().decode("utf-8")
            try:
                content = json.loads(body)
            except Exception:
                content = body
            return status_code, content
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read().decode("utf-8")
        try:
            content = json.loads(body)
        except Exception:
            content = body
        return status_code, content


def run_tests():
    print("=== STARTING API TESTS ===")

    # 1. Test Ping
    print("\n1. Testing GET /ping...")
    status, res = make_request("/ping", "GET")
    print(f"Status: {status} | Response: {res}")
    assert status == 200 and res == "pong", "Ping failed"
    print("-> Ping Succeeded!")

    # Database is deleted at the start of the script before the server runs

    # 2. Test Register Admin
    print("\n2. Testing POST /register (Admin)...")
    admin_payload = {
        "email": "admin@example.com",
        "password": "adminpassword",
        "role": "admin",
    }
    status, res = make_request("/register", "POST", data=admin_payload)
    print(f"Status: {status} | Response: {res}")
    assert status == 201, "Admin registration failed"
    print("-> Admin registration Succeeded!")

    # 3. Test Register Regular User
    print("\n3. Testing POST /register (User)...")
    user_payload = {
        "email": "user@example.com",
        "password": "userpassword",
        "role": "user",
    }
    status, res = make_request("/register", "POST", data=user_payload)
    print(f"Status: {status} | Response: {res}")
    assert status == 201, "User registration failed"
    user_id = res.get("id")
    print(f"-> User registration Succeeded! (User ID: {user_id})")

    # 4. Test Login
    print("\n4. Testing POST /login...")
    login_payload = {"email": "user@example.com", "password": "userpassword"}
    status, res = make_request("/login", "POST", data=login_payload)
    print(f"Status: {status} | Response keys: {list(res.keys())}")
    assert status == 200, "Login failed"

    access_token = res["access_token"]
    refresh_token = res["refresh_token"]
    print("-> Login Succeeded!")

    # Headers for authenticated requests
    user_headers = {"Authorization": f"Bearer {access_token}"}

    # 5. Test Get Profile /me
    print("\n5. Testing GET /users/me (Authenticated)...")
    status, res = make_request("/users/me", "GET", headers=user_headers)
    print(f"Status: {status} | Response: {json.dumps(res, indent=2)}")
    assert status == 200, "Profile fetch failed"
    assert res["is_online"] is True, "User should be online"
    print("-> Profile fetch Succeeded!")

    # 6. Test Get Activity Status
    print(f"\n6. Testing GET /users/{user_id}/status...")
    status, res = make_request(f"/users/{user_id}/status", "GET", headers=user_headers)
    print(f"Status: {status} | Response: {json.dumps(res, indent=2)}")
    assert status == 200, "Status query failed"
    assert res["is_online"] is True, "Status should show online"
    print("-> Activity status check Succeeded!")

    # 7. Test Admin Route Access as Regular User
    print("\n7. Testing GET /users/all as regular user (Should fail)...")
    status, res = make_request("/users/all", "GET", headers=user_headers)
    print(f"Status: {status} | Response: {res}")
    assert status == 403, "Access should be forbidden"
    print("-> Admin endpoint protection works (HTTP 403 Forbidden)!")

    # 8. Test Admin Login and Admin access
    print("\n8. Testing Admin Login...")
    admin_login_payload = {"email": "admin@example.com", "password": "adminpassword"}
    status, admin_res = make_request("/login", "POST", data=admin_login_payload)
    print(f"Status: {status}")
    assert status == 200, "Admin login failed"

    admin_headers = {"Authorization": f"Bearer {admin_res['access_token']}"}

    print("\n8b. Testing GET /users/all as admin (Should succeed)...")
    status, res = make_request("/users/all", "GET", headers=admin_headers)
    print(f"Status: {status} | Response: {json.dumps(res, indent=2)}")
    assert status == 200, "Admin list retrieval failed"
    assert len(res) >= 2, "Should return at least two users"
    print("-> Admin list retrieval Succeeded!")

    # 9. Test Token Refresh
    print("\n9. Testing POST /token/refresh...")
    refresh_payload = {"refresh_token": refresh_token}
    status, res = make_request("/token/refresh", "POST", data=refresh_payload)
    print(f"Status: {status} | Response keys: {list(res.keys())}")
    assert status == 200, "Token refresh failed"
    new_access_token = res["access_token"]
    new_refresh_token = res["refresh_token"]
    print("-> Token refresh/rotation Succeeded!")

    # Verify that the old refresh token is now blacklisted
    print("\n9b. Testing token rotation (using old refresh token)...")
    status, res = make_request("/token/refresh", "POST", data=refresh_payload)
    print(f"Status: {status} | Response: {res}")
    assert status == 401, "Old refresh token should be rejected"
    print("-> Old refresh token rejection verified (Token rotation works)!")

    # 10. Test Logout
    print("\n10. Testing POST /logout...")
    logout_payload = {"refresh_token": new_refresh_token}
    logout_headers = {"Authorization": f"Bearer {new_access_token}"}
    status, res = make_request(
        "/logout", "POST", data=logout_payload, headers=logout_headers
    )
    print(f"Status: {status} | Response: {res}")
    assert status == 200, "Logout failed"
    print("-> Logout Succeeded!")

    # 11. Test that logged out token cannot refresh
    print("\n11. Testing token refresh using logged-out token...")
    status, res = make_request("/token/refresh", "POST", data=logout_payload)
    print(f"Status: {status} | Response: {res}")
    assert status == 401, "Logged-out token should be rejected"
    print("-> Logged-out token rejection verified!")

    # 12. Check status after logout
    print("\n12. Testing user status after logout...")
    status, res = make_request(f"/users/{user_id}/status", "GET", headers=admin_headers)
    print(f"Status: {status} | Response: {json.dumps(res, indent=2)}")
    assert status == 200, "Status query failed"
    assert res["is_online"] is False, "Status should show offline after logout"
    print("-> Status shows offline after logout!")

    print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    # Delete existing SQLite database if it exists to start fresh (only if not already running)
    # Check if server is already running first
    server_already_running = False
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/ping", method="GET")
        with urllib.request.urlopen(req, timeout=1.0) as conn:
            if conn.read().decode("utf-8") == "pong":
                server_already_running = True
                print(
                    "Detected uvicorn server already running on port 8000. Running tests against it..."
                )
    except Exception:
        pass

    if not server_already_running and os.path.exists("auth_demo.db"):
        try:
            os.remove("auth_demo.db")
            print(
                "Removed existing test database 'auth_demo.db' before starting the server."
            )
        except Exception as e:
            print(f"Warning: Could not remove db file: {e}")

    if not server_already_running:
        print("Starting uvicorn server in background...")
        python_exe = "python"
        server_process = subprocess.Popen(
            [
                python_exe,
                "-m",
                "uvicorn",
                "auth_api_demo.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ]
        )

        # Wait for the server to start up by polling /ping
        server_ready = False
        print("Waiting for server to become responsive...")
        for _ in range(15):
            time.sleep(1.0)
            try:
                req = urllib.request.Request(f"{API_URL}/ping", method="GET")
                with urllib.request.urlopen(req, timeout=1.0) as conn:
                    if conn.read().decode("utf-8") == "pong":
                        server_ready = True
                        break
            except Exception:
                pass

        if not server_ready:
            print("Error: Uvicorn server failed to start within 15 seconds or crashed.")
            server_process.terminate()
            sys.exit(1)

        try:
            run_tests()
        finally:
            print("\nStopping uvicorn server...")
            server_process.terminate()
            server_process.wait()
            print("Server stopped.")
    else:
        run_tests()
