# 快速开始指南

欢迎使用融资租赁计算器！本指南将帮助您快速部署和使用系统。

## 🎯 选择部署方式

### 方式一：Docker部署 (推荐，最简单)

适合：想要快速体验或生产部署的用户

```bash
# 1. 克隆项目
git clone https://github.com/tyj1987/lease-calculator.git
cd lease-calculator

# 2. 一键Docker部署
chmod +x scripts/docker-deploy.sh
./scripts/docker-deploy.sh

# 3. 访问系统
# 打开浏览器访问: http://localhost
```

### 方式二：传统部署 (推荐开发者)

适合：需要自定义配置或开发的用户

```bash
# 1. 克隆项目
git clone https://github.com/tyj1987/lease-calculator.git
cd lease-calculator

# 2. 选择您的系统执行相应脚本

# Ubuntu/Debian 系统:
chmod +x scripts/deploy-ubuntu.sh
./scripts/deploy-ubuntu.sh

# CentOS/RHEL 系统:
chmod +x scripts/deploy-centos.sh  
./scripts/deploy-centos.sh

# Arch Linux 系统:
chmod +x scripts/deploy-arch.sh
./scripts/deploy-arch.sh

# 3. 访问系统
# 打开浏览器访问: http://您的服务器IP
```

### 方式三：手动部署 (推荐学习)

适合：想要了解每个步骤的用户

```bash
# 1. 环境准备
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. 克隆项目
git clone https://github.com/tyj1987/lease-calculator.git
cd lease-calculator

# 3. 设置Python环境
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 启动服务
python app.py

# 5. 访问系统
# 打开浏览器访问: http://localhost:5002
```

## 🚀 系统功能概览

### 主要功能

1. **💰 租赁计算**
   - 等额年金法 (等额本息)
   - 等额本金法
   - 平息法
   - 浮动利率法

2. **📊 数据导出**
   - Excel格式导出 (包含多个工作表)
   - JSON格式导出 (完全中文化)

3. **🔍 高级功能**
   - IRR内部收益率计算
   - 保证金冲抵处理
   - 敏感性分析

### 使用示例

1. **基本计算**：
   - 租赁本金：100万元
   - 年利率：8%
   - 租赁期限：36期
   - 支付频率：月付

2. **保证金处理**：
   - 保证金：5万元
   - 处理方式：尾期冲抵

3. **结果导出**：
   - 点击"导出Excel"获得详细报表
   - 点击"导出JSON"获得结构化数据

## 🔧 常用配置

### 环境变量配置

创建 `.env` 文件进行自定义配置：

```bash
# 服务配置
PORT=5002
SECRET_KEY=your-secret-key

# 日志配置  
LOG_LEVEL=INFO
LOG_FILE=logs/lease-calculator.log
```

### Nginx反向代理 (生产环境)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🐛 常见问题

### Q1: 端口占用怎么办？

```bash
# 查看占用端口的进程
sudo netstat -tulpn | grep :5002

# 终止进程
sudo kill -9 <进程ID>

# 或者修改配置使用其他端口
export PORT=5003
```

### Q2: 权限问题？

```bash
# 修复文件权限
chmod +x scripts/*.sh
chown -R $USER:$USER .
```

### Q3: Python依赖安装失败？

```bash
# 升级pip
pip install --upgrade pip

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### Q4: Docker容器无法启动？

```bash
# 查看容器日志
docker-compose logs

# 重新构建
docker-compose down
docker-compose up -d --build
```

## 📞 获取帮助

- **项目地址**: https://github.com/tyj1987/lease-calculator
- **API文档**: 查看 `docs/API.md`
- **问题反馈**: 提交GitHub Issues
- **邮箱联系**: tuoyongjun1987@qq.com

## 🎉 下一步

系统部署成功后，您可以：

1. 📖 阅读 [API文档](docs/API.md) 了解接口详情
2. 🧪 运行测试确保功能正常：`python -m pytest tests/`
3. 🚀 配置生产环境的HTTPS和域名
4. 📊 集成到您的业务系统中

祝您使用愉快！🎯
