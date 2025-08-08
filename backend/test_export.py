#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导出功能的脚本
"""

import requests
import json

# 测试数据
test_data = {
    "method": "equal_annuity",
    "pv": 1000000,
    "annual_rate": 0.08,
    "periods": 36,
    "frequency": 12,
    "guarantee": 50000,
    "guarantee_mode": "尾期冲抵",
}


def test_calculate():
    """测试计算功能"""
    print("🧮 测试计算功能...")

    response = requests.post(
        "http://127.0.0.1:5002/api/calculate",
        json=test_data,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ 计算成功")
        print(f"每期租金: {result['data'].get('pmt', 0):.2f}")
        print(f"总利息: {result['data'].get('total_interest', 0):.2f}")
        print(f"IRR: {result['data'].get('irr', 0)*100:.4f}%")
        return result["data"]
    else:
        print(f"❌ 计算失败: {response.text}")
        return None


def test_excel_export(calculation_result):
    """测试Excel导出"""
    print("\n📊 测试Excel导出...")

    # 合并计算结果和原始参数
    export_data = calculation_result.copy()
    export_data.update(test_data)

    response = requests.post(
        "http://127.0.0.1:5002/api/export/excel",
        json=export_data,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        print("✅ Excel导出成功")
        print(f"文件类型: {response.headers.get('Content-Type')}")
        print(f"文件大小: {len(response.content)} bytes")

        # 保存文件
        with open("test_export.xlsx", "wb") as f:
            f.write(response.content)
        print("✅ Excel文件已保存为 test_export.xlsx")
    else:
        print(f"❌ Excel导出失败: {response.text}")


def test_json_export(calculation_result):
    """测试JSON导出"""
    print("\n📄 测试JSON导出...")

    # 合并计算结果和原始参数
    export_data = calculation_result.copy()
    export_data.update(test_data)

    response = requests.post(
        "http://127.0.0.1:5002/api/export/json",
        json=export_data,
        headers={"Content-Type": "application/json"},
    )

    if response.status_code == 200:
        print("✅ JSON导出成功")

        # 保存并显示文件内容
        with open("test_export.json", "wb") as f:
            f.write(response.content)

        # 读取并解析JSON内容
        try:
            json_content = json.loads(response.content.decode("utf-8"))
            print("✅ JSON文件已保存为 test_export.json")
            print("\n📋 JSON内容预览:")
            print("基本信息:", json_content.get("基本信息", {}))
            print("计算结果:", json_content.get("计算结果", {}))
            if "详细数据" in json_content and "还款计划表" in json_content["详细数据"]:
                schedule_count = len(json_content["详细数据"]["还款计划表"])
                print(f"还款计划表: 共{schedule_count}期数据")
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
    else:
        print(f"❌ JSON导出失败: {response.text}")


if __name__ == "__main__":
    print("🚀 开始测试融资租赁计算器导出功能")
    print("=" * 50)

    # 测试计算
    calc_result = test_calculate()

    if calc_result:
        # 测试导出
        test_excel_export(calc_result)
        test_json_export(calc_result)

    print("\n" + "=" * 50)
    print("🎉 测试完成!")
