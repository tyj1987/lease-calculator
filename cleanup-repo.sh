#!/bin/bash

# 仓库彻底清理脚本 - 确保GitHub仓库极其干净整洁
# 删除所有开发、测试、缓存和临时文件

echo "🧹 开始彻底清理仓库..."

# ===== 1. 删除Python缓存和编译文件 =====
echo "📦 清理Python缓存..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true
find . -name "*.so" -delete 2>/dev/null || true

# ===== 2. 删除测试和覆盖率文件 =====
echo "🧪 清理测试相关文件..."
rm -rf .pytest_cache/
rm -rf htmlcov/
rm -f .coverage
rm -f coverage.xml
rm -rf .tox/
rm -rf .cache/

# ===== 3. 删除日志文件 =====
echo "📋 清理日志文件..."
rm -rf logs/
rm -f *.log
rm -f backend/logs/
find . -name "*.log" -delete 2>/dev/null || true

# ===== 4. 删除大型报告文件 =====
echo "📊 清理分析报告..."
rm -f bandit-report.json
rm -f backend/bandit-report.json
rm -f safety-report.json
rm -f backend/safety-report.json

# ===== 5. 删除虚拟环境 =====
echo "🐍 清理虚拟环境..."
rm -rf backend/venv/
rm -rf venv/
rm -rf env/
rm -rf .venv/

# ===== 6. 删除测试文件（保留tests目录结构，但清理临时文件）=====
echo "🔬 清理测试文件..."
rm -f backend/test_*.py
rm -f backend/check_excel.py
rm -f backend/final_validation_test.py
find tests/ -name "*.pyc" -delete 2>/dev/null || true

# ===== 7. 删除构建和分发文件 =====
echo "🔨 清理构建文件..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/
rm -rf .eggs/

# ===== 8. 删除开发脚本 =====
echo "📜 清理开发脚本..."
rm -f install.sh
rm -f quick-deploy.sh
rm -f start.sh
rm -f stop.sh
rm -f verify.sh
rm -f optimize-docker.sh

# ===== 9. 删除多余的Dockerfile =====
echo "🐳 清理多余Docker文件..."
rm -f Dockerfile.optimized
rm -f Dockerfile.alpine
# 保留 Dockerfile 和 Dockerfile.full-optimized

# ===== 10. 删除临时和系统文件 =====
echo "🗑️ 清理临时文件..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true
find . -name "*.Zone.Identifier" -delete 2>/dev/null || true

# ===== 11. 删除IDE配置 =====
echo "⚙️ 清理IDE配置..."
rm -rf .vscode/
rm -rf .idea/
rm -rf *.sublime-*

# ===== 12. 删除多余的依赖文件 =====
echo "📋 清理多余依赖文件..."
rm -f backend/requirements.txt
rm -f backend/requirements-centos7.txt
rm -f backend/requirements-prod.txt
# 保留 backend/requirements-full-prod.txt

# ===== 13. 显示清理结果 =====
echo ""
echo "✅ 清理完成！当前仓库文件："
echo "🗂️ 保留的核心文件和目录："
find . -maxdepth 2 -type f | grep -v ".git" | sort

echo ""
echo "📊 仓库大小："
du -sh . 2>/dev/null || echo "无法计算大小"

echo ""
echo "🎯 建议接下来执行："
echo "1. git add -A"
echo "2. git commit -m 'cleanup: 彻底清理仓库，删除所有开发和临时文件'"
echo "3. git push"
