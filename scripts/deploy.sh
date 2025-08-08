#!/bin/bash

# 融资租赁计算器 - 通用一键部署脚本
# 支持 Ubuntu/Debian, CentOS/RHEL, Arch Linux

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        error "无法检测操作系统类型"
    fi
    
    log "检测到操作系统: $OS $VER"
}

# 检查依赖
check_dependencies() {
    log "检查系统依赖..."
    
    # 检查Python版本
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d" " -f2 | cut -d"." -f1,2)
        log "Python版本: $PYTHON_VERSION"
        
        if [ "$(printf '%s\n' "3.8" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.8" ]; then
            error "需要Python 3.8+，当前版本: $PYTHON_VERSION"
        fi
    else
        error "未找到Python3"
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        error "未找到pip3"
    fi
}

# 安装系统依赖
install_system_deps() {
    log "安装系统依赖..."
    
    case "$OS" in
        *"Ubuntu"*|*"Debian"*)
            log "使用APT包管理器..."
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv git nginx curl
            ;;
        *"CentOS"*|*"Red Hat"*|*"Rocky"*|*"AlmaLinux"*)
            log "使用YUM/DNF包管理器..."
            if command -v dnf &> /dev/null; then
                sudo dnf install -y python3 python3-pip git nginx curl
            else
                sudo yum install -y python3 python3-pip git nginx curl
            fi
            ;;
        *"Arch"*)
            log "使用Pacman包管理器..."
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm python python-pip git nginx curl
            ;;
        *)
            warn "未识别的操作系统，尝试通用安装..."
            ;;
    esac
}

# 设置Python环境
setup_python_env() {
    log "设置Python虚拟环境..."
    
    cd backend
    
    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    log "安装Python依赖..."
    pip install -r requirements.txt
    
    log "Python环境设置完成"
}

# 配置Nginx
setup_nginx() {
    log "配置Nginx..."
    
    # 备份原配置
    if [ -f /etc/nginx/sites-available/default ]; then
        sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
    fi
    
    # 复制配置文件
    sudo cp config/nginx.conf /etc/nginx/sites-available/lease-calculator
    
    # 启用站点
    if [ -d /etc/nginx/sites-enabled ]; then
        sudo ln -sf /etc/nginx/sites-available/lease-calculator /etc/nginx/sites-enabled/
        sudo rm -f /etc/nginx/sites-enabled/default
    else
        # CentOS/RHEL风格
        sudo cp config/nginx.conf /etc/nginx/conf.d/lease-calculator.conf
    fi
    
    # 测试配置
    if sudo nginx -t; then
        log "Nginx配置测试通过"
        sudo systemctl restart nginx
        sudo systemctl enable nginx
    else
        error "Nginx配置测试失败"
    fi
}

# 设置系统服务
setup_systemd() {
    log "设置systemd服务..."
    
    # 更新服务文件中的路径
    sed "s|/path/to/your|$(pwd)|g" config/lease-calculator.service > /tmp/lease-calculator.service
    
    # 复制服务文件
    sudo cp /tmp/lease-calculator.service /etc/systemd/system/
    
    # 重载systemd并启动服务
    sudo systemctl daemon-reload
    sudo systemctl enable lease-calculator
    sudo systemctl start lease-calculator
    
    # 检查服务状态
    if sudo systemctl is-active --quiet lease-calculator; then
        log "服务启动成功"
    else
        error "服务启动失败"
    fi
}

# 配置防火墙
setup_firewall() {
    log "配置防火墙..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian - ufw
        sudo ufw allow 22/tcp
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
        sudo ufw --force enable
        log "UFW防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL - firewalld
        sudo firewall-cmd --permanent --add-service=http
        sudo firewall-cmd --permanent --add-service=https
        sudo firewall-cmd --permanent --add-service=ssh
        sudo firewall-cmd --reload
        log "Firewalld防火墙配置完成"
    else
        warn "未检测到防火墙管理工具，请手动配置防火墙规则"
    fi
}

# 健康检查
health_check() {
    log "执行健康检查..."
    
    # 等待服务启动
    sleep 10
    
    # 检查端口
    if netstat -tuln | grep -q ":5002"; then
        log "应用端口5002正常监听"
    else
        error "应用端口5002未监听"
    fi
    
    # 检查HTTP响应
    if curl -f -s http://localhost:5002/ > /dev/null; then
        log "HTTP健康检查通过"
    else
        warn "HTTP健康检查失败，请检查应用状态"
    fi
    
    # 检查Nginx
    if curl -f -s http://localhost/ > /dev/null; then
        log "Nginx反向代理正常"
    else
        warn "Nginx反向代理可能有问题"
    fi
}

# 显示部署信息
show_info() {
    echo ""
    echo "======================================="
    echo -e "${GREEN}🎉 部署完成！${NC}"
    echo "======================================="
    echo ""
    echo "🌐 访问地址:"
    echo "   HTTP:  http://$(hostname -I | awk '{print $1}')"
    echo "   本地:  http://localhost"
    echo ""
    echo "📊 服务状态:"
    echo "   应用服务: $(sudo systemctl is-active lease-calculator)"
    echo "   Nginx:   $(sudo systemctl is-active nginx)"
    echo ""
    echo "📁 重要路径:"
    echo "   应用目录: $(pwd)"
    echo "   日志文件: $(pwd)/logs/lease-calculator.log"
    echo "   配置文件: $(pwd)/config/"
    echo ""
    echo "🔧 管理命令:"
    echo "   启动服务: sudo systemctl start lease-calculator"
    echo "   停止服务: sudo systemctl stop lease-calculator"
    echo "   重启服务: sudo systemctl restart lease-calculator"
    echo "   查看日志: tail -f logs/lease-calculator.log"
    echo ""
    echo "🔒 安全提醒:"
    echo "   - 请修改默认的SECRET_KEY"
    echo "   - 建议配置HTTPS证书"
    echo "   - 定期更新系统和依赖"
    echo ""
}

# 主函数
main() {
    log "开始部署融资租赁计算器..."
    
    # 检查是否为root用户
    if [ "$EUID" -eq 0 ]; then
        error "请不要使用root用户运行此脚本"
    fi
    
    # 检查是否在项目根目录
    if [ ! -f "README.md" ] || [ ! -d "backend" ]; then
        error "请在项目根目录运行此脚本"
    fi
    
    detect_os
    check_dependencies
    install_system_deps
    setup_python_env
    setup_nginx
    setup_systemd
    setup_firewall
    health_check
    show_info
    
    log "部署完成！"
}

# 错误处理
trap 'error "部署过程中发生错误，脚本已终止"' ERR

# 执行主函数
main "$@"
