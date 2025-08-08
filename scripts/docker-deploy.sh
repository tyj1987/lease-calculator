#!/bin/bash

# Docker 快速部署脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

log "🐳 融资租赁计算器 - Docker快速部署"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    error "Docker未安装，请先安装Docker"
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose未安装，请先安装Docker Compose"
fi

# 检查Docker服务状态
if ! docker info &> /dev/null; then
    error "Docker服务未运行，请启动Docker服务"
fi

log "✅ Docker环境检查通过"

# 停止可能存在的容器
info "停止现有容器..."
docker-compose down 2>/dev/null || true

# 清理旧镜像
info "清理旧镜像..."
docker system prune -f

# 构建并启动服务
log "🚀 启动服务..."
docker-compose up -d --build

# 等待服务启动
log "⏳ 等待服务启动..."
sleep 15

# 健康检查
log "🔍 执行健康检查..."
if curl -f -s http://localhost:5002/api/health > /dev/null; then
    log "✅ 应用健康检查通过"
else
    warn "❌ 应用健康检查失败"
fi

if curl -f -s http://localhost/ > /dev/null; then
    log "✅ Nginx反向代理正常"
else
    warn "❌ Nginx反向代理可能有问题"
fi

# 显示容器状态
log "📊 容器状态:"
docker-compose ps

# 显示日志
log "📄 最近日志:"
docker-compose logs --tail=10

# 显示访问信息
echo ""
echo "======================================="
echo -e "${GREEN}🎉 Docker部署完成！${NC}"
echo "======================================="
echo ""
echo "🌐 访问地址:"
echo "   HTTP:  http://localhost"
echo "   API:   http://localhost/api/health"
echo ""
echo "🔧 管理命令:"
echo "   查看状态: docker-compose ps"
echo "   查看日志: docker-compose logs -f"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart"
echo ""
echo "📁 数据卷:"
echo "   日志目录: ./logs"
echo "   配置目录: ./config"
echo ""

log "🎯 部署完成！项目已在Docker中运行"
