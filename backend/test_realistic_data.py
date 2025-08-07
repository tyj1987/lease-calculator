#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用完整的还款计划测试参数推导
"""

import requests
import json

# 模拟完整的还款计划数据（前端实际会传递的）
realistic_data = {
    "pmt": 31336.37,
    "total_interest": 128109.14,
    "total_payment": 1128109.32,
    "irr": 0.052945,
    "method": "等额年金法",
    "schedule": [
        {"period": 1, "payment": 31336.37, "principal": 24669.70, "interest": 6666.67, "remaining_balance": 975330.30},
        {"period": 2, "payment": 31336.37, "principal": 24834.17, "interest": 6502.20, "remaining_balance": 950496.13},
        {"period": 3, "payment": 31336.37, "principal": 24999.73, "interest": 6336.64, "remaining_balance": 925496.40},
        # ... 这里应该有36期的完整数据，为简化只显示前几期
        {"period": 35, "payment": 31336.37, "principal": 30922.69, "interest": 413.68, "remaining_balance": 31128.67},
        {"period": 36, "payment": 31336.37, "principal": 31128.67, "interest": 207.70, "remaining_balance": 0.0}
    ],
    "guarantee_offset": {
        "total_offset": 50000.0,
        "unused_guarantee": 0.0,
        "offset_details": [
            {"period": 36, "offset_amount": 31336.37, "remaining_payment": 0.00},
            {"period": 35, "offset_amount": 18663.63, "remaining_payment": 12672.74}
        ]
    }
}

def test_realistic_export():
    """测试真实数据的导出"""
    print("📊 测试Excel导出（真实数据）...")
    response = requests.post('http://127.0.0.1:5002/api/export/excel',
                           json=realistic_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print("✅ Excel导出成功")
        with open('realistic_test_export.xlsx', 'wb') as f:
            f.write(response.content)
        print("✅ 文件保存为 realistic_test_export.xlsx")
    else:
        print(f"❌ Excel导出失败: {response.text}")
    
    print("\n📄 测试JSON导出（真实数据）...")
    response = requests.post('http://127.0.0.1:5002/api/export/json',
                           json=realistic_data,
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        print("✅ JSON导出成功")
        with open('realistic_test_export.json', 'wb') as f:
            f.write(response.content)
        
        try:
            json_content = json.loads(response.content.decode('utf-8'))
            print("✅ JSON内容预览:")
            print("基本信息:", json_content.get('基本信息', {}))
            print("计算结果:", json_content.get('计算结果', {}))
            schedule_count = len(json_content.get('详细数据', {}).get('还款计划表', []))
            print(f"还款计划表: 共{schedule_count}期数据")
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
    else:
        print(f"❌ JSON导出失败: {response.text}")

if __name__ == "__main__":
    print("🚀 测试真实数据的参数推导")
    print("=" * 50)
    test_realistic_export()
    print("\n🎉 测试完成!")
