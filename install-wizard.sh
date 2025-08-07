#!/bin/bash

# 融资租赁计算器 - 一键安装选择器
# 提供多种简化安装方案

echo "========================================="
echo "🚀 融资租赁计算器 - 安装向导"
echo "========================================="
echo ""
echo "请选择安装方式:"
echo ""
echo "1) 🐳 Docker容器化安装 (推荐)"
echo "   ✅ 最简单，环境隔离"
echo "   ✅ 一键启动，自动重启"
echo "   ✅ 无需配置Python环境"
echo ""
echo "2) 🐍 Python直接运行"
echo "   ✅ 轻量级，占用资源少"
echo "   ✅ 直接使用系统Python"
echo "   ✅ 适合开发和测试"
echo ""
echo "3) 📋 查看系统信息"
echo ""

read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🐳 开始Docker安装..."
        echo "----------------------------------------"
        if [ -f "simple-install.sh" ]; then
            ./simple-install.sh
        else
            echo "❌ 错误: 未找到Docker安装脚本"
            exit 1
        fi
        ;;
    2)
        echo ""
        echo "🐍 开始Python直接安装..."
        echo "----------------------------------------"
        if [ -f "ultra-simple-install.sh" ]; then
            ./ultra-simple-install.sh
        else
            echo "❌ 错误: 未找到Python安装脚本"
            exit 1
        fi
        ;;
    3)
        echo ""
        echo "📋 系统信息:"
        echo "----------------------------------------"
        echo "操作系统: $(cat /etc/redhat-release 2>/dev/null || echo '未知')"
        echo "内核版本: $(uname -r)"
        echo "架构: $(uname -m)"
        echo ""
        echo "Python版本:"
        python3 --version 2>/dev/null || echo "  ❌ Python3 未安装"
        python3.8 --version 2>/dev/null && echo "  ✅ Python 3.8 可用"
        python3.7 --version 2>/dev/null && echo "  ✅ Python 3.7 可用"
        echo ""
        echo "Docker状态:"
        if command -v docker &> /dev/null; then
            echo "  ✅ Docker 已安装: $(docker --version)"
            if systemctl is-active --quiet docker; then
                echo "  ✅ Docker 服务运行中"
            else
                echo "  ⚠️  Docker 服务未启动"
            fi
        else
            echo "  ❌ Docker 未安装"
        fi
        echo ""
        echo "网络端口:"
        echo "  8080端口: $(netstat -tuln | grep :8080 && echo '占用' || echo '可用')"
        echo "  5002端口: $(netstat -tuln | grep :5002 && echo '占用' || echo '可用')"
        echo ""
        echo "重新运行脚本选择安装方式"
        ;;
    *)
        echo "❌ 无效选项，请重新运行脚本"
        exit 1
        ;;
esac
