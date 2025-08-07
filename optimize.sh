#!/bin/bash

# 融资租赁计算器 - 生产环境优化脚本
# 用于CentOS 7生产部署的额外优化

echo "正在进行生产环境优化..."

# 优化systemd服务配置
cat > /etc/systemd/system/lease-calculator.service << 'EOF'
[Unit]
Description=Lease Calculator Backend Service
After=network.target

[Service]
Type=simple
User=leaseapp
Group=leaseapp
WorkingDirectory=/opt/lease-calculator/backend
Environment=PATH=/opt/lease-calculator/backend/venv/bin
Environment=FLASK_ENV=production
Environment=FLASK_APP=app.py
Environment=PYTHONPATH=/opt/lease-calculator/backend

# 使用Gunicorn作为WSGI服务器 (更适合生产环境)
ExecStart=/opt/lease-calculator/backend/venv/bin/gunicorn --bind 127.0.0.1:5002 --workers 4 --timeout 120 --keep-alive 2 --max-requests 1000 --max-requests-jitter 100 app:app

ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lease-calculator

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
systemctl daemon-reload

# 优化Nginx配置
cat > /etc/nginx/conf.d/lease-calculator.conf << 'EOF'
# 上游后端服务器配置
upstream lease_backend {
    server 127.0.0.1:5002;
    keepalive 32;
}

server {
    listen 80;
    server_name _;
    
    # 日志配置
    access_log /var/log/nginx/lease-calculator.access.log;
    error_log /var/log/nginx/lease-calculator.error.log;
    
    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # 前端静态文件
    location / {
        root /opt/lease-calculator/frontend;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
        
        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Static-Cache "HIT";
        }
        
        # HTML文件不缓存
        location ~* \.html$ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
        }
    }
    
    # API代理优化
    location /api/ {
        proxy_pass http://lease_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲配置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # 连接复用
        proxy_set_header Connection "";
    }
    
    # 导出接口代理
    location /export/ {
        proxy_pass http://lease_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 增加超时时间用于文件生成
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # 大文件支持
        client_max_body_size 10M;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://lease_backend/health;
        access_log off;
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }
    
    # Gzip压缩优化
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
        text/json
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml
        font/truetype
        font/opentype
        application/vnd.ms-fontobject;
        
    # 禁止访问敏感文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# 测试Nginx配置
nginx -t

if [ $? -eq 0 ]; then
    echo "✓ Nginx配置验证成功"
    systemctl reload nginx
else
    echo "✗ Nginx配置验证失败"
    exit 1
fi

# 配置日志轮转
cat > /etc/logrotate.d/lease-calculator << 'EOF'
/var/log/nginx/lease-calculator.*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}

/opt/lease-calculator/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 leaseapp leaseapp
    postrotate
        systemctl reload lease-calculator
    endscript
}
EOF

# 创建性能监控脚本
cat > /opt/lease-calculator/monitor.sh << 'EOF'
#!/bin/bash

# 融资租赁计算器性能监控脚本

LOG_FILE="/var/log/lease-calculator/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 检查服务状态
if systemctl is-active --quiet lease-calculator; then
    SERVICE_STATUS="运行中"
else
    SERVICE_STATUS="已停止"
    echo "[$DATE] 警告: 服务已停止" >> $LOG_FILE
fi

# 检查端口
if netstat -tlnp | grep -q :5002; then
    PORT_STATUS="正常"
else
    PORT_STATUS="异常"
    echo "[$DATE] 警告: 端口5002未监听" >> $LOG_FILE
fi

# 检查内存使用
MEMORY_USAGE=$(ps aux | grep "[g]unicorn" | awk '{sum += $6} END {print sum/1024}')
if [ -z "$MEMORY_USAGE" ]; then
    MEMORY_USAGE=0
fi

# 检查磁盘空间
DISK_USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')

# 检查日志文件大小
LOG_SIZE=$(du -sh /opt/lease-calculator/logs 2>/dev/null | cut -f1 || echo "0K")

echo "[$DATE] 状态报告: 服务=$SERVICE_STATUS, 端口=$PORT_STATUS, 内存=${MEMORY_USAGE}MB, 磁盘使用=${DISK_USAGE}%, 日志大小=$LOG_SIZE"

# 如果磁盘使用超过90%，发出警告
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "[$DATE] 警告: 磁盘使用率过高 ($DISK_USAGE%)" >> $LOG_FILE
fi
EOF

chmod +x /opt/lease-calculator/monitor.sh
chown leaseapp:leaseapp /opt/lease-calculator/monitor.sh

# 添加监控到crontab
if ! crontab -u leaseapp -l 2>/dev/null | grep -q "monitor.sh"; then
    (crontab -u leaseapp -l 2>/dev/null; echo "*/5 * * * * /opt/lease-calculator/monitor.sh") | crontab -u leaseapp -
    echo "✓ 已添加性能监控任务"
fi

# 优化系统参数
cat >> /etc/sysctl.conf << 'EOF'

# 融资租赁计算器优化参数
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000
EOF

sysctl -p

echo ""
echo "================================="
echo "✅ 生产环境优化完成!"
echo "================================="
echo "优化内容:"
echo "- 使用Gunicorn WSGI服务器"
echo "- 优化Nginx配置"
echo "- 配置日志轮转"
echo "- 添加性能监控"
echo "- 优化系统参数"
echo ""
echo "监控命令:"
echo "- 查看服务状态: systemctl status lease-calculator"
echo "- 查看性能监控: tail -f /var/log/lease-calculator/monitor.log"
echo "- 手动性能检查: /opt/lease-calculator/monitor.sh"
echo "================================="
