#!/bin/bash

# 融资租赁计算器 - 超简单安装脚本
# 适用于：CentOS 7.9.2009 x86_64，Python 3.8+
# 无需Nginx、Docker，直接运行

set -e

echo "========================================="
echo "融资租赁计算器 - 超简单部署"
echo "系统: CentOS 7.9.2009 x86_64"
echo "方式: Python直接运行"
echo "========================================="

# 设置变量
APP_NAME="lease-calculator"
APP_DIR="/opt/$APP_NAME"
PORT=8080

echo "步骤1: 检查Python环境..."

# 检测Python版本
PYTHON_CMD=""
if command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
elif command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version 2>&1 | grep -o "[0-9]\.[0-9]")
    if [[ "$PYTHON_VER" == "3.8" ]] || [[ "$PYTHON_VER" > "3.8" ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ 错误: 需要Python 3.8+版本"
    echo "您的Python版本: $(python3 --version 2>/dev/null || echo '未安装')"
    exit 1
fi

echo "✅ 找到Python: $PYTHON_CMD ($(${PYTHON_CMD} --version))"

echo "步骤2: 安装pip依赖..."

# 确保pip可用
if ! command -v pip3 &> /dev/null; then
    echo "正在安装pip..."
    curl https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
fi

echo "步骤3: 创建应用目录..."

# 创建目录
mkdir -p $APP_DIR
cd $APP_DIR

# 复制文件
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

echo "步骤4: 安装Python依赖..."

# 安装基础依赖
pip3 install flask flask-cors pandas matplotlib seaborn plotly openpyxl

echo "步骤5: 修改应用配置..."

# 创建简化版启动脚本
cat > app_simple.py << EOF
#!/usr/bin/env python3
"""
融资租赁计算器 - 简化版启动脚本
直接运行，无需复杂配置
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入原始app
from app import app

if __name__ == '__main__':
    import logging
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 50)
    print("🚀 融资租赁计算器启动中...")
    print("🌐 访问地址: http://localhost:$PORT")
    print("🌐 局域网访问: http://服务器IP:$PORT")
    print("⏹️  停止服务: Ctrl+C")
    print("=" * 50)
    
    # 启动应用
    app.run(
        host='0.0.0.0',
        port=$PORT,
        debug=False,
        threaded=True
    )
EOF

echo "步骤6: 创建启动脚本..."

# 创建启动脚本
cat > start.sh << EOF
#!/bin/bash
cd $APP_DIR
echo "启动融资租赁计算器..."
nohup $PYTHON_CMD app_simple.py > logs/app.log 2>&1 &
echo \$! > app.pid
echo "服务已启动，PID: \$(cat app.pid)"
echo "访问: http://localhost:$PORT"
EOF

# 创建停止脚本
cat > stop.sh << EOF
#!/bin/bash
cd $APP_DIR
if [ -f app.pid ]; then
    PID=\$(cat app.pid)
    if kill \$PID 2>/dev/null; then
        echo "服务已停止"
        rm -f app.pid
    else
        echo "服务未运行或停止失败"
    fi
else
    echo "未找到PID文件，尝试强制停止..."
    pkill -f "app_simple.py" || echo "没有找到运行的服务"
fi
EOF

# 创建状态检查脚本
cat > status.sh << EOF
#!/bin/bash
cd $APP_DIR
if [ -f app.pid ] && kill -0 \$(cat app.pid) 2>/dev/null; then
    echo "✅ 服务正在运行，PID: \$(cat app.pid)"
    echo "🌐 访问地址: http://localhost:$PORT"
    curl -s http://localhost:$PORT/api/health | grep -q healthy && echo "✅ 健康检查通过" || echo "❌ 健康检查失败"
else
    echo "❌ 服务未运行"
fi
EOF

# 设置执行权限
chmod +x start.sh stop.sh status.sh app_simple.py

# 创建日志目录
mkdir -p logs

echo "步骤7: 创建全局管理命令..."

# 创建全局管理脚本
cat > /usr/local/bin/lease-calc << EOF
#!/bin/bash
cd $APP_DIR
case "\$1" in
    start)
        ./start.sh
        ;;
    stop)
        ./stop.sh
        ;;
    restart)
        ./stop.sh
        sleep 2
        ./start.sh
        ;;
    status)
        ./status.sh
        ;;
    logs)
        tail -f logs/app.log
        ;;
    test)
        curl -s http://localhost:$PORT/api/health || echo "服务未响应"
        ;;
    run)
        echo "直接运行模式 (Ctrl+C停止):"
        $PYTHON_CMD app_simple.py
        ;;
    *)
        echo "用法: \$0 {start|stop|restart|status|logs|test|run}"
        echo ""
        echo "  start   - 后台启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        echo "  test    - 测试连接"
        echo "  run     - 前台运行（调试用）"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/lease-calc

echo "步骤8: 启动服务..."

# 启动服务
./start.sh

# 等待启动
sleep 3

echo "步骤9: 验证部署..."

# 验证服务
if curl -s "http://localhost:$PORT/api/health" | grep -q "healthy"; then
    echo "✅ 服务启动成功"
else
    echo "⚠️  服务可能启动中，请稍等或查看日志"
fi

echo "========================================="
echo "✅ 融资租赁计算器部署完成!"
echo "========================================="
echo ""
echo "📁 安装目录: $APP_DIR"
echo "🌐 访问地址:"
echo "  http://localhost:$PORT"
echo "  http://服务器IP:$PORT"
echo ""
echo "🔧 管理命令:"
echo "  lease-calc start     # 后台启动"
echo "  lease-calc stop      # 停止服务"
echo "  lease-calc restart   # 重启服务"
echo "  lease-calc status    # 查看状态"
echo "  lease-calc logs      # 查看日志"
echo "  lease-calc test      # 测试连接"
echo "  lease-calc run       # 前台运行（调试）"
echo ""
echo "🔥 防火墙设置（如需要）:"
echo "  firewall-cmd --permanent --add-port=$PORT/tcp"
echo "  firewall-cmd --reload"
echo ""
echo "🎉 现在可以访问 http://服务器IP:$PORT 使用计算器！"
echo "========================================="
