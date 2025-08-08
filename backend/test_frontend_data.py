#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试实际前端传递的导出数据
"""

import requests
import json
import time

# 模拟前端可能传递的不完整数据（这可能是问题所在）
incomplete_data = {
    # 只有计算结果，缺少原始参数
    "pmt": 31336.37,
    "total_interest": 128109.14,
    "irr": 0.052945,
    "schedule": [
        {"period": 1, "payment": 31336.37, "principal": 24669.70, "interest": 6666.67, "remaining_balance": 975330.30}
    ],
    "guarantee_offset": {
        "total_offset": 50000.00,
        "unused_guarantee": 0.00,
        "offset_details": [{"period": 36, "offset_amount": 31336.37, "remaining_payment": 0.00}],
    },
}


def test_incomplete_export():
    """测试不完整数据的导出"""
    print("🧪 测试不完整数据的导出...")

    print(f"传递的数据: {json.dumps(incomplete_data, indent=2, ensure_ascii=False)}")

    # 测试Excel导出
    print("\n📊 测试Excel导出（不完整数据）...")
    response = requests.post(
        "http://127.0.0.1:5002/api/export/excel", json=incomplete_data, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        print("✅ Excel导出成功")
        with open("incomplete_test_export.xlsx", "wb") as f:
            f.write(response.content)
        print("✅ 文件保存为 incomplete_test_export.xlsx")
    else:
        print(f"❌ Excel导出失败: {response.text}")

    # 测试JSON导出
    print("\n📄 测试JSON导出（不完整数据）...")
    response = requests.post(
        "http://127.0.0.1:5002/api/export/json", json=incomplete_data, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        print("✅ JSON导出成功")
        with open("incomplete_test_export.json", "wb") as f:
            f.write(response.content)

        # 检查内容
        try:
            json_content = json.loads(response.content.decode("utf-8"))
            print("✅ JSON内容预览:")
            print("基本信息:", json_content.get("基本信息", {}))
            print("计算结果:", json_content.get("计算结果", {}))
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
    else:
        print(f"❌ JSON导出失败: {response.text}")


def monitor_requests():
    """监控实际的API请求"""
    print("🔍 请在浏览器中进行导出操作，我将监控终端输出...")
    print("按 Ctrl+C 结束监控")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n监控结束")


if __name__ == "__main__":
    print("🚀 测试前端数据传递问题")
    print("=" * 50)

    test_incomplete_export()

    print("\n" + "=" * 50)
    print("💡 如果基本信息显示为0，说明前端没有传递原始计算参数")
    print("   需要修复前端传递完整数据，或者后端从计算结果中推导参数")
