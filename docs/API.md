# API 文档

## 基础信息

- **基础URL**: `http://your-domain.com/api`
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: 无需认证 (可根据需要添加)

## 通用响应格式

### 成功响应
```json
{
  "status": "success",
  "data": {...},
  "timestamp": "2025-08-06T20:00:00.000000"
}
```

### 错误响应
```json
{
  "status": "error", 
  "message": "错误信息",
  "timestamp": "2025-08-06T20:00:00.000000"
}
```

## 接口列表

### 1. 健康检查

**接口地址**: `GET /api/health`

**请求参数**: 无

**响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T20:00:00.000000",
  "version": "1.0.0"
}
```

### 2. 租赁计算

**接口地址**: `POST /api/calculate`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| method | string | 是 | 计算方法: equal_annuity, equal_principal, flat_rate, floating_rate |
| pv | number | 是 | 租赁本金 (元) |
| annual_rate | number | 是 | 年利率 (小数形式，如0.08表示8%) |
| periods | integer | 是 | 租赁期限 (期) |
| frequency | integer | 否 | 支付频率 (默认12，月付) |
| guarantee | number | 否 | 保证金金额 (元) |
| guarantee_mode | string | 否 | 保证金处理方式 (默认"尾期冲抵") |
| years | number | 否 | 租赁年限 (平息法需要) |
| rate_reset_schedule | array | 否 | 利率重置计划 (浮动利率法需要) |

**请求示例**:
```json
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

**响应示例**:
```json
{
  "status": "success",
  "data": {
    "method": "equal_annuity",
    "pmt": 31336.37,
    "total_interest": 128109.14,
    "total_payment": 1128109.32,
    "irr": 0.052945,
    "schedule": [
      {
        "period": 1,
        "payment": 31336.37,
        "principal": 24669.70,
        "interest": 6666.67,
        "remaining_balance": 975330.30
      }
    ],
    "guarantee_offset": {
      "total_offset": 50000.0,
      "unused_guarantee": 0.0,
      "offset_details": [...]
    },
    "export_data": {...}
  },
  "timestamp": "2025-08-06T20:00:00.000000"
}
```

### 3. 反向计算

**接口地址**: `POST /api/reverse_calculate`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_pmt | number | 是 | 目标每期租金 |
| annual_rate | number | 是 | 年利率 |
| periods | integer | 是 | 租赁期限 |
| frequency | integer | 否 | 支付频率 (默认12) |

**请求示例**:
```json
{
  "target_pmt": 30000,
  "annual_rate": 0.08,
  "periods": 36,
  "frequency": 12
}
```

### 4. Excel导出

**接口地址**: `POST /api/export/excel`

**请求参数**: 计算结果对象 (与calculate接口的响应data部分相同)

**响应**: Excel文件流

**Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

### 5. JSON导出

**接口地址**: `POST /api/export/json`

**请求参数**: 计算结果对象

**响应**: JSON文件流

**Content-Type**: `application/json; charset=utf-8`

**响应示例**:
```json
{
  "导出信息": {
    "导出时间": "2025-08-06 20:00:00",
    "导出格式": "JSON",
    "系统版本": "融资租赁计算器 v1.0.0"
  },
  "基本信息": {
    "计算方法": "等额年金法(等额本息)",
    "租赁本金": "¥1,000,000.00",
    "年利率": "8.0000%",
    "租赁期限": "36期",
    "支付频率": "月付",
    "保证金": "¥50,000.00",
    "保证金处理方式": "尾期冲抵"
  },
  "计算结果": {
    "每期租金": "¥31,336.37",
    "总利息": "¥128,109.14", 
    "总支付额": "¥1,128,109.32",
    "内部收益率(IRR)": "5.2945%"
  },
  "详细数据": {
    "还款计划表": [...],
    "保证金冲抵明细": [...]
  }
}
```

## 错误代码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 接口不存在 |
| 405 | 请求方法不允许 |
| 500 | 服务器内部错误 |

## 使用示例

### Python 请求示例

```python
import requests
import json

# 计算租赁
url = "http://localhost:5002/api/calculate"
payload = {
    "method": "equal_annuity",
    "pv": 1000000,
    "annual_rate": 0.08,
    "periods": 36,
    "frequency": 12
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    result = response.json()
    print(f"每期租金: {result['data']['pmt']}")
else:
    print(f"错误: {response.text}")

# 导出Excel
if response.status_code == 200:
    export_url = "http://localhost:5002/api/export/excel"
    export_response = requests.post(export_url, json=result['data'])
    
    if export_response.status_code == 200:
        with open('lease_calculation.xlsx', 'wb') as f:
            f.write(export_response.content)
        print("Excel文件导出成功")
```

### JavaScript 请求示例

```javascript
// 使用fetch API
const calculateLease = async () => {
  const payload = {
    method: 'equal_annuity',
    pv: 1000000,
    annual_rate: 0.08,
    periods: 36,
    frequency: 12
  };

  try {
    const response = await fetch('/api/calculate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (result.status === 'success') {
      console.log('每期租金:', result.data.pmt);
    } else {
      console.error('计算失败:', result.message);
    }
  } catch (error) {
    console.error('请求失败:', error);
  }
};
```

### curl 请求示例

```bash
# 计算租赁
curl -X POST http://localhost:5002/api/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "method": "equal_annuity",
    "pv": 1000000,
    "annual_rate": 0.08,
    "periods": 36,
    "frequency": 12
  }'

# 健康检查
curl http://localhost:5002/api/health
```

## 注意事项

1. **数值精度**: 所有金额计算保留2位小数
2. **利率格式**: 年利率使用小数形式，如8%应传入0.08
3. **期数限制**: 建议期数不超过600期(50年)
4. **并发限制**: 单个IP每分钟最多100次请求
5. **数据大小**: 单次请求数据不超过1MB
6. **超时时间**: 接口超时时间为30秒

## 更新日志

### v1.0.0 (2025-08-06)
- 初始API版本发布
- 支持基本的租赁计算功能
- 支持Excel和JSON导出
- 完整的中文字段映射
