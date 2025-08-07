#!/bin/bash

# 融资租赁计算器快速启动脚本

APP_DIR="/opt/lease-calculator"
SERVICE_NAME="lease-calculator"

echo "正在启动融资租赁计算器..."

# 检查服务状态
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "服务已在运行中"
    systemctl status $SERVICE_NAME
else
    echo "启动后端服务..."
    systemctl start $SERVICE_NAME
    
    # 等待服务启动
    sleep 3
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✓ 后端服务启动成功"
    else
        echo "✗ 后端服务启动失败"
        echo "查看日志: journalctl -u $SERVICE_NAME -f"
        exit 1
    fi
fi

# 检查Nginx状态
if systemctl is-active --quiet nginx; then
    echo "✓ Nginx已运行"
else
    echo "启动Nginx..."
    systemctl start nginx
    if systemctl is-active --quiet nginx; then
        echo "✓ Nginx启动成功"
    else
        echo "✗ Nginx启动失败"
        exit 1
    fi
fi

echo ""
echo "================================="
echo "🎉 融资租赁计算器启动成功!"
echo "================================="
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo "服务状态: systemctl status $SERVICE_NAME"
echo "查看日志: journalctl -u $SERVICE_NAME -f"
echo "停止服务: systemctl stop $SERVICE_NAME"
echo "================================="
