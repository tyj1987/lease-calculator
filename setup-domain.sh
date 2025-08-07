#!/bin/bash

# 融资租赁计算器 - 域名配置脚本
# 适配宝塔面板环境 - jsq.52trz.com

set -e

echo "================================="
echo "融资租赁计算器 - 域名配置"
echo "专用域名: jsq.52trz.com"
echo "================================="

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "请使用root用户运行此脚本: sudo ./setup-domain.sh"
   exit 1
fi

# 预设域名
DOMAIN_NAME="jsq.52trz.com"
NGINX_CONF_DIR="/www/server/nginx/conf"
SSL_CERT_DIR="/www/server/panel/vhost/cert/$DOMAIN_NAME"

echo "配置域名: $DOMAIN_NAME"
echo "Nginx配置目录: $NGINX_CONF_DIR"
echo "SSL证书目录: $SSL_CERT_DIR"

# 检查Nginx配置目录
if [ ! -d "$NGINX_CONF_DIR" ]; then
    echo "❌ 错误: Nginx配置目录不存在: $NGINX_CONF_DIR"
    echo "请确认您使用的是宝塔面板环境"
    exit 1
fi

# 创建SSL证书目录
mkdir -p "$SSL_CERT_DIR"

# 询问是否配置SSL
echo ""
echo "SSL证书配置选项："
echo "1) 使用已有SSL证书（推荐）"
echo "2) 使用 Let's Encrypt 免费SSL证书"
echo "3) 仅HTTP访问（不使用SSL）"
read -p "请选择 (1/2/3): " ssl_choice

# 备份原配置（如果存在）
CONF_FILE="$NGINX_CONF_DIR/$DOMAIN_NAME.conf"
if [ -f "$CONF_FILE" ]; then
    echo "备份原配置..."
    cp "$CONF_FILE" "$CONF_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

case $ssl_choice in
    1)
        echo "配置已有SSL证书..."
        echo ""
        echo "📋 证书文件放置说明："
        echo "请将您的SSL证书文件放置到以下目录："
        echo "证书目录: $SSL_CERT_DIR"
        echo ""
        echo "文件命名要求："
        echo "- 证书文件: $SSL_CERT_DIR/fullchain.pem"
        echo "- 私钥文件: $SSL_CERT_DIR/privkey.pem"
        echo ""
        echo "如果您的证书文件名不同，请重命名为上述文件名"
        echo ""
        
        read -p "证书文件是否已经放置完毕？(y/n): " cert_ready
        
        if [ "$cert_ready" != "y" ] && [ "$cert_ready" != "Y" ]; then
            echo "请先放置证书文件后再运行此脚本"
            exit 1
        fi
        
        # 验证证书文件
        if [ ! -f "$SSL_CERT_DIR/fullchain.pem" ] || [ ! -f "$SSL_CERT_DIR/privkey.pem" ]; then
            echo "❌ 错误: 证书文件不存在"
            echo "请确保以下文件存在："
            echo "- $SSL_CERT_DIR/fullchain.pem"
            echo "- $SSL_CERT_DIR/privkey.pem"
            exit 1
        fi
        
        # 设置证书文件权限
        chmod 644 "$SSL_CERT_DIR/fullchain.pem"
        chmod 600 "$SSL_CERT_DIR/privkey.pem"
        
        # 创建HTTPS配置
        cat > "$CONF_FILE" << EOF
# HTTP跳转到HTTPS
server {
    listen 80;
    server_name $DOMAIN_NAME;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS主配置
server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;
    
    # SSL证书配置
    ssl_certificate $SSL_CERT_DIR/fullchain.pem;
    ssl_certificate_key $SSL_CERT_DIR/privkey.pem;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    
    # 日志配置
    access_log /www/wwwlogs/$DOMAIN_NAME.access.log;
    error_log /www/wwwlogs/$DOMAIN_NAME.error.log;
    
    # 前端静态文件
    location / {
        root /opt/lease-calculator/frontend;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 导出接口代理
    location /export/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 增加超时时间用于文件生成
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:5002/health;
        access_log off;
    }
    
    # 安全头配置
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types 
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
EOF
        
        echo "✅ HTTPS配置完成"
        ;;
        
    2)
        echo "配置 Let's Encrypt SSL证书..."
        
        # 安装 Certbot（如果未安装）
        if ! command -v certbot &> /dev/null; then
            echo "安装 Certbot..."
            yum install -y epel-release
            yum install -y certbot
        fi
        
        # 创建临时HTTP配置用于验证
        cat > "$CONF_FILE" << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    location /.well-known/acme-challenge/ {
        root /tmp/certbot-public;
        try_files \$uri =404;
    }
    
    location / {
        root /opt/lease-calculator/frontend;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        
        # 创建临时目录
        mkdir -p /tmp/certbot-public
        
        # 重启Nginx
        nginx -t && nginx -s reload
        
        # 获取SSL证书
        certbot certonly --webroot -w /tmp/certbot-public -d $DOMAIN_NAME --non-interactive --agree-tos --email admin@52trz.com
        
        # 复制证书到指定目录
        cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem "$SSL_CERT_DIR/"
        cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem "$SSL_CERT_DIR/"
        chmod 644 "$SSL_CERT_DIR/fullchain.pem"
        chmod 600 "$SSL_CERT_DIR/privkey.pem"
        
        # 创建完整的HTTPS配置（重用上面的配置模板）
        cat > "$CONF_FILE" << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;
    
    ssl_certificate $SSL_CERT_DIR/fullchain.pem;
    ssl_certificate_key $SSL_CERT_DIR/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    access_log /www/wwwlogs/$DOMAIN_NAME.access.log;
    error_log /www/wwwlogs/$DOMAIN_NAME.error.log;
    
    location / {
        root /opt/lease-calculator/frontend;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;
}
EOF
        
        # 设置自动续期
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'nginx -s reload'") | crontab -
        
        echo "✅ Let's Encrypt SSL证书配置完成"
        ;;
        
    3)
        echo "配置HTTP访问..."
        
        # 创建HTTP配置
        cat > "$CONF_FILE" << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    access_log /www/wwwlogs/$DOMAIN_NAME.access.log;
    error_log /www/wwwlogs/$DOMAIN_NAME.error.log;
    
    location / {
        root /opt/lease-calculator/frontend;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
        
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)\$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;
}
EOF
        
        echo "✅ HTTP配置完成"
        ;;
        
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

# 测试Nginx配置
echo "测试Nginx配置..."
nginx -t

if [ $? -eq 0 ]; then
    # 重启Nginx
    echo "重启Nginx..."
    nginx -s reload
    
    # 检查服务状态
    echo "检查服务状态..."
    if ! systemctl is-active --quiet lease-calculator; then
        echo "启动融资租赁计算器服务..."
        systemctl start lease-calculator
    fi
    
    echo ""
    echo "================================="
    echo "✅ 域名配置完成！"
    echo "================================="
    echo "域名: $DOMAIN_NAME"
    echo "配置文件: $CONF_FILE"
    
    if [ "$ssl_choice" == "1" ]; then
        echo "SSL证书目录: $SSL_CERT_DIR"
        echo "访问地址: https://$DOMAIN_NAME"
        echo "HTTP自动跳转到HTTPS"
        echo ""
        echo "📋 证书文件位置："
        echo "- 证书文件: $SSL_CERT_DIR/fullchain.pem"
        echo "- 私钥文件: $SSL_CERT_DIR/privkey.pem"
    elif [ "$ssl_choice" == "2" ]; then
        echo "访问地址: https://$DOMAIN_NAME"
        echo "HTTP自动跳转到HTTPS"
    else
        echo "访问地址: http://$DOMAIN_NAME"
    fi
    
    echo ""
    echo "🔍 验证命令:"
    echo "curl -I http://$DOMAIN_NAME"
    if [ "$ssl_choice" != "3" ]; then
        echo "curl -I https://$DOMAIN_NAME"
    fi
    
    echo ""
    echo "📊 服务状态检查:"
    echo "systemctl status lease-calculator"
    echo "systemctl status nginx"
    
    echo ""
    echo "📁 重要文件路径："
    echo "- 应用目录: /opt/lease-calculator"
    echo "- Nginx配置: $CONF_FILE"
    echo "- 日志目录: /www/wwwlogs"
    
    if [ "$ssl_choice" == "1" ]; then
        echo ""
        echo "🔒 SSL证书管理："
        echo "如需更换证书，请将新证书放置到："
        echo "$SSL_CERT_DIR/"
        echo "然后重新加载Nginx: nginx -s reload"
    fi
    
    echo "================================="
    
else
    echo "❌ Nginx配置有误，请检查配置文件"
    echo "配置文件路径: $CONF_FILE"
    echo "错误详情:"
    nginx -t
    exit 1
fi
