#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查生成的Excel文件内容
"""

import pandas as pd


def check_excel_content():
    """检查Excel文件内容"""
    print("📊 检查Excel文件内容...")

    try:
        # 读取所有sheet
        excel_file = pd.ExcelFile("test_export.xlsx")
        print(f"✅ Excel文件包含以下工作表: {excel_file.sheet_names}")

        # 检查基本信息
        if "基本信息" in excel_file.sheet_names:
            basic_info = pd.read_excel(excel_file, sheet_name="基本信息")
            print("\n📋 基本信息工作表:")
            print(basic_info.to_string(index=False))

        # 检查还款计划表
        if "还款计划表" in excel_file.sheet_names:
            schedule = pd.read_excel(excel_file, sheet_name="还款计划表")
            print(f"\n📅 还款计划表: 共{len(schedule)}期")
            print("前5期数据:")
            print(schedule.head().to_string(index=False))
            print("后5期数据:")
            print(schedule.tail().to_string(index=False))

        # 检查保证金相关信息
        if "保证金冲抵详情" in excel_file.sheet_names:
            offset_details = pd.read_excel(excel_file, sheet_name="保证金冲抵详情")
            print(f"\n💰 保证金冲抵详情: 共{len(offset_details)}期")
            print(offset_details.to_string(index=False))

        if "保证金汇总" in excel_file.sheet_names:
            guarantee_summary = pd.read_excel(excel_file, sheet_name="保证金汇总")
            print(f"\n💰 保证金汇总信息:")
            print(guarantee_summary.to_string(index=False))

    except Exception as e:
        print(f"❌ 检查Excel文件失败: {e}")


if __name__ == "__main__":
    check_excel_content()
