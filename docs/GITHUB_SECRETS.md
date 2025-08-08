# GitHub Secrets 配置指南

本项目需要在GitHub仓库中配置以下Secrets，用于CI/CD流程的自动化部署。

## � 必需的Secrets配置

### 1. Docker Hub 认证

```
DOCKERHUB_TOKEN
```
**值**: `dckr_pat_uOJQgE31jFixm5bB_9-bF5O_In0`
**用途**: Docker Hub个人访问令牌，用于推送Docker镜像

### 2. 生产服务器SSH认证

```
PROD_SSH_PASSWORD
```
**值**: `Tyj_98729`
**用途**: 生产服务器SSH密码 (47.94.225.76)

### 3. 测试服务器SSH认证

```
TEST_SSH_PASSWORD
```
**值**: `tyj198729`
**用途**: 测试服务器SSH密码 (192.168.2.8)

### 4. 通知配置（可选）

```
SLACK_WEBHOOK_URL
```
**值**: 您的Slack Webhook URL
**用途**: 部署完成后发送通知

## �️ 配置步骤

1. 进入GitHub仓库页面
2. 点击 `Settings` → `Secrets and variables` → `Actions`
3. 点击 `New repository secret`
4. 输入Secret名称和对应的值
5. 点击 `Add secret` 保存

## 🔒 安全说明

- **DOCKERHUB_TOKEN**: Docker Hub个人访问令牌，用于自动推送镜像
- **PROD_SSH_PASSWORD**: 生产服务器密码，仅用于自动部署
- **TEST_SSH_PASSWORD**: 测试服务器密码，仅用于测试环境部署
- 这些Secrets在GitHub Actions中是加密存储的，不会在日志中显示

## 🌐 服务器信息

### 生产服务器
- **IP**: 47.94.225.76
- **用户名**: root
- **端口**: 22
- **部署目录**: /opt/lease-calculator

### 测试服务器
- **IP**: 192.168.2.8
- **用户名**: root  
- **端口**: 22
- **部署目录**: /opt/lease-calculator-test

## 📋 CI/CD 流程

1. **推送到main分支** → 自动部署到生产环境
2. **推送到develop分支** → 自动部署到测试环境
3. **Pull Request** → 仅运行测试，不部署
4. **手动触发** → 可选择是否部署到生产环境

## 🔄 部署验证

每次部署后，系统会自动进行健康检查：
- 生产环境: `http://47.94.225.76/api/health`
- 测试环境: `http://192.168.2.8:8080/api/health`

如果健康检查失败，生产环境会自动回滚到上一个版本。
