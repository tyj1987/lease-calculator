# 自动部署环境配置说明

## 测试环境 (192.168.2.8)
- **用途**: 用于测试最新的main分支代码
- **触发条件**: main分支推送时自动部署
- **Docker镜像**: tuoyongjun1987/lease-calculator:main-{commit-sha}
- **服务端口**: 8080
- **配置文件**: docker-compose.test.yml

## 生产环境 (47.94.225.76)  
- **用途**: 稳定的生产服务
- **触发条件**: main分支推送或手动触发
- **Docker镜像**: tuoyongjun1987/lease-calculator:latest
- **服务端口**: 80
- **配置文件**: docker-compose.yml

## 所需的GitHub Secrets

为了正常部署，需要在GitHub仓库设置中配置以下Secrets：

### SSH认证
```
TEST_SSH_PASSWORD=测试服务器root密码
PROD_SSH_PASSWORD=生产服务器root密码
```

### Docker Hub认证（已配置）
```
DOCKERHUB_USERNAME=tuoyongjun1987
DOCKERHUB_TOKEN=已配置的Docker Hub访问令牌
```

### 通知配置（可选）
```
SLACK_WEBHOOK_URL=Slack通知webhook地址
```

## 部署流程验证

### ✅ 已验证的功能
1. GitHub Actions工作流自动触发
2. Docker镜像构建和推送到Docker Hub
3. 部署脚本逻辑正确性
4. 分支条件判断准确性

### ⏳ 需要服务器环境的功能
1. SSH连接到目标服务器
2. Docker服务在目标服务器上运行
3. 应用服务启动和健康检查

## 下一步建议

1. **配置服务器环境**:
   - 确保测试服务器(192.168.2.8)可访问
   - 在服务器上安装Docker和docker-compose
   - 配置SSH访问权限

2. **GitHub Secrets配置**:
   - 添加SSH密码到GitHub Secrets
   - 测试SSH连接

3. **部署配置文件**:
   - 创建docker-compose.test.yml
   - 确保端口和环境变量配置正确

4. **监控和日志**:
   - 设置部署成功/失败通知
   - 配置应用日志收集
