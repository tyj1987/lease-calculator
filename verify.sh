#!/bin/bash

echo "========================================"
echo "部署包完整性验证"
echo "========================================"

ERRORS=0

# 检查后端文件
echo "🔍 检查后端文件..."
BACKEND_FILES=("app.py" "lease_calculator.py" "requirements.txt")
for file in "${BACKEND_FILES[@]}"; do
    if [ ! -f "backend/$file" ]; then
        echo "❌ 缺失: backend/$file"
        ERRORS=$((ERRORS + 1))
    fi
done

# 检查前端文件
echo "🔍 检查前端文件..."
if [ ! -f "frontend/index.html" ]; then
    echo "❌ 缺失: frontend/index.html"
    ERRORS=$((ERRORS + 1))
fi

if [ ! -d "frontend/static" ]; then
    echo "❌ 缺失: frontend/static目录"
    ERRORS=$((ERRORS + 1))
fi

# 检查配置文件
echo "🔍 检查配置文件..."
CONFIG_FILES=("nginx.conf" "lease-calculator.service")
for file in "${CONFIG_FILES[@]}"; do
    if [ ! -f "config/$file" ]; then
        echo "❌ 缺失: config/$file"
        ERRORS=$((ERRORS + 1))
    fi
done

# 检查脚本文件
echo "🔍 检查脚本文件..."
SCRIPT_FILES=("install.sh" "quick-deploy.sh" "setup-domain.sh")
for file in "${SCRIPT_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺失: $file"
        ERRORS=$((ERRORS + 1))
    elif [ ! -x "$file" ]; then
        echo "🔧 修复: 设置 $file 执行权限"
        chmod +x "$file"
    fi
done

# 显示统计信息
echo ""
echo "📊 文件统计:"
echo "前端文件: $(find frontend -type f | wc -l) 个"
echo "后端文件: $(find backend -type f | wc -l) 个"  
echo "配置文件: $(find config -type f | wc -l) 个"
echo "总大小: $(du -sh . | cut -f1)"

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo "✅ 验证通过！部署包完整，可以安全部署。"
    echo "========================================"
    exit 0
else
    echo ""
    echo "❌ 验证失败！发现 $ERRORS 个问题，请重新下载部署包。"
    echo "========================================"
    exit 1
fi
