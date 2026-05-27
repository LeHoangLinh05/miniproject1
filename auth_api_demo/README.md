# FastAPI Auth & Activity Tracking API (Week 1 Mini Project)

This project implements a secure Web API featuring JWT Authentication (with token rotation), user registration/login, SQLite storage, structured logging, and an online/offline status tracking mechanism using Redis (with automatic in-memory MockRedis fallback).

---

## Features

1. **JWT Auth & Security**:
   - Short-lived Access Tokens (15 minutes).
   - Long-lived Refresh Tokens (7 days).
   - Password hashing using `bcrypt` (secure, modern hash algorithm).
   - **Refresh Token Rotation (RTR)**: Refreshing an access token invalidates (blacklists) the old refresh token and returns a new access/refresh pair to prevent reuse attacks.
2. **Session / Blacklist Manager (Redis & MockRedis)**:
   - Tracks blacklisted refresh tokens to handle logouts and token rotation.
   - Automatically attempts to connect to local Redis (`127.0.0.1:6379`).
   - If Redis is unavailable, it **gracefully falls back to a thread-safe, in-memory Cache (MockRedis)**. No extra setup is required to run the project.
3. **Creative Feature: Online / Offline Status Tracking**:
   - An authenticated request updates the user's activity timestamp in the cache.
   - An endpoint `/users/{user_id}/status` retrieves a user's status: whether they are `online` (active within the last 2 minutes) or how many minutes ago they were active (`offline_minutes`).
   - User lists and profiles also report this status.
4. **Structured Logging & REST Exception Format**:
   - Standardized request/response logging written to both the terminal and `app.log`.
   - Customized error handlers format standard FastAPI validation errors and HTTP exceptions into a clean REST format.

---

## Folder Structure

```
auth_api_demo/
│── main.py              # Entrypoint, DB creation, exception handling, and middlewares
│── database.py          # SQLite connection and DB session dependency
│── redis_client.py      # Redis/MockRedis client for session/blacklist management
│── dependencies.py      # Authentication/authorization guards & user status update triggers
│── requirements.txt     # Python package requirements
│── routers/
│   ├── __init__.py
│   ├── auth.py          # /register, /login, /token/refresh, /logout
│   └── users.py         # /users/me, /users/all, /users/{id}/status
│── schemas/
│   ├── __init__.py
│   ├── user_schema.py   # Pydantic schemas for user profile responses and status
│   └── token_schema.py  # Pydantic schemas for tokens and login/refresh payloads
│── utils/
│   ├── __init__.py
│   ├── jwt_handler.py   # JWT token generation and validation
│   └── password_hash.py # Bcrypt password hashing
│── models/
│   ├── __init__.py
│   └── user_model.py    # SQLAlchemy database models for users
```

---

## Installation & Setup

1. **Navigate to the workspace root**:
   Make sure you are in the parent directory (`d:\miniproject1`).

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv .venv
   ```
   Activate the virtual environment:
   - On Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - On Linux/macOS: `source .venv/bin/activate`

3. **Install Dependencies**:
   ```bash
   pip install -r auth_api_demo/requirements.txt
   ```

4. **Start the API Server**:
   From the parent directory (`d:\miniproject1`), run:
   ```bash
   uvicorn auth_api_demo.main:app --reload
   ```
   *Note: If running directly inside the `auth_api_demo` directory, run: `uvicorn main:app --reload` instead.*

5. **Access API Documentation**:
   Open your browser to: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI) or [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) (ReDoc).

---

## API Documentation Summary

| Endpoint | Method | Description | Auth Required |
|---|---|---|---|
| `/ping` | GET | Verification endpoint. Returns `"pong"`. | ✗ |
| `/register` | POST | Register new account (params: `email`, `password`, `role`). | ✗ |
| `/login` | POST | Login and receive `access_token` & `refresh_token`. | ✗ |
| `/token/refresh`| POST | Rotate and issue a new `access_token` & `refresh_token`. | ✗ |
| `/logout` | POST | Logout a user. Blacklists their refresh token. | ✓ |
| `/users/me` | GET | Retrieve logged-in user profile with online status. | ✓ |
| `/users/all` | GET | Retrieve list of all users and status (**Admin Only**). | ✓ (Admin) |
| `/users/{id}/status`| GET| Retrieve detailed online/offline status of a user. | ✓ |

---

## Testing with PowerShell

Here are commands to test the API directly using PowerShell.

### 1. Ping Check
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/ping" -Method Get
```

### 2. Register Users
Register an **Admin User**:
```powershell
$adminBody = @{
    email = "admin@example.com"
    password = "adminpassword"
    role = "admin"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/register" -Method Post -Body $adminBody -ContentType "application/json"
```

Register a **Regular User**:
```powershell
$userBody = @{
    email = "user@example.com"
    password = "userpassword"
    role = "user"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/register" -Method Post -Body $userBody -ContentType "application/json"
```

### 3. Log In (Get Tokens)
Log in as the standard user to get JWT tokens:
```powershell
$loginBody = @{
    email = "user@example.com"
    password = "userpassword"
} | ConvertTo-Json

$tokens = Invoke-RestMethod -Uri "http://127.0.0.1:8000/login" -Method Post -Body $loginBody -ContentType "application/json"
$tokens | Format-List
```
This stores the access token in `$tokens.access_token` and the refresh token in `$tokens.refresh_token`.

### 4. Fetch Current User Profile
```powershell
$headers = @{ Authorization = "Bearer $($tokens.access_token)" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/users/me" -Method Get -Headers $headers
```

### 5. Check User Status (Creative Feature)
Wait a few seconds, then check the user's status details:
```powershell
# Check user 2 status (standard user)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/users/2/status" -Method Get -Headers $headers
```

### 6. Admin User List (Should fail for standard user, succeed for admin)
Try checking with the standard user token (should return `403 Forbidden`):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/users/all" -Method Get -Headers $headers
```

Log in as the admin:
```powershell
$adminLoginBody = @{
    email = "admin@example.com"
    password = "adminpassword"
} | ConvertTo-Json

$adminTokens = Invoke-RestMethod -Uri "http://127.0.0.1:8000/login" -Method Post -Body $adminLoginBody -ContentType "application/json"
$adminHeaders = @{ Authorization = "Bearer $($adminTokens.access_token)" }

# Retrieve user list with statuses
Invoke-RestMethod -Uri "http://127.0.0.1:8000/users/all" -Method Get -Headers $adminHeaders | ConvertTo-Json
```

### 7. Refresh Access Token (Token Rotation)
```powershell
$refreshBody = @{
    refresh_token = $tokens.refresh_token
} | ConvertTo-Json

$newTokens = Invoke-RestMethod -Uri "http://127.0.0.1:8000/token/refresh" -Method Post -Body $refreshBody -ContentType "application/json"
$newTokens | Format-List
```

### 8. Log Out (Blacklist Token)
Log out using the new refresh token:
```powershell
$logoutBody = @{
    refresh_token = $newTokens.refresh_token
} | ConvertTo-Json

$logoutHeaders = @{ Authorization = "Bearer $($newTokens.access_token)" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/logout" -Method Post -Body $logoutBody -ContentType "application/json" -Headers $logoutHeaders
```

Try using the logged-out refresh token again (should return `401 Unauthorized` due to blacklisting):
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/token/refresh" -Method Post -Body $logoutBody -ContentType "application/json"
```
