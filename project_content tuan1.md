# Lộ Trình Đào Tạo Python + NextJS + AI Agent — Tuần 1

## MÔI TRƯỜNG & KIẾN TRÚC WEB (BACKEND PYTHON)

---

## Lịch Học Chi Tiết

| Buổi | Chủ đề | Nội dung chi tiết | Công cụ / Kỹ thuật | Tài Liệu Tham Khảo |
|------|--------|-------------------|-------------------|-------------------|
| 1 | Tổng quan Web & Môi trường phát triển | - Giới thiệu mô hình Web (Client – Server – Database)<br>- HTTP protocol, REST vs RPC<br>- Setup Python 3.12, Node.js 20+, VSCode, Postman<br>- Giới thiệu Docker và Git | Python, Docker, Git, Postman | https://fastapi.tiangolo.com/ |
| 2 | FastAPI căn bản | - Tạo dự án FastAPI<br>- Route, path parameter, query parameter<br>- Response JSON, status code, dependency injection | FastAPI, Uvicorn | https://docs.pydantic.dev/latest/ |
| 3 | Xử lý dữ liệu và cấu trúc project | - Request body (Pydantic model)<br>- Response model<br>- Folder structure: main.py, routers, schemas, models | Pydantic, FastAPI project layout | https://www.jwt.io/introduction |
| 4 | Authentication với JWT | - JSON Web Token là gì?<br>- Access token & refresh token<br>- Login/Signup API<br>- Bảo vệ route bằng JWT middleware | pyjwt, FastAPI Security ⇒ Tự build | https://docs.python.org/3/library/logging.html |
| 5 | Logging & Error Handling | - Logging cơ bản<br>- Xử lý exception (HTTPException, custom handler)<br>- Response chuẩn REST | Python logging, FastAPI exception | — |
| Cuối tuần | Ôn tập & bài tập thực hành | Tổng kết + review project mini | Git commit & push lên GitHub | — |

---

## Cấu Trúc Folder Dự Án

```
auth_api_demo/
│── main.py
│── routers/
│   ├── auth.py
│   └── users.py
│── schemas/
│   ├── user_schema.py
│   └── token_schema.py
│── utils/
│   ├── jwt_handler.py
│   └── password_hash.py
│── models/
│   └── user_model.py
│── requirements.txt
```

---

## Danh Sách API Tối Thiểu

| Endpoint | Method | Mô tả | Auth yêu cầu | Ghi chú kỹ thuật |
|----------|--------|-------|:------------:|------------------|
| `/ping` | GET | Kiểm tra server hoạt động | ✗ | Trả về "pong" – kiểm tra môi trường |
| `/register` | POST | Đăng ký tài khoản mới | ✗ | Lưu thông tin user (email, password) – password được hash |
| `/login` | POST | Đăng nhập, trả về access_token và refresh_token | ✗ | Kiểm tra user, sinh JWT 2 tầng (access + refresh) |
| `/token/refresh` | POST | Cấp lại access_token mới từ refresh_token | ✗ | Validate refresh_token → sinh access_token mới |
| `/users/me` | GET | Lấy thông tin người dùng hiện tại | ✓ | Dùng access_token xác thực |
| `/users/all` | GET | Lấy danh sách user (chỉ admin) | ✓ | Dùng access_token, kiểm tra role |
| `/logout` | POST | Đăng xuất (vô hiệu hóa token) | ✓ | Có thể thêm blacklist token hoặc xóa refresh token (nếu có Redis ở tuần sau) |

---

## Tiêu Chí Chấm Điểm

| Tiêu chí | Trọng số |
|----------|:--------:|
| API hoạt động đúng (CRUD + Auth + refresh token) | 30% |
| Cấu trúc code rõ ràng, tách module | 25% |
| JWT đúng quy trình (access/refresh, expiry) | 25% |
| Có log + xử lý lỗi chuẩn REST | 10% |
| Push lên GitHub + README rõ ràng | 5% |
| Thêm API + Công nghệ mới + Sáng tạo | 5% |

---

## Bài Tập Tuần (Mini Project)

Xây dựng một ứng dụng Web API có cơ chế Auth sử dụng JWT.

**Yêu cầu:**
- Khuyến khích tự viết
- Sử dụng thêm Redis
- Thêm các tính năng sáng tạo khác như check được user đó offline bao nhiêu phút trước hoặc đang online hay không
- Thêm cả DB vào như MySQL vào càng tốt, nếu không chỉ cần tạo const user login là được
- Yêu cầu cần viết tối thiểu các API được liệt kê ở trên
