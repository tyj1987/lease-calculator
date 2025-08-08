# 融资租赁计算器 - Makefile
# 简化开发和部署流程

.PHONY: help install test lint format clean build run docker-build docker-run deploy

# 默认目标
help:
	@echo "融资租赁计算器 - 可用命令："
	@echo "  help          显示此帮助信息"
	@echo "  install       安装依赖"
	@echo "  test          运行所有测试"
	@echo "  test-unit     运行单元测试"
	@echo "  test-e2e      运行端到端测试"
	@echo "  test-perf     运行性能测试"
	@echo "  lint          代码质量检查"
	@echo "  format        代码格式化"
	@echo "  clean         清理临时文件"
	@echo "  build         构建项目"
	@echo "  run           运行开发服务器"
	@echo "  docker-build  构建Docker镜像"
	@echo "  docker-run    运行Docker容器"
	@echo "  deploy        部署到生产环境"

# 安装依赖
install:
	cd backend && pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 isort bandit safety locust

# 运行所有测试
test:
	cd backend && python -m pytest ../tests/ -v --cov=. --cov-report=html --cov-report=xml

# 运行单元测试
test-unit:
	cd backend && python -m pytest ../tests/test_calculator.py ../tests/test_api.py -v

# 运行端到端测试
test-e2e:
	cd backend && python -m pytest ../tests/test_e2e.py -v -m e2e

# 运行性能测试
test-perf:
	cd backend && python -m pytest ../tests/test_performance.py -v -m performance

# 代码质量检查
lint:
	cd backend && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	cd backend && flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	cd backend && bandit -r . -f json -o bandit-report.json || true
	cd backend && safety check -r requirements.txt

# 代码格式化
format:
	cd backend && black .
	cd backend && isort .

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -name "bandit-report.json" -delete

# 构建项目
build: clean test lint
	@echo "✅ 项目构建完成"

# 运行开发服务器
run:
	cd backend && python app.py

# 构建Docker镜像
docker-build:
	docker build -t tuoyongjun1987/lease-calculator:latest .
	docker build -t tuoyongjun1987/lease-calculator:dev .

# 运行Docker容器
docker-run:
	docker-compose up -d
	@echo "🐳 Docker容器已启动"
	@echo "访问地址: http://localhost"

# 停止Docker容器
docker-stop:
	docker-compose down

# 查看Docker日志
docker-logs:
	docker-compose logs -f

# 部署到生产环境
deploy: build docker-build
	@echo "🚀 开始部署..."
	@if [ -f scripts/docker-deploy.sh ]; then \
		chmod +x scripts/docker-deploy.sh && ./scripts/docker-deploy.sh; \
	else \
		echo "部署脚本不存在"; \
	fi

# 健康检查
health-check:
	@echo "🔍 执行健康检查..."
	@curl -f http://localhost:5002/api/health || echo "❌ 健康检查失败"
	@curl -f http://localhost/ || echo "❌ 前端服务异常"

# 生成测试报告
test-report: test
	@echo "📊 测试报告已生成："
	@echo "  HTML覆盖率报告: htmlcov/index.html"
	@echo "  XML覆盖率报告: coverage.xml"

# 安全扫描
security-scan:
	cd backend && bandit -r . -f json -o bandit-report.json
	cd backend && safety check -r requirements.txt
	@echo "🔒 安全扫描完成"

# 性能基准测试
benchmark:
	@echo "🏃 运行性能基准测试..."
	cd backend && python -c "
import time
from lease_calculator import LeaseCalculator

calc = LeaseCalculator()
start = time.time()
for i in range(1000):
    calc.equal_annuity_method(1000000, 0.08, 36, 12)
end = time.time()
print(f'1000次计算耗时: {end-start:.2f}秒')
print(f'平均每次: {(end-start)*1000:.2f}毫秒')
"

# 生成API文档
docs:
	@echo "📚 生成API文档..."
	@echo "API文档位置: docs/API.md"

# 完整的CI/CD流程
ci: install test lint security-scan
	@echo "✅ CI流程完成"

# 本地开发环境设置
dev-setup: install
	cd backend && python -m venv venv
	@echo "虚拟环境已创建，请运行: source backend/venv/bin/activate"

# 版本发布
release:
	@echo "📦 准备发布版本..."
	@git tag -a v$(shell date +%Y%m%d-%H%M) -m "Release version $(shell date +%Y%m%d-%H%M)"
	@echo "版本标签已创建，推送到远程: git push origin --tags"
