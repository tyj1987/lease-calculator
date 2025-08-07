# 测试配置文件
import os

# 测试数据库路径 (如果使用数据库)
TEST_DATABASE_URI = 'sqlite:///:memory:'

# 测试环境配置
TESTING = True
DEBUG = True

# 禁用CSRF保护 (测试环境)
WTF_CSRF_ENABLED = False

# 测试用的SECRET_KEY
SECRET_KEY = 'test-secret-key-do-not-use-in-production'

# 日志级别
LOG_LEVEL = 'DEBUG'
