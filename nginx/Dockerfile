FROM nginx:alpine

# Cài đặt openssl để sinh self-signed SSL certificate
RUN apk add --no-cache openssl

# Tạo thư mục chứa certificates
RUN mkdir -p /etc/nginx/ssl

# Copy file cấu hình và entrypoint
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh

# Cấp quyền thực thi cho entrypoint
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
