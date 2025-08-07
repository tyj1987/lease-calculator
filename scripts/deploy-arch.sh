#!/bin/bash

# Arch Linux 专用部署脚本

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

log "Arch Linux 系统部署脚本"

# 更新系统
log "更新系统包..."
sudo pacman -Syu --noconfirm

# 安装依赖
log "安装系统依赖..."
sudo pacman -S --noconfirm python python-pip git nginx curl htop

# 设置Python环境
log "设置Python环境..."
cd backend
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cd ..

# 配置Nginx
log "配置Nginx..."
sudo cp config/nginx.conf /etc/nginx/conf.d/lease-calculator.conf

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

# 配置防火墙 (如果使用ufw)
if command -v ufw &> /dev/null; then
    log "配置UFW防火墙..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp  
    sudo ufw allow 443/tcp
    sudo ufw --force enable
else
    log "未安装UFW，请手动配置防火墙规则"
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

log "🎉 Arch Linux 系统部署完成！"
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
