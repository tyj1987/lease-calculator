#!/bin/bash

# 融资租赁计算器 - 宝塔面板环境安装脚本
# 适用于：CentOS 7.9.2009 x86_64 (Python 3.7.9) + 宝塔面板
# Author: Auto Deployment Script
# Date: $(date +%Y-%m-%d)

set -e  # 遇到错误立即退出

echo "========================================="
echo "融资租赁计算器 - 宝塔面板环境部署脚本"
echo "系统: CentOS 7.9.2009 x86_64"
echo "Python: 3.7.9"
echo "环境: 宝塔面板"
echo "========================================="

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "请使用root用户运行此脚本"
   exit 1
fi

# 设置变量
APP_NAME="lease-calculator"
APP_DIR="/www/wwwroot/$APP_NAME"
SERVICE_USER="www"  # 宝塔面板默认用户
PYTHON_VERSION="3.7"
BT_PATH="/www/server"
NGINX_CONF_DIR="/www/server/nginx/conf/vhost"

# 检查宝塔面板是否安装
if [ ! -d "/www/server/panel" ]; then
    echo "❌ 错误: 未检测到宝塔面板，请先安装宝塔面板"
    echo "安装命令: yum install -y wget && wget -O install.sh http://download.bt.cn/install/install_6.0.sh && sh install.sh"
    exit 1
fi

echo "✅ 检测到宝塔面板环境"

# 检查Python版本
PYTHON_CMD=""
if command -v python3.7 &> /dev/null; then
    PYTHON_CMD="python3.7"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION_CHECK=$(python3 --version 2>&1 | grep -o "[0-9]\.[0-9]")
    if [[ "$PYTHON_VERSION_CHECK" == "3.7" ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 错误: 未找到Python 3.7，正在安装..."
    
    # 在宝塔环境中安装Python 3.7
    if [ -f "/www/server/panel/install/install_soft.sh" ]; then
        echo "使用宝塔面板安装Python 3.7..."
        /www/server/panel/install/install_soft.sh install python_manager
    else
        echo "安装Python 3.7依赖..."
        yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel xz-devel
        
        # 从源码编译Python 3.7
        cd /tmp
        wget https://www.python.org/ftp/python/3.7.9/Python-3.7.9.tgz
        tar xzf Python-3.7.9.tgz
        cd Python-3.7.9
        ./configure --enable-optimizations --prefix=/usr/local
        make -j 8
        make altinstall
        ln -sf /usr/local/bin/python3.7 /usr/bin/python3.7
        ln -sf /usr/local/bin/pip3.7 /usr/bin/pip3.7
    fi
    
    PYTHON_CMD="python3.7"
fi

echo "✅ Python环境检查完成: $PYTHON_CMD"

# 安装pip和必要的Python包管理工具
if ! command -v pip3.7 &> /dev/null; then
    echo "正在安装pip..."
    curl https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
fi

# 创建应用目录
echo "正在创建应用目录..."
mkdir -p $APP_DIR
cd $APP_DIR

# 复制应用文件
echo "正在复制应用文件..."
if [ -d "../backend" ]; then
    cp -r ../backend/* ./
else
    echo "❌ 错误: 未找到backend目录"
    exit 1
fi

if [ -d "../frontend" ]; then
    cp -r ../frontend ./
else
    echo "❌ 错误: 未找到frontend目录"
    exit 1
fi

# 设置目录权限
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR
chmod -R 755 $APP_DIR

# 创建虚拟环境
echo "正在创建Python虚拟环境..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装Python依赖
echo "正在安装Python依赖..."
if [ -f "requirements-centos7.txt" ]; then
    pip install -r requirements-centos7.txt
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "安装基础依赖..."
    pip install flask flask-cors pandas matplotlib seaborn plotly openpyxl
fi

# 创建日志目录
mkdir -p $APP_DIR/logs
chown -R $SERVICE_USER:$SERVICE_USER $APP_DIR/logs

# 创建systemd服务文件（适配宝塔环境）
echo "正在创建systemd服务..."
cat > /etc/systemd/system/lease-calculator.service << EOF
[Unit]
Description=融资租赁计算器
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python app.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
systemctl daemon-reload

# 创建Nginx配置文件（适配宝塔面板）
echo "正在创建Nginx配置..."

# 检查端口是否被占用
PORT=5002
while netstat -tuln | grep ":$PORT " > /dev/null; do
    PORT=$((PORT + 1))
done

echo "使用端口: $PORT"

# 更新app.py中的端口
sed -i "s/port=5002/port=$PORT/g" $APP_DIR/app.py

# 创建Nginx站点配置
DOMAIN_NAME="lease-calculator.local"
cat > $NGINX_CONF_DIR/$APP_NAME.conf << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    # 日志配置
    access_log /www/wwwlogs/$APP_NAME.access.log;
    error_log /www/wwwlogs/$APP_NAME.error.log;
    
    # 静态文件处理
    location /static/ {
        alias $APP_DIR/frontend/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header Access-Control-Allow-Origin "*";
    }
    
    # API请求代理到Flask
    location /api/ {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:$PORT/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 前端页面
    location / {
        try_files \$uri \$uri/ @flask;
        root $APP_DIR/frontend;
        index index.html;
        
        # SPA支持
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
            root $APP_DIR/frontend;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
        }
    }
    
    # 后备到Flask处理SPA路由
    location @flask {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 禁止访问敏感文件
    location ~ /\. {
        deny all;
    }
    
    location ~ \.(py|sh|conf)\$ {
        deny all;
    }
}
EOF

# 测试Nginx配置
echo "正在测试Nginx配置..."
if ! nginx -t; then
    echo "❌ Nginx配置测试失败，请检查配置文件"
    exit 1
fi

# 重载Nginx配置
echo "正在重载Nginx配置..."
systemctl reload nginx || systemctl restart nginx

# 启动服务
echo "正在启动服务..."
systemctl enable lease-calculator
systemctl start lease-calculator

# 等待服务启动
sleep 3

# 检查服务状态
if systemctl is-active --quiet lease-calculator; then
    echo "✅ 服务启动成功"
else
    echo "❌ 服务启动失败，检查日志:"
    systemctl status lease-calculator
    journalctl -u lease-calculator --no-pager -l
    exit 1
fi

# 健康检查
echo "正在进行健康检查..."
HEALTH_URL="http://127.0.0.1:$PORT/api/health"
for i in {1..5}; do
    if curl -s "$HEALTH_URL" | grep -q "healthy"; then
        echo "✅ 健康检查通过"
        break
    else
        echo "等待服务就绪... ($i/5)"
        sleep 2
    fi
done

# 创建管理脚本
echo "正在创建管理脚本..."
cat > $APP_DIR/manage.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="lease-calculator"
APP_DIR="/www/wwwroot/lease-calculator"

case "$1" in
    start)
        echo "启动融资租赁计算器..."
        systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "停止融资租赁计算器..."
        systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "重启融资租赁计算器..."
        systemctl restart $SERVICE_NAME
        ;;
    status)
        systemctl status $SERVICE_NAME
        ;;
    logs)
        journalctl -u $SERVICE_NAME -f
        ;;
    update)
        echo "更新应用..."
        systemctl stop $SERVICE_NAME
        cd $APP_DIR
        git pull origin main 2>/dev/null || echo "无Git仓库，跳过更新"
        source venv/bin/activate
        pip install -r requirements*.txt
        systemctl start $SERVICE_NAME
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|update}"
        exit 1
        ;;
esac
EOF

chmod +x $APP_DIR/manage.sh

# 添加到宝塔面板软件管理（如果可能）
if [ -f "/www/server/panel/class/public.py" ]; then
    echo "正在注册到宝塔面板..."
    # 这里可以添加宝塔面板集成代码
fi

# 创建快速访问脚本
cat > /usr/local/bin/lease-calc << EOF
#!/bin/bash
cd $APP_DIR && ./manage.sh \$@
EOF
chmod +x /usr/local/bin/lease-calc

echo "========================================="
echo "✅ 融资租赁计算器安装完成!"
echo "========================================="
echo ""
echo "📊 安装信息:"
echo "  应用目录: $APP_DIR"
echo "  运行端口: $PORT"
echo "  服务名称: lease-calculator"
echo "  运行用户: $SERVICE_USER"
echo ""
echo "🌐 访问地址:"
echo "  本地访问: http://localhost"
echo "  局域网访问: http://服务器IP"
echo "  健康检查: http://localhost/health"
echo ""
echo "🔧 管理命令:"
echo "  启动服务: lease-calc start"
echo "  停止服务: lease-calc stop"
echo "  重启服务: lease-calc restart"
echo "  查看状态: lease-calc status"
echo "  查看日志: lease-calc logs"
echo "  更新应用: lease-calc update"
echo ""
echo "📁 重要文件:"
echo "  应用管理: $APP_DIR/manage.sh"
echo "  Nginx配置: $NGINX_CONF_DIR/$APP_NAME.conf"
echo "  服务配置: /etc/systemd/system/lease-calculator.service"
echo ""
echo "🛠️ 宝塔面板集成:"
echo "  1. 可在宝塔面板 > 软件商店 > 已安装 中管理"
echo "  2. 可在宝塔面板 > 网站 中查看站点"
echo "  3. 日志文件位于 /www/wwwlogs/$APP_NAME.*.log"
echo ""
echo "⚠️  注意事项:"
echo "  1. 如需绑定域名，请修改: $NGINX_CONF_DIR/$APP_NAME.conf"
echo "  2. 防火墙需开放80端口"
echo "  3. 如需SSL，请在宝塔面板中配置"
echo ""
echo "🎉 部署完成，请访问 http://服务器IP 使用计算器!"
echo "========================================="
