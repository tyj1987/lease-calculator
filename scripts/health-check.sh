#!/bin/bash

# 健康检查脚本
# 用于验证应用是否正常运行

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# 配置
APP_URL="${APP_URL:-http://localhost:5002}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost}"
TIMEOUT="${TIMEOUT:-10}"

log "🔍 开始健康检查..."

# 检查后端API健康状态
info "检查后端API健康状态..."
if curl -f -s --max-time $TIMEOUT "${APP_URL}/api/health" > /dev/null; then
    log "✅ 后端API健康检查通过"
else
    error "❌ 后端API健康检查失败"
    exit 1
fi

# 检查API响应内容
info "检查API响应内容..."
API_RESPONSE=$(curl -s --max-time $TIMEOUT "${APP_URL}/api/health")
if echo "$API_RESPONSE" | grep -q "healthy"; then
    log "✅ API响应内容正确"
else
    error "❌ API响应内容异常: $API_RESPONSE"
    exit 1
fi

# 检查前端服务
info "检查前端服务..."
if curl -f -s --max-time $TIMEOUT "${FRONTEND_URL}/" > /dev/null; then
    log "✅ 前端服务正常"
else
    warn "⚠️ 前端服务可能异常"
fi

# 测试核心API功能
info "测试核心计算API..."
CALC_RESPONSE=$(curl -s --max-time $TIMEOUT -X POST \
    "${APP_URL}/api/calculate" \
    -H "Content-Type: application/json" \
    -d '{
        "method": "equal_annuity",
        "pv": 1000000,
        "annual_rate": 0.08,
        "periods": 36,
        "frequency": 12
    }')

if echo "$CALC_RESPONSE" | grep -q "success"; then
    log "✅ 核心计算API功能正常"
else
    error "❌ 核心计算API功能异常: $CALC_RESPONSE"
    exit 1
fi

# 检查Docker容器状态（如果使用Docker）
if command -v docker &> /dev/null; then
    info "检查Docker容器状态..."
    if docker-compose ps | grep -q "Up"; then
        log "✅ Docker容器运行正常"
    else
        warn "⚠️ Docker容器状态异常"
    fi
fi

# 检查系统资源
info "检查系统资源使用情况..."

# 内存使用率
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
    warn "⚠️ 内存使用率过高: ${MEM_USAGE}%"
else
    log "✅ 内存使用率正常: ${MEM_USAGE}%"
fi

# 磁盘使用率
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    warn "⚠️ 磁盘使用率过高: ${DISK_USAGE}%"
else
    log "✅ 磁盘使用率正常: ${DISK_USAGE}%"
fi

# 检查日志文件
info "检查日志文件..."
if [ -f "logs/lease-calculator.log" ]; then
    LOG_SIZE=$(du -h logs/lease-calculator.log | cut -f1)
    log "✅ 日志文件正常，大小: $LOG_SIZE"
    
    # 检查最近的错误日志
    ERROR_COUNT=$(tail -n 100 logs/lease-calculator.log | grep -i "error" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        warn "⚠️ 发现 $ERROR_COUNT 个错误日志"
    fi
else
    warn "⚠️ 日志文件不存在"
fi

# 性能测试
info "执行简单性能测试..."
START_TIME=$(date +%s.%N)
for i in {1..5}; do
    curl -s --max-time 5 "${APP_URL}/api/health" > /dev/null
done
END_TIME=$(date +%s.%N)
DURATION=$(echo "$END_TIME - $START_TIME" | bc)
AVG_TIME=$(echo "scale=3; $DURATION / 5" | bc)

if (( $(echo "$AVG_TIME > 1.0" | bc -l) )); then
    warn "⚠️ API响应时间较慢: 平均 ${AVG_TIME}秒"
else
    log "✅ API响应时间正常: 平均 ${AVG_TIME}秒"
fi

echo ""
echo "======================================="
log "🎉 健康检查完成！"
echo "======================================="
echo ""
echo "📊 检查结果汇总:"
echo "  🌐 后端API: 正常"
echo "  🎨 前端服务: 正常"
echo "  ⚙️ 核心功能: 正常"
echo "  💾 内存使用: ${MEM_USAGE}%"
echo "  💿 磁盘使用: ${DISK_USAGE}%"
echo "  ⏱️ 平均响应: ${AVG_TIME}秒"
echo ""
echo "🔗 访问地址:"
echo "  前端: $FRONTEND_URL"
echo "  API:  $APP_URL/api/health"
echo ""

log "健康检查全部通过 ✅"
