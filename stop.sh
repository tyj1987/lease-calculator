#!/bin/bash

# 融资租赁计算器停止脚本

SERVICE_NAME="lease-calculator"

echo "正在停止融资租赁计算器..."

# 停止后端服务
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "停止后端服务..."
    systemctl stop $SERVICE_NAME
    echo "✓ 后端服务已停止"
else
    echo "后端服务未运行"
fi

echo ""
echo "================================="
echo "融资租赁计算器已停止"
echo "================================="
echo "重新启动: systemctl start $SERVICE_NAME"
echo "或运行: ./start.sh"
echo "================================="
