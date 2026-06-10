# DEVOPS & DOCKER

## Buổi 1: Tổng quan Docker & Containerization

### Nội dung chi tiết

* Giới thiệu Docker, Image, Container, Volume, Network
* Phân biệt giữa Dockerfile & docker-compose
* Cấu trúc thư mục dự án FE, BE, DB
* Tạo Dockerfile đầu tiên cho Python FastAPI

### Công cụ / Kỹ thuật

* Docker
* Docker CLI
* FastAPI

---

## Buổi 2: Docker Backend (FastAPI)

### Nội dung chi tiết

* Viết Dockerfile.dev và Dockerfile.prod cho Backend
* Cài đặt uvicorn, gunicorn worker
* Mount volume để auto reload trong dev mode
* Dùng .env để config DB_URI, SECRET_KEY

### Công cụ / Kỹ thuật

* FastAPI
* Uvicorn
* Gunicorn
* python-dotenv

---

## Buổi 3: Docker Frontend (Next.js)

### Nội dung chi tiết

* Viết Dockerfile.dev và Dockerfile.prod cho Next.js 15
* Chạy frontend trong container
* Kết nối frontend container với backend container qua network
* Build production bằng next build

### Công cụ / Kỹ thuật

* Next.js 15
* Node.js
* Docker Compose

---

## Buổi 4: Docker Database Services

### Nội dung chi tiết

* Viết Docker Compose cho MySQL, MongoDB, Redis
* Cấu hình volume lưu trữ dữ liệu persist
* Kiểm tra kết nối từ Backend (DB_URL, Redis Cache)
* Backup & restore data container

### Công cụ / Kỹ thuật

* MySQL
* MongoDB
* Redis
* Docker Compose

---

## Buổi 5: Nginx Reverse Proxy

### Nội dung chi tiết

* Cấu hình Nginx làm reverse proxy
* Tạo file nginx.conf để route api/ → backend, / → frontend
* Mapping port 80 và 443
* Hiểu cơ chế proxy_pass, upstream

### Công cụ / Kỹ thuật

* Nginx
* Reverse Proxy

---

## Buổi 6: Triển khai Production (Render / Railway / AWS EC2)

### Nội dung chi tiết

* Giới thiệu Render, Railway, EC2, và Docker Hub
* Push image lên Docker Hub
* Deploy toàn bộ stack bằng docker-compose
* Mô hình triển khai thực tế (FE + BE + DB + Proxy)

### Công cụ / Kỹ thuật

* Docker Hub
* Render
* Railway
* AWS EC2

---

## Buổi 7: Giám sát & Logging

### Nội dung chi tiết

* Dùng docker ps, docker logs, docker exec
* Kiểm tra healthcheck các container
* Ghi log access / error từ Nginx và Gunicorn
* Xử lý lỗi mạng / CORS khi proxy

### Công cụ / Kỹ thuật

* Docker CLI
* Log File
* Nginx
* Gunicorn

---

## Buổi 8: Tổng hợp & Bảo vệ mini project

### Nội dung chi tiết

* Chạy toàn bộ hệ thống qua 1 lệnh docker-compose up
* FE + BE + DB hoạt động đồng bộ
* Bảo vệ bài làm, giải thích cấu trúc file và flow build
* Đánh giá performance, tối ưu image

### Công cụ / Kỹ thuật

* Docker Compose
* CI/CD Basic

---

# Tiêu chí đánh giá

| Nhóm tiêu chí                                      | Nội dung đánh giá cụ thể                                                                                                      | Điểm tối đa | Mức đạt yêu cầu                      |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------ |
| Docker Backend (FastAPI)                           | Tạo được Dockerfile.dev & Dockerfile.prod<br>App FastAPI chạy ổn trong container<br>Config .env kết nối DB                    | 15          | API hoạt động trong container        |
| Docker Frontend (Next.js)                          | Dockerfile cho FE chạy được SSR/CSR<br>Build được image production (next build)<br>FE gọi được API backend qua network nội bộ | 15          | FE hiển thị đúng dữ liệu             |
| Docker Compose tổng thể                            | Viết file docker-compose.yml gồm FE, BE, DB<br>Network nội bộ kết nối đúng<br>Chạy được toàn bộ stack bằng docker-compose up  | 20          | FE + BE + DB đồng bộ                 |
| Docker Database Services                           | MySQL, MongoDB, Redis hoạt động ổn định<br>Có volume lưu data<br>BE kết nối DB được qua container name                        | 15          | Các DB hoạt động và lưu dữ liệu      |
| Nginx Reverse Proxy                                | Nginx route chuẩn /api và /<br>Config reverse proxy chính xác<br>Kiểm tra truy cập FE/BE qua 1 port duy nhất                  | 15          | Proxy hoạt động ổn, truy cập ổn định |
| Triển khai Production                              | Push image lên Docker Hub<br>Deploy lên Render / Railway / EC2<br>Có domain hoặc public link demo                             | 10          | Có thể truy cập demo online          |
| Bảo vệ bài làm & hiểu kiến trúc                    | Giải thích rõ pipeline build FE → BE → DB<br>Biết so sánh Dev vs Prod environment<br>Trình bày logic network, proxy, env      | 10          | Trình bày mạch lạc, hiểu tổng quan   |
| Tối ưu Dockerfile (multi-stage build, small image) | Dung lượng image nhỏ hơn 400MB                                                                                                | 3           |                                      |
| Sử dụng .env an toàn, không commit vào Git         | Quản lý bí mật đúng chuẩn                                                                                                     | 2           |                                      |
| Triển khai HTTPS với Nginx                         | Có SSL/TLS thật                                                                                                               | 3           |                                      |

---

# Bài tập tuần (DevOps & Docker)

Bài tập tuần (DevOps & Docker) sẽ giúp học viên thực hành triển khai thực tế toàn bộ hệ thống FE + BE + DB trong môi trường container.

**Yêu cầu:**

* Config toàn bộ Docker Development
* Config Docker Build cho source
