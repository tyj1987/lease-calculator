#!/bin/bash

# Docker镜像大小优化对比脚本
# 构建并比较不同版本的镜像大小

echo "🔍 Docker镜像大小优化对比测试"
echo "================================"

# 定义镜像标签
IMAGE_NAME="lease-calculator"
ORIGINAL_TAG="original"
OPTIMIZED_TAG="optimized" 
ALPINE_TAG="alpine"

echo ""
echo "📦 1. 构建原始版本 (当前Dockerfile)..."
docker build -f Dockerfile -t ${IMAGE_NAME}:${ORIGINAL_TAG} . || {
    echo "❌ 原始版本构建失败"
    exit 1
}

echo ""
echo "📦 2. 构建优化版本 (多阶段构建)..."
docker build -f Dockerfile.optimized -t ${IMAGE_NAME}:${OPTIMIZED_TAG} . || {
    echo "❌ 优化版本构建失败"
    exit 1
}

echo ""
echo "📦 3. 构建Alpine版本 (超轻量)..."
docker build -f Dockerfile.alpine -t ${IMAGE_NAME}:${ALPINE_TAG} . || {
    echo "❌ Alpine版本构建失败"
    exit 1
}

echo ""
echo "📊 镜像大小对比结果："
echo "================================"

# 获取镜像大小
original_size=$(docker images ${IMAGE_NAME}:${ORIGINAL_TAG} --format "{{.Size}}")
optimized_size=$(docker images ${IMAGE_NAME}:${OPTIMIZED_TAG} --format "{{.Size}}")
alpine_size=$(docker images ${IMAGE_NAME}:${ALPINE_TAG} --format "{{.Size}}")

echo "🔹 原始版本:    ${original_size}"
echo "🔹 优化版本:    ${optimized_size}"
echo "🔹 Alpine版本:  ${alpine_size}"

echo ""
echo "📋 详细信息："
docker images ${IMAGE_NAME} --format "table {{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "🧪 测试镜像功能："
echo "启动测试容器..."

# 测试Alpine版本
echo "正在测试Alpine版本..."
docker run -d --name test-alpine -p 5005:5002 ${IMAGE_NAME}:${ALPINE_TAG}
sleep 5

if curl -s http://localhost:5005/api/health > /dev/null; then
    echo "✅ Alpine版本功能正常"
else
    echo "❌ Alpine版本功能异常"
    docker logs test-alpine
fi

# 清理测试容器
docker stop test-alpine > /dev/null 2>&1
docker rm test-alpine > /dev/null 2>&1

echo ""
echo "🎯 优化建议："
echo "1. 建议使用Alpine版本 (${alpine_size})"
echo "2. 如果需要完整功能，使用优化版本 (${optimized_size})"
echo "3. 原始版本过大，不建议生产使用 (${original_size})"
