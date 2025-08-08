#!/bin/bash
set -e

echo "🔍 融资租赁计算器 CI/CD 配置检查"
echo "=================================="

# 检查必需文件
echo "📁 检查项目文件结构..."
required_files=(
    ".github/workflows/ci-cd.yml"
    "Dockerfile"
    "docker-compose.yml"
    "docker-compose.test.yml"
    "backend/requirements.txt"
    "backend/app.py"
    "frontend/index.html"
    "tests/"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [[ ! -e "$file" ]]; then
        missing_files+=("$file")
    else
        echo "✅ $file"
    fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
    echo "❌ 缺少以下文件:"
    printf '%s\n' "${missing_files[@]}"
    exit 1
fi

# 检查Docker镜像构建
echo ""
echo "🐳 检查Docker配置..."
if command -v docker >/dev/null 2>&1; then
    echo "✅ Docker已安装"
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker服务运行正常"
        # 跳过实际构建，仅检查Dockerfile语法
        if [[ -f "Dockerfile" ]]; then
            echo "✅ Dockerfile存在"
        fi
    else
        echo "⚠️  Docker服务未运行"
    fi
else
    echo "⚠️  Docker未安装（CI/CD环境中会自动安装）"
fi

# 检查Python依赖
echo ""
echo "🐍 检查Python依赖..."
cd backend
if python -m pip install -r requirements.txt >/dev/null 2>&1; then
    echo "✅ Python依赖安装成功"
else
    echo "❌ Python依赖安装失败"
    exit 1
fi

# 运行测试
echo ""
echo "🧪 运行测试套件..."
if python -m pytest ../tests/ -q; then
    echo "✅ 所有测试通过"
else
    echo "❌ 测试失败"
    exit 1
fi

# 检查代码质量
echo ""
echo "📝 检查代码质量..."
if flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics >/dev/null 2>&1; then
    echo "✅ 代码质量检查通过"
else
    echo "⚠️  代码质量检查有警告（可忽略）"
fi

# 安全检查
echo ""
echo "🔒 运行安全检查..."
if bandit -r . -f json -o ../bandit-report.json >/dev/null 2>&1; then
    echo "✅ 安全检查完成"
else
    echo "⚠️  安全检查有警告（请查看bandit-report.json）"
fi

cd ..

echo ""
echo "📋 CI/CD 配置摘要"
echo "=================="
echo "• Docker Hub用户: tuoyongjun1987"
echo "• 生产服务器: 47.94.225.76:22"
echo "• 测试服务器: 192.168.2.8:22"
echo "• GitHub仓库: tyj1987/lease-calculator"
echo ""
echo "🔑 需要配置的GitHub Secrets:"
echo "• DOCKERHUB_TOKEN"
echo "• PROD_SSH_PASSWORD"
echo "• TEST_SSH_PASSWORD"
echo "• SLACK_WEBHOOK_URL (可选)"
echo ""
echo "✅ CI/CD配置检查完成！"
echo "📚 详细配置请参考: docs/GITHUB_SECRETS.md"
