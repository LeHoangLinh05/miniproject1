#!/bin/sh

# Tự động tạo SSL Certificate nếu chưa tồn tại
if [ ! -f /etc/nginx/ssl/nginx.crt ]; then
    echo "Creating self-signed SSL certificate..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/nginx.key \
        -out /etc/nginx/ssl/nginx.crt \
        -subj "/C=VN/ST=Hanoi/L=Hanoi/O=Development/OU=Dev/CN=localhost"
fi

# Chạy lệnh CMD mặc định của Nginx container
exec "$@"
