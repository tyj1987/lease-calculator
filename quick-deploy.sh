#!/bin/bash

echo "========================================"
echo "融资租赁计算器 - 快速部署"
echo "========================================"

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "❌ 请使用root用户运行: sudo ./quick-deploy.sh"
   exit 1
fi

# 预检查
echo "🔍 正在进行预检查..."

if [ ! -f "backend/app.py" ]; then
    echo "❌ 错误: 后端文件缺失"
    exit 1
fi

if [ ! -f "frontend/index.html" ]; then
    echo "❌ 错误: 前端文件缺失"
    exit 1
fi

echo "✅ 预检查通过"

# 显示系统信息
echo "📋 系统信息:"
echo "操作系统: $(cat /etc/redhat-release 2>/dev/null || echo 'Unknown')"
echo "Python版本: $(python3 --version 2>/dev/null || echo 'Not found')"
echo "内存使用: $(free -h | grep Mem)"
echo "磁盘空间: $(df -h / | tail -1)"

# 运行安装
echo ""
echo "🚀 开始安装..."
./install.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "🎉 部署成功!"
    echo "========================================"
    echo "🌐 访问地址: http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "📋 管理命令:"
    echo "  启动服务: systemctl start lease-calculator"
    echo "  停止服务: systemctl stop lease-calculator"  
    echo "  查看状态: systemctl status lease-calculator"
    echo "  查看日志: journalctl -u lease-calculator -f"
    echo ""
    echo "🔧 配置域名:"
    echo "  sudo ./setup-domain.sh your-domain.com"
    echo ""
    echo "📚 更多信息请查看 docs/ 目录"
    echo "========================================"
else
    echo "❌ 部署失败，请检查错误信息并参考文档"
    exit 1
fi
