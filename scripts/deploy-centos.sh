#!/bin/bash

# CentOS/RHEL 专用部署脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

log "CentOS/RHEL 系统部署脚本"

# 检测包管理器
if command -v dnf &> /dev/null; then
    PKG_MGR="dnf"
elif command -v yum &> /dev/null; then
    PKG_MGR="yum"
else
    error "未找到包管理器"
fi

log "使用包管理器: $PKG_MGR"

# 更新系统
log "更新系统包..."
sudo $PKG_MGR update -y

# 安装EPEL仓库 (如果需要)
if [ "$PKG_MGR" = "yum" ]; then
    sudo yum install -y epel-release
fi

# 安装依赖
log "安装系统依赖..."
sudo $PKG_MGR install -y python3 python3-pip git nginx curl htop

# 设置Python环境
log "设置Python环境..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 如果是CentOS 7，可能需要特殊处理
if [ -f requirements-centos7.txt ]; then
    pip install -r requirements-centos7.txt
else
    pip install -r requirements.txt
fi

cd ..

# 配置Nginx
log "配置Nginx..."
sudo cp config/nginx.conf /etc/nginx/conf.d/lease-calculator.conf

# 设置SELinux (如果启用)
if command -v getenforce &> /dev/null && [ "$(getenforce)" = "Enforcing" ]; then
    log "配置SELinux..."
    sudo setsebool -P httpd_can_network_connect 1
fi

# 测试Nginx配置
if sudo nginx -t; then
    sudo systemctl restart nginx
    sudo systemctl enable nginx
else
    error "Nginx配置错误"
fi

# 设置系统服务
log "设置systemd服务..."
sed "s|/path/to/your|$(pwd)|g" config/lease-calculator.service > /tmp/lease-calculator.service
sudo cp /tmp/lease-calculator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lease-calculator
sudo systemctl start lease-calculator

# 配置Firewalld防火墙
log "配置防火墙..."
if systemctl is-active --quiet firewalld; then
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --permanent --add-service=ssh
    sudo firewall-cmd --reload
else
    log "Firewalld未运行，跳过防火墙配置"
fi

# 健康检查
log "健康检查..."
sleep 10

if systemctl is-active --quiet lease-calculator; then
    log "✅ 应用服务运行正常"
else
    error "❌ 应用服务启动失败"
fi

if systemctl is-active --quiet nginx; then
    log "✅ Nginx服务运行正常"
else
    error "❌ Nginx服务异常"
fi

log "🎉 CentOS/RHEL 系统部署完成！"
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
