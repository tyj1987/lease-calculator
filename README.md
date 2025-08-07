# 融资租赁计算器 (Lease Calculator)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 项目简介

融资租赁计算器是一个专业的金融计算工具，支持多种租赁计算方法，提供完整的还款计划生成和数据导出功能。系统采用前后端分离架构，前端使用React构建用户界面，后端使用Flask提供REST API服务。

### ✨ 主要特性

- 🧮 **多种计算方法**: 等额年金法、等额本金法、平息法、浮动利率法
- 💰 **保证金处理**: 支持尾期冲抵、分期冲抵等多种处理方式  
- 📊 **数据可视化**: 还款计划图表、敏感性分析图
- 📁 **数据导出**: Excel和JSON格式导出，完全中文化
- 🔍 **IRR计算**: 内部收益率自动计算
- 📈 **敏感性分析**: 利率、期限敏感性测试
- 🌐 **响应式设计**: 支持桌面和移动端访问

## 📋 系统要求

### 最低要求
- Python 3.8+
- Node.js 16+ (仅开发环境需要)
- 2GB RAM
- 1GB 磁盘空间

### 推荐配置
- Python 3.10+
- 4GB+ RAM
- SSD存储
- Linux/Windows/macOS

## 🛠️ 技术栈

### 后端技术
- **Flask 2.3+**: Web框架
- **NumPy**: 数值计算
- **Pandas**: 数据处理
- **OpenPyXL**: Excel文件处理
- **Matplotlib/Plotly**: 图表生成

### 前端技术  
- **React 18**: UI框架
- **Bootstrap**: UI组件库
- **Chart.js**: 图表库
- **Axios**: HTTP客户端

## � 快速开始

### 方式一：一键部署脚本 (推荐)

```bash
# 下载项目
git clone https://github.com/your-username/lease-calculator.git
cd lease-calculator

# 运行一键部署脚本
chmod +x deploy.sh
./deploy.sh
```

### 方式二：手动部署

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/lease-calculator.git
cd lease-calculator
```

#### 2. 后端部署
```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python app.py
```

#### 3. 访问应用
打开浏览器访问: http://localhost:5002

## 🐳 Docker部署

### 使用Docker Compose (推荐)

```bash
# 克隆项目
git clone https://github.com/your-username/lease-calculator.git
cd lease-calculator

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 使用Docker

```bash
# 构建镜像
docker build -t lease-calculator .

# 运行容器
docker run -d -p 5002:5002 --name lease-calc lease-calculator

# 查看日志
docker logs lease-calc
```

## 🌐 不同Linux发行版部署指南

### Ubuntu/Debian 系统

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install -y python3 python3-pip python3-venv git nginx

# 克隆项目
git clone https://github.com/your-username/lease-calculator.git
cd lease-calculator

# 运行Ubuntu部署脚本
chmod +x scripts/deploy-ubuntu.sh
./scripts/deploy-ubuntu.sh
```

### CentOS/RHEL 系统

```bash
# 更新系统
sudo yum update -y

# 安装依赖
sudo yum install -y python3 python3-pip git nginx

# 克隆项目
git clone https://github.com/your-username/lease-calculator.git
cd lease-calculator

# 运行CentOS部署脚本  
chmod +x scripts/deploy-centos.sh
./scripts/deploy-centos.sh
```

### Arch Linux 系统

```bash
# 更新系统
sudo pacman -Syu

# 安装依赖
sudo pacman -S python python-pip git nginx

# 克隆项目
git clone https://github.com/your-username/lease-calculator.git
cd lease-calculator  

# 运行Arch部署脚本
chmod +x scripts/deploy-arch.sh
./scripts/deploy-arch.sh
```

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件：
```bash
# Flask配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
PORT=5002

# 数据库配置 (可选)
DATABASE_URL=sqlite:///lease_calculator.db

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/lease-calculator.log
```

### Nginx配置

参考 `config/nginx.conf` 进行Nginx反向代理配置。

### 系统服务配置

参考 `config/lease-calculator.service` 配置systemd服务。

## 📊 API文档

### 计算接口

```http
POST /api/calculate
Content-Type: application/json

{
  "method": "equal_annuity",
  "pv": 1000000,
  "annual_rate": 0.08,
  "periods": 36,
  "frequency": 12,
  "guarantee": 50000,
  "guarantee_mode": "尾期冲抵"
}
```

### 导出接口

```http
# Excel导出
POST /api/export/excel
Content-Type: application/json

# JSON导出  
POST /api/export/json
Content-Type: application/json
```

更多API详情请参考 [API文档](docs/API.md)

## 🧪 测试

```bash
# 运行后端测试
cd backend
python -m pytest tests/

# 运行前端测试 (如果有)
cd frontend  
npm test
```

## � 项目结构

```
lease-calculator/
├── backend/                 # 后端代码
│   ├── app.py              # Flask主应用
│   ├── lease_calculator.py # 核心计算逻辑
│   ├── requirements.txt    # Python依赖
│   └── venv/              # Python虚拟环境
├── frontend/              # 前端静态文件
│   ├── static/            # CSS/JS资源
│   └── index.html         # 主页面
├── config/                # 配置文件
│   ├── nginx.conf         # Nginx配置
│   └── lease-calculator.service  # systemd服务
├── scripts/               # 部署脚本
│   ├── deploy.sh          # 通用部署脚本
│   ├── deploy-ubuntu.sh   # Ubuntu部署
│   ├── deploy-centos.sh   # CentOS部署
│   └── deploy-arch.sh     # Arch部署
├── docs/                  # 文档
├── logs/                  # 日志文件
├── docker-compose.yml     # Docker Compose配置
├── Dockerfile            # Docker镜像配置  
└── README.md             # 项目说明
```

## 🚀 生产环境部署

### 使用Gunicorn + Nginx

1. **安装Gunicorn**
```bash
pip install gunicorn
```

2. **启动Gunicorn服务**
```bash
cd backend
gunicorn -c gunicorn_conf.py app:app
```

3. **配置Nginx反向代理**
```bash
sudo cp config/nginx.conf /etc/nginx/sites-available/lease-calculator
sudo ln -s /etc/nginx/sites-available/lease-calculator /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

4. **设置系统服务**
```bash
sudo cp config/lease-calculator.service /etc/systemd/system/
sudo systemctl enable lease-calculator
sudo systemctl start lease-calculator
```

## 🔒 安全配置

- 修改默认SECRET_KEY
- 配置HTTPS证书
- 设置防火墙规则
- 定期更新依赖包

## 🐛 故障排查

### 常见问题

1. **端口占用错误**
   ```bash
   # 查看端口使用情况
   sudo netstat -tulpn | grep :5002
   
   # 终止占用进程
   sudo kill -9 <PID>
   ```

2. **Python依赖问题**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt --force-reinstall
   ```

3. **权限问题**
   ```bash
   # 修复文件权限
   chmod +x *.sh
   chown -R $USER:$USER .
   ```

### 日志查看

```bash
# 查看应用日志
tail -f logs/lease-calculator.log

# 查看系统服务日志
sudo journalctl -u lease-calculator -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/error.log
```

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2025-08-06)
- ✨ 初始版本发布
- ✅ 完整的租赁计算功能
- ✅ 中文化导出功能
- ✅ Docker支持
- ✅ 多Linux发行版部署支持

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目维护者: [脱永军]
- 邮箱: your.email@example.com
- 项目地址: https://github.com/your-username/lease-calculator

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

⭐ 如果这个项目对您有帮助，请给我们一个星标！
