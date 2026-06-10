# Mini Project 1 — Auth API + Next.js (Docker)

## Demo online

**Production:** https://15.135.194.148/

- Frontend: `https://15.135.194.148/`
- API (qua Nginx): `https://15.135.194.148/api/ping` → `pong`
- Swagger (trực tiếp backend, chỉ khi expose port 8000): `/docs`

---

## Kiến trúc

```text
Browser
   │
   ▼
Nginx (:80 → redirect HTTPS, :443)
   ├── /api/*  →  backend:8000  (FastAPI, prefix /api)
   └── /*      →  frontend:3000 (Next.js standalone)
                        │
                        ▼
                   postgres:5432
```

| Môi trường | Compose file | Mô tả |
|------------|--------------|-------|
| Development | `docker-compose.yaml` | Hot reload, expose port 8080 (FE) và 8000 (BE) |
| Production | `docker-compose.prod.yaml` | Image từ Docker Hub, chỉ expose 80/443 qua Nginx |

---

## Database migrations (Alembic)

Schema được quản lý bằng Alembic — **không** dùng `create_all()` khi app boot.

```bash
cd backend

# Tạo migration mới sau khi đổi model
alembic revision --autogenerate -m "describe change"
alembic upgrade head

# Xem lịch sử / rollback 1 bước
alembic history
alembic downgrade -1
```

Container backend tự chạy `alembic upgrade head` qua `entrypoint.sh` trước Gunicorn/Uvicorn.

**EC2 đã có bảng `users` từ lần deploy cũ** (chưa có `alembic_version`):

```bash
docker exec -it miniproject1-backend alembic stamp head
```

---

## Chạy local (Development)

### Yêu cầu

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (đã bật)
- Git

### 1. Clone & cấu hình `.env`

```bash
git clone <repo-url> miniproject1
cd miniproject1

# Backend — copy và chỉnh nếu cần
cp backend/.env.example backend/.env

# Frontend — dùng URL nội bộ Docker network
cp frontend/.env.example frontend/.env
```

Nội dung quan trọng trong `backend/.env`:

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/auth_demo
POSTGRES_DB=auth_demo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
JWT_SECRET=change-me-to-a-long-random-secret-key
REDIS_URL=          # để trống nếu chưa có Redis; hoặc điền Upstash URL
```

Nội dung `frontend/.env` khi chạy Docker Compose:

```env
NEXT_PUBLIC_API_URL=http://backend:8000
```

> `backend` và `postgres` là **tên service** trong Docker network — không đổi thành `localhost` khi chạy full stack bằng Compose.

### 2. Khởi động stack dev (Docker Compose)

```bash
# Từ thư mục gốc miniproject1/
docker compose up --build
```

Lần đầu chạy, container `backend` sẽ tự:

1. Chạy `alembic upgrade head` (tạo bảng `users`)
2. Start Uvicorn với `--reload` (sửa code backend → tự reload)

| Service | Container | Port host | Mô tả |
|---------|-----------|-----------|-------|
| Frontend | `miniproject1-frontend` | **8080** | Next.js dev server, hot reload |
| Backend | `miniproject1-backend` | **8000** | FastAPI + Uvicorn, hot reload |
| PostgreSQL | `miniproject1-postgres` | *(nội bộ)* | Data lưu tại `./data/postgres` |
| Nginx | `miniproject1-nginx` | **80**, **443** | Reverse proxy giống production |

Chạy nền (detached):

```bash
docker compose up --build -d
```

Dừng stack:

```bash
docker compose down
```

Xóa cả volume DB (reset data):

```bash
docker compose down -v
rm -rf data/postgres   # Linux/macOS
# Windows PowerShell: Remove-Item -Recurse -Force data\postgres
```

### 3. Truy cập & kiểm tra

| Mục đích | URL |
|----------|-----|
| Frontend (trực tiếp) | http://localhost:8080 |
| API health check | http://localhost:8000/api/ping → `pong` |
| Swagger UI | http://localhost:8000/docs |
| Qua Nginx (giống prod) | https://localhost/api/ping *(self-signed cert, browser có thể cảnh báo)* |
| Frontend qua Nginx | https://localhost/ |

PowerShell test nhanh:

```powershell
Invoke-RestMethod http://localhost:8000/api/ping
```

```bash
# Git Bash / WSL / macOS / Linux
curl http://localhost:8000/api/ping
```

### 4. Lệnh hữu ích khi dev

```bash
# Xem log từng service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres

# Rebuild chỉ backend sau khi đổi requirements.txt
docker compose up --build backend -d

# Chạy migration thủ công (trong container)
docker exec miniproject1-backend alembic upgrade head

# Vào shell container backend
docker exec -it miniproject1-backend sh

# Kiểm tra Postgres
docker exec -it miniproject1-postgres psql -U postgres -d auth_demo -c "\dt"
```

### 5. Chạy dev không dùng Docker (tùy chọn)

Dùng khi muốn debug nhanh từng phần trên máy, không qua container.

**Yêu cầu thêm:** Python 3.11+, Node.js 20+

#### Backend + Postgres (Docker) + Frontend (npm)

```bash
# Terminal 1 — chỉ chạy Postgres
docker compose up postgres -d

# Terminal 2 — backend trên host
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r auth_api_demo/requirements.txt

# .env dùng localhost thay vì tên container
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/auth_demo
# (cần expose port 5432 — thêm ports: "5432:5432" vào service postgres tạm thời,
#  hoặc dùng SQLite: DATABASE_URL=sqlite:///./auth_demo.db)

alembic upgrade head
uvicorn auth_api_demo.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Terminal 3 — frontend trên host
cd frontend
npm install

# frontend/.env
# NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

npm run dev
# → http://localhost:3000
```

| Chế độ | FE URL | BE URL | Ghi chú |
|--------|--------|--------|---------|
| Docker Compose (khuyến nghị) | :8080 | :8000/api/* | Giống prod, có Nginx |
| Host native | :3000 | :8000/api/* | Nhanh hơn khi chỉ sửa FE/BE |

### 6. Lỗi thường gặp (dev)

| Triệu chứng | Nguyên nhân | Cách xử lý |
|-------------|-------------|------------|
| `502` qua Nginx | Backend chưa sẵn sàng | `docker compose logs backend`, đợi migration xong |
| FE không gọi được API | Sai `NEXT_PUBLIC_API_URL` | Docker: `http://backend:8000` — Host: `http://127.0.0.1:8000` |
| `connection refused` Postgres | Postgres chưa healthy | `docker compose ps`, đợi healthcheck xanh |
| Port 80/443 bị chiếm | Service khác trên máy | Tắt IIS/Skype hoặc đổi port trong `docker-compose.yaml` |
| Migration lỗi duplicate table | DB cũ còn schema | `docker compose down`, xóa `data/postgres`, `up` lại |

---

## Triển khai Production (AWS EC2)

Server demo: **15.135.194.148** (AWS EC2).

### 1. Build và push image lên Docker Hub

```bash
# Backend
docker build -f backend/Dockerfile.prod -t lehoanglinh05/miniproject1-app-backend:latest ./backend
docker push lehoanglinh05/miniproject1-app-backend:latest

# Frontend
docker build -f frontend/Dockerfile.prod -t lehoanglinh05/miniproject1-app-frontend:latest ./frontend
docker push lehoanglinh05/miniproject1-app-frontend:latest

# Nginx (sau khi sửa nginx.conf)
docker build -t lehoanglinh05/miniproject1-app-nginxproxy:latest ./nginx
docker push lehoanglinh05/miniproject1-app-nginxproxy:latest
```

### 2. Trên EC2

```bash
git clone <repo-url> miniproject1 && cd miniproject1
cp backend/.env.example backend/.env   # điền secret thật
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
```

### 3. Mở Security Group

- Inbound: TCP **80**, **443** từ `0.0.0.0/0`

### 4. Kiểm tra

```bash
curl -k https://15.135.194.148/api/ping
# pong
```

> **Lưu ý:** Sau khi sửa code, cần **rebuild + push** image backend (Alembic + bind `0.0.0.0`) rồi deploy lại trên EC2:

```bash
# Local
docker build -f backend/Dockerfile.prod -t lehoanglinh05/miniproject1-app-backend:latest ./backend
docker push lehoanglinh05/miniproject1-app-backend:latest

# EC2 — DB đã có bảng users từ deploy cũ, chạy stamp một lần:
docker compose -f docker-compose.prod.yaml pull
docker compose -f docker-compose.prod.yaml up -d
docker exec miniproject1-backend alembic stamp head   # chỉ lần đầu sau khi chuyển sang Alembic

curl -k https://15.135.194.148/api/ping   # → pong
```

---

## Backup & Restore PostgreSQL

### Backup

```bash
# Development (container tên miniproject1-postgres)
docker exec miniproject1-postgres pg_dump -U postgres auth_demo > backup_$(date +%Y%m%d).sql

# Production
docker exec miniproject1-postgres pg_dump -U postgres auth_demo > backup_prod.sql
```

### Restore

```bash
# Dừng backend trước để tránh ghi đè
docker compose stop backend

cat backup_20260101.sql | docker exec -i miniproject1-postgres psql -U postgres -d auth_demo

docker compose start backend
```

### Backup volume (toàn bộ data directory)

```bash
docker run --rm \
  -v miniproject1_postgres-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres-volume.tar.gz -C /data .
```

---

## API routes (prefix `/api`)

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/ping` | GET | Health check |
| `/api/register` | POST | Đăng ký |
| `/api/login` | POST | Đăng nhập |
| `/api/token/refresh` | POST | Refresh token |
| `/api/logout` | POST | Đăng xuất |
| `/api/users/me` | GET | Profile hiện tại |
| `/api/users/all` | GET | Danh sách user (admin) |

Chi tiết backend: [backend/auth_api_demo/README.md](backend/auth_api_demo/README.md)

---

## Cấu trúc thư mục

```text
miniproject1/
├── backend/           # FastAPI + Dockerfile.dev/prod
├── frontend/          # Next.js 16 + Dockerfile.dev/prod
├── nginx/             # Reverse proxy + self-signed SSL
├── docker-compose.yaml       # Dev
└── docker-compose.prod.yaml  # Production (Docker Hub)
```
