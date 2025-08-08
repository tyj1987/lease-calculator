#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通过实际API调用获得完整数据并测试导出
"""

import requests
import json


def test_complete_calculation_flow():
    """测试完整的计算->导出流程"""
    print("🔢 首先进行完整的租赁计算...")

    # 使用典型的计算参数
    calc_data = {
        "pv": 1000000,  # 租赁本金100万
        "annual_rate": 0.08,  # 年利率8%
        "periods": 36,  # 36期
        "frequency": 12,  # 月付(12期/年)
        "guarantee": 50000,  # 保证金5万
        "guarantee_mode": "尾期冲抵",  # 尾期冲抵
        "method": "equal_annuity",  # 等额年金法
    }

    print(f"📋 计算参数: 本金¥{calc_data['pv']:,}, 利率{calc_data['annual_rate']:.1%}, {calc_data['periods']}期")

    # 调用计算API
    response = requests.post(
        "http://127.0.0.1:5002/api/calculate", json=calc_data, headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        response_data = response.json()
        calc_result = response_data.get("data", {})  # 提取data字段
        print("✅ 计算成功")
        print(f"🔍 计算结果预览:")
        print(f"  - 每期租金: ¥{calc_result.get('pmt', 0):,.2f}")
        print(f"  - 总利息: ¥{calc_result.get('total_interest', 0):,.2f}")
        print(f"  - IRR: {calc_result.get('irr', 0):.4%}")
        print(f"  - 还款计划: {len(calc_result.get('schedule', []))}期")

        print("\n📊 测试Excel导出...")
        export_response = requests.post(
            "http://127.0.0.1:5002/api/export/excel", json=calc_result, headers={"Content-Type": "application/json"}
        )

        if export_response.status_code == 200:
            print("✅ Excel导出成功")
            with open("complete_flow_export.xlsx", "wb") as f:
                f.write(export_response.content)
            print("✅ 文件保存为 complete_flow_export.xlsx")
        else:
            print(f"❌ Excel导出失败: {export_response.text}")

        print("\n📄 测试JSON导出...")
        json_response = requests.post(
            "http://127.0.0.1:5002/api/export/json", json=calc_result, headers={"Content-Type": "application/json"}
        )

        if json_response.status_code == 200:
            print("✅ JSON导出成功")
            with open("complete_flow_export.json", "wb") as f:
                f.write(json_response.content)

            try:
                json_content = json.loads(json_response.content.decode("utf-8"))
                print("✅ JSON内容验证:")
                basic_info = json_content.get("基本信息", {})
                calc_results = json_content.get("计算结果", {})

                print("📋 基本信息:")
                for key, value in basic_info.items():
                    print(f"  - {key}: {value}")

                print("📊 计算结果:")
                for key, value in calc_results.items():
                    print(f"  - {key}: {value}")

                schedule_count = len(json_content.get("详细数据", {}).get("还款计划表", []))
                print(f"📅 还款计划表: 共{schedule_count}期数据")

                # 验证保证金冲抵
                offset_info = json_content.get("详细数据", {}).get("保证金冲抵明细", [])
                if offset_info:
                    print(f"💰 保证金冲抵: {len(offset_info)}项明细")

            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
        else:
            print(f"❌ JSON导出失败: {json_response.text}")

    else:
        print(f"❌ 计算失败: {response.text}")


if __name__ == "__main__":
    print("🚀 测试完整的计算->导出流程")
    print("=" * 60)
    test_complete_calculation_flow()
    print("\n🎉 完整测试完成!")
