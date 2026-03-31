FROM nginxinc/nginx-unprivileged:1.25-alpine

COPY html/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
