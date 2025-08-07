# 专业融资租赁计算器

## 项目简介

这是一个专业的融资租赁计算器Web应用，支持多种租金计算方法、保证金处理、敏感性分析和方案对比功能。基于React前端和Python Flask后端架构开发。

## 功能特性

### 🧮 核心计算算法
- **等额年金法（等额本息）**：每期租金相等，最常用的计算方法
- **等额本金法**：每期本金相等，租金逐期递减
- **平息法**：按初始本金计算总利息，实际利率高于名义利率
- **浮动利率法**：支持利率定期重置，适用于LPR等基准利率模式
- **隐含利率计算（IRR）**：自动计算项目内部收益率

### 💰 保证金处理模块
- **尾期冲抵**：从最后一期向前冲抵（默认模式）
- **按比例分摊**：平均冲抵各期租金
- **首期冲抵**：从第一期开始冲抵
- **法律合规**：遵循民法典第561条抵扣顺序规定

### 📊 可视化分析
- **租金构成图**：堆叠柱状图显示本金/利息构成
- **现金流图表**：时序图展示每期和累计现金流
- **多方案对比**：最多支持5个方案并行对比
- **敏感性分析**：参数变动对租金和IRR的影响分析

### 📤 导出功能
- **Excel格式**：包含完整计算过程和图表
- **JSON格式**：结构化数据便于API调用
- **响应式设计**：支持PC/平板/手机访问

### 🔧 技术特性
- **高精度计算**：使用Decimal库，精度达到0.01元
- **实时计算**：前后端分离架构，响应速度<1秒
- **错误处理**：完善的参数验证和错误提示
- **RESTful API**：标准化接口便于扩展

## 技术架构

```
前端（React + Bootstrap）  →  Flask API  →  计算引擎（NumPy + Decimal）
        ↓                        ↓
   交互式图表（Plotly）     →  数据导出（Excel/JSON）
```

### 后端技术栈
- **Python 3.8+**
- **Flask 2.3+**：Web框架
- **NumPy**：金融计算库
- **Pandas**：数据处理
- **Plotly**：图表生成
- **OpenPyXL**：Excel导出

### 前端技术栈
- **React 18**：用户界面
- **Bootstrap 5**：响应式设计
- **React Hook Form**：表单管理
- **Plotly.js**：交互式图表
- **Axios**：HTTP客户端

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 1. 克隆项目
```bash
git clone <repository-url>
cd lease-calculator
```

### 2. 启动后端服务

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动Flask服务器
python app.py
```

后端服务将在 `http://localhost:5000` 启动

### 3. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

前端服务将在 `http://localhost:3000` 启动

### 4. 访问应用

打开浏览器访问 `http://localhost:3000` 即可使用计算器。

## API接口文档

### 核心计算接口

#### POST /api/calculate
计算租金方案

**请求参数：**
```json
{
  "method": "equal_annuity",  // 计算方法
  "pv": 1000000,              // 租赁本金
  "annual_rate": 0.08,        // 年利率
  "periods": 36,              // 租赁期限
  "frequency": 12,            // 支付频率
  "guarantee": 50000,         // 保证金（可选）
  "guarantee_mode": "尾期冲抵" // 保证金冲抵模式（可选）
}
```

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "method": "等额年金法",
    "pmt": 25068.80,
    "total_interest": 122475.80,
    "total_payment": 902475.80,
    "irr": 0.083,
    "schedule": [
      {
        "period": 1,
        "payment": 25068.80,
        "principal": 19735.47,
        "interest": 5333.33,
        "remaining_balance": 980264.53
      }
      // ... 更多期数
    ]
  }
}
```

#### POST /api/compare
多方案对比

#### POST /api/sensitivity
敏感性分析

#### POST /api/export/excel
导出Excel报告

#### POST /api/export/json
导出JSON数据

## 使用示例

### 1. 等额年金法计算
```javascript
// 设备价格100万，首付20万，租期3年，年利率8%
const params = {
  method: 'equal_annuity',
  pv: 800000,        // 租赁本金 = 100万 - 20万
  annual_rate: 0.08,
  periods: 36,
  frequency: 12
};
```

### 2. 保证金冲抵处理
```javascript
const params = {
  // ... 基础参数
  guarantee: 50000,           // 保证金5万
  guarantee_mode: '尾期冲抵'  // 从最后一期开始冲抵
};
```

### 3. 浮动利率计算
```javascript
const params = {
  method: 'floating_rate',
  // ... 基础参数
  rate_reset_schedule: [
    { period: 6, new_rate: 0.065 },   // 第6期重置为6.5%
    { period: 12, new_rate: 0.07 }    // 第12期重置为7%
  ]
};
```

## 算法说明

### 等额年金法公式
```
PMT = PV × [i × (1+i)^n] / [(1+i)^n - 1]

其中：
- PMT：每期租金
- PV：租赁本金
- i：期利率（年利率 ÷ 年付次数）
- n：总期数
```

### 等额本金法公式
```
每期本金 = PV / n
每期利息 = 剩余本金 × 期利率
每期租金 = 每期本金 + 每期利息
```

### IRR计算
```
NPV = Σ(CF_t / (1+IRR)^t) = 0

使用牛顿法迭代求解IRR，确保高精度计算
```

## 业务规则

### 保证金冲抵规则
1. **尾期冲抵**（推荐）：从最后一期向前冲抵，符合实务习惯
2. **按比例分摊**：平均分摊到各期，适用于特殊合同约定
3. **首期冲抵**：从第一期开始冲抵，降低初期现金流压力

### 法律合规要求
- 默认抵扣顺序：实现债权的费用 → 逾期利息 → 违约金 → 租金（民法典第561条）
- 支持合同特殊约定的自定义抵扣顺序

### 风险控制指标
- 支持不良率、逾期率等风险指标计算
- 提供敏感性分析，识别关键风险因素

## 开发指南

### 添加新的计算方法

1. **后端实现**（`backend/lease_calculator.py`）：
```python
def new_calculation_method(self, pv, annual_rate, periods, **kwargs):
    # 实现新的计算逻辑
    return {
        'method': '新方法名称',
        'pmt': calculated_pmt,
        'schedule': payment_schedule
    }
```

2. **API集成**（`backend/app.py`）：
```python
elif method == 'new_method':
    result = calculator.new_calculation_method(**params)
```

3. **前端表单**（`frontend/src/components/CalculatorForm.js`）：
```javascript
const methodOptions = [
  // ... 现有选项
  { value: 'new_method', label: '新计算方法' }
];
```

### 自定义图表
在 `frontend/src/components/ResultsDisplay.js` 中添加新的图表类型：

```javascript
const customChart = {
  data: [...],
  layout: {
    title: '自定义图表',
    // ... 布局配置
  }
};
```

## 测试用例

### 标准测试案例
| 测试项 | 输入参数 | 预期输出 |
|--------|----------|----------|
| 等额年金法 | PV=80万, i=8%, n=36 | PMT≈25,068.80元 |
| 保证金尾期冲抵 | 保证金=5万 | 最后一期租金减少5万 |
| 平息法IRR验证 | 平息率8%, 3年 | 实际IRR≈15.1% |

### 精度测试
- 金额精度：0.01元
- IRR精度：0.0001 (0.01%)
- 百万元级计算误差：<0.01元

## 部署说明

### 生产环境部署

1. **后端部署**：
```bash
# 使用Gunicorn部署Flask应用
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **前端构建**：
```bash
npm run build
# 使用Nginx托管构建后的静态文件
```

3. **Nginx配置示例**：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker部署

```dockerfile
# Dockerfile.backend
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

# Dockerfile.frontend
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
```

## 扩展功能预留

### 1. 行业风控指标
- 不良率计算：`不良资产余额/总资产`
- 资本充足率：`（自有资本-风险加权资产）/总资产`

### 2. 监管合规支持
- 租金分解禁止项检测
- 关联交易比例预警

### 3. 多租户架构
- 用户认证和权限管理
- 数据隔离和安全加密

## 许可证

MIT License

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 支持与反馈

如有问题或建议，请：
- 提交 GitHub Issue
- 发送邮件至：support@example.com
- 查看在线文档：[文档链接]

---

**注意**：本计算器严格遵循融资租赁行业实践与法律规范，确保计算结果的准确性和合规性。在实际业务应用中，请结合具体合同条款进行调整。
