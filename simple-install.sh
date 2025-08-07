#!/bin/bash

# 融资租赁计算器 - 极简Docker安装脚本
# 适用于：CentOS 7.9.2009 x86_64
# 无需复杂配置，一键启动

set -e

echo "========================================="
echo "融资租赁计算器 - 极简Docker部署"
echo "系统: CentOS 7.9.2009 x86_64"
echo "方式: Docker容器化"
echo "========================================="

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo "请使用root用户运行此脚本"
   exit 1
fi

# 设置变量
APP_NAME="lease-calculator"
CONTAINER_NAME="lease-calc"
PORT=8080

echo "步骤1: 安装Docker..."

# 检查Docker是否已安装
if command -v docker &> /dev/null; then
    echo "✅ Docker已安装"
else
    echo "正在安装Docker..."
    
    # 安装Docker
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io
    
    # 启动Docker服务
    systemctl start docker
    systemctl enable docker
    
    echo "✅ Docker安装完成"
fi

echo "步骤2: 构建应用镜像..."

# 创建Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制后端文件
COPY backend/ /app/

# 复制前端构建好的文件
COPY frontend/ /app/frontend/

# 安装Python依赖
RUN pip install --no-cache-dir flask flask-cors pandas matplotlib seaborn plotly openpyxl

# 暴露端口
EXPOSE 5002

# 启动命令
CMD ["python", "app.py"]
EOF

# 构建镜像
echo "正在构建Docker镜像..."
docker build -t $APP_NAME .

echo "步骤3: 启动容器..."

# 停止并删除已存在的容器
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# 启动新容器
docker run -d \
    --name $CONTAINER_NAME \
    --restart always \
    -p $PORT:5002 \
    $APP_NAME

# 等待容器启动
sleep 5

# 检查容器状态
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ 容器启动成功"
else
    echo "❌ 容器启动失败，查看日志:"
    docker logs $CONTAINER_NAME
    exit 1
fi

# 健康检查
echo "步骤4: 健康检查..."
for i in {1..5}; do
    if curl -s "http://localhost:$PORT/api/health" | grep -q "healthy"; then
        echo "✅ 健康检查通过"
        break
    else
        echo "等待服务就绪... ($i/5)"
        sleep 3
    fi
done

# 创建管理脚本
cat > /usr/local/bin/lease-calc << EOF
#!/bin/bash
case "\$1" in
    start)
        docker start $CONTAINER_NAME
        ;;
    stop)
        docker stop $CONTAINER_NAME
        ;;
    restart)
        docker restart $CONTAINER_NAME
        ;;
    status)
        docker ps | grep $CONTAINER_NAME || echo "容器未运行"
        ;;
    logs)
        docker logs -f $CONTAINER_NAME
        ;;
    update)
        echo "更新应用..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        docker build -t $APP_NAME .
        docker run -d --name $CONTAINER_NAME --restart always -p $PORT:5002 $APP_NAME
        ;;
    shell)
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    *)
        echo "用法: \$0 {start|stop|restart|status|logs|update|shell}"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/lease-calc

echo "========================================="
echo "✅ 融资租赁计算器部署完成!"
echo "========================================="
echo ""
echo "🌐 访问地址:"
echo "  http://localhost:$PORT"
echo "  http://服务器IP:$PORT"
echo ""
echo "🔧 管理命令:"
echo "  lease-calc start     # 启动"
echo "  lease-calc stop      # 停止"
echo "  lease-calc restart   # 重启"
echo "  lease-calc status    # 状态"
echo "  lease-calc logs      # 日志"
echo "  lease-calc update    # 更新"
echo "  lease-calc shell     # 进入容器"
echo ""
echo "🔥 防火墙设置:"
echo "  firewall-cmd --permanent --add-port=$PORT/tcp"
echo "  firewall-cmd --reload"
echo ""
echo "🎉 部署完成！访问 http://服务器IP:$PORT 使用计算器"
echo "========================================="