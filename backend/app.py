"""
Flask API服务器
提供融资租赁计算的RESTful API接口
"""

import os
from flask import Flask, request, jsonify, send_file
from werkzeug.exceptions import BadRequest, HTTPException
from flask_cors import CORS
import json
import io
import base64
from datetime import datetime
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # 使用非GUI后端
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import logging
from logging.handlers import RotatingFileHandler

from lease_calculator import LeaseCalculator

# 设置前端构建目录
FRONTEND_BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))

app = Flask(__name__, static_folder=FRONTEND_BUILD_DIR, static_url_path="")
CORS(app)  # 允许跨域请求

# 配置日志
if not app.debug:
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler("logs/lease-calculator.log", maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("融资租赁计算器启动")

# 创建计算器实例
calculator = LeaseCalculator()


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"})


# 字段映射表 - 英文到中文
FIELD_MAPPING = {
    # 基本信息字段
    "method": "计算方法",
    "pv": "租赁本金(元)",
    "annual_rate": "年利率",
    "periods": "租赁期限(期)",
    "frequency": "支付频率",
    "pmt": "每期租金(元)",
    "total_interest": "总利息(元)",
    "total_payment": "总支付额(元)",
    "irr": "内部收益率(IRR)",
    "flat_rate": "平息年利率",
    "actual_irr": "实际年利率(IRR)",
    "guarantee": "保证金(元)",
    "guarantee_mode": "保证金处理方式",
    # 还款计划字段
    "period": "期数",
    "payment": "租金(元)",
    "principal": "本金(元)",
    "interest": "利息(元)",
    "remaining_balance": "剩余本金(元)",
    "rate": "当期利率",
    # 保证金冲抵字段
    "offset_amount": "冲抵金额(元)",
    "remaining_payment": "冲抵后租金(元)",
    "unused_guarantee": "未用保证金(元)",
    "total_offset": "总冲抵金额(元)",
    # 计算方法映射
    "equal_annuity": "等额年金法(等额本息)",
    "equal_principal": "等额本金法",
    "flat_rate_method": "平息法",
    "floating_rate": "浮动利率法",
    # 保证金处理模式
    "尾期冲抵": "尾期冲抵",
    "按比例分摊": "按比例分摊",
    "首期冲抵": "首期冲抵",
}


def format_currency(value):
    """格式化货币显示"""
    if isinstance(value, (int, float)):
        return f"¥{value:,.2f}"
    return value


def format_percentage(value):
    """格式化百分比显示"""
    if isinstance(value, (int, float)):
        return f"{value*100:.4f}%"
    return value


def extract_missing_params(data):
    """从计算结果中提取或推导缺失的参数"""
    # 如果有export_data，直接使用
    if "export_data" in data:
        return data["export_data"]

    # 否则尝试从其他信息推导
    extracted = {}

    # 从还款计划推导参数
    if "schedule" in data and data["schedule"]:
        schedule = data["schedule"]
        extracted["periods"] = len(schedule)

        # 从第一期推导本金（通过累计本金）
        if len(schedule) > 0:
            total_principal = sum(item.get("principal", 0) for item in schedule)
            extracted["pv"] = total_principal

        # 从利息计算推导年利率（粗略估算）
        if len(schedule) > 1 and "pv" in extracted:
            first_interest = schedule[0].get("interest", 0)
            first_balance = schedule[0].get("remaining_balance", 0) + schedule[0].get("principal", 0)
            if first_balance > 0:
                monthly_rate = first_interest / first_balance
                extracted["annual_rate"] = monthly_rate * 12
                extracted["frequency"] = 12  # 假设月付

    # 从方法名推导
    if "method" in data:
        extracted["method"] = data["method"]

    # 从保证金信息推导
    if "guarantee_offset" in data:
        offset_info = data["guarantee_offset"]
        if "total_offset" in offset_info:
            extracted["guarantee"] = offset_info["total_offset"]

    return extracted


def translate_result_fields(data):
    """将英文字段翻译为中文，并格式化数值"""
    if isinstance(data, dict):
        translated = {}
        for key, value in data.items():
            # 获取中文字段名
            cn_key = FIELD_MAPPING.get(key, key)

            # 特殊格式化处理
            if key in [
                "pv",
                "pmt",
                "total_interest",
                "total_payment",
                "payment",
                "principal",
                "interest",
                "remaining_balance",
                "offset_amount",
                "remaining_payment",
                "guarantee",
                "unused_guarantee",
                "total_offset",
            ]:
                translated[cn_key] = format_currency(value)
            elif key in ["annual_rate", "irr", "actual_irr", "flat_rate", "rate"]:
                translated[cn_key] = format_percentage(value)
            elif key == "method" and isinstance(value, str):
                translated[cn_key] = FIELD_MAPPING.get(value, value)
            elif isinstance(value, list):
                translated[cn_key] = [translate_result_fields(item) for item in value]
            elif isinstance(value, dict):
                translated[cn_key] = translate_result_fields(value)
            else:
                translated[cn_key] = value

        return translated
    elif isinstance(data, list):
        return [translate_result_fields(item) for item in data]
    else:
        return data


# 设置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


@app.route("/api/calculate", methods=["POST"])
def calculate_lease():
    """
    核心计算接口
    支持多种计算方法：等额年金法、等额本金法、平息法、浮动利率法
    """
    try:
        # 检查JSON格式并捕获BadRequest
        try:
            data = request.get_json()
        except BadRequest:
            return jsonify({"error": "请求体不是有效的JSON格式"}), 400
            
        if data is None:
            return jsonify({"error": "请求体不是有效的JSON格式"}), 400

        # 验证必要参数
        required_params = ["method", "pv", "annual_rate", "periods"]
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"缺少必要参数: {param}"}), 400

        method = data["method"]
        try:
            pv = float(data["pv"])
            annual_rate = float(data["annual_rate"])
            periods = int(data["periods"])
            frequency = int(data.get("frequency", 12))  # 默认月付
        except (ValueError, TypeError, KeyError) as e:
            return jsonify({"error": f"参数类型错误: {str(e)}"}), 400

        result = None

        try:
            if method == "equal_annuity":
                result = calculator.equal_annuity_method(pv, annual_rate, periods, frequency)
            elif method == "equal_principal":
                result = calculator.equal_principal_method(pv, annual_rate, periods, frequency)
            elif method == "flat_rate":
                years = float(data.get("years", periods / frequency))
                result = calculator.flat_rate_method(pv, annual_rate, years, frequency)
            elif method == "floating_rate":
                rate_reset_schedule = data.get("rate_reset_schedule", [])
                result = calculator.floating_rate_method(pv, annual_rate, periods, rate_reset_schedule, frequency)
            else:
                return jsonify({"error": f"不支持的计算方法: {method}"}), 400
        except (ValueError, TypeError) as e:
            return jsonify({"error": f"参数错误: {str(e)}"}), 400

        # 处理保证金冲抵
        guarantee = float(data.get("guarantee", 0))
        guarantee_mode = data.get("guarantee_mode", "尾期冲抵")

        if guarantee > 0:
            offset_result = calculator.apply_guarantee_offset(result["schedule"], guarantee, guarantee_mode)
            result["guarantee_offset"] = offset_result

        # 计算IRR
        if "schedule" in result:
            cash_flows = [-pv] + [item["payment"] for item in result["schedule"]]
            result["irr"] = calculator.calculate_irr(cash_flows, frequency)

        # 添加原始数据到结果中，用于导出
        result["export_data"] = {
            "method": method,
            "pv": pv,
            "annual_rate": annual_rate,
            "periods": periods,
            "frequency": frequency,
            "guarantee": guarantee,
            "guarantee_mode": guarantee_mode,
        }


        return jsonify({"status": "success", "data": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/sensitivity_analysis", methods=["POST"])
def sensitivity_analysis_compat():
    """敏感性分析接口 - 重新设计的完整实现"""
    try:
        data = request.get_json()

        # 提取基础参数
        pv = float(data.get("pv", 1000000))
        annual_rate = float(data.get("annual_rate", 0.08))
        periods = int(data.get("periods", 36))
        frequency = int(data.get("frequency", 12))
        method = data.get("method", "equal_annuity")

        # 提取敏感性参数
        rate_variation = float(data.get("rate_variation", 0.01))  # 利率变动幅度
        period_variation = int(data.get("period_variation", 6))  # 期限变动幅度
        pv_variation = float(data.get("pv_variation", 100000))  # 本金变动幅度

        # 计算基准值
        base_result = None
        if method == "equal_annuity":
            base_result = calculator.equal_annuity_method(pv, annual_rate, periods, frequency)
        elif method == "equal_principal":
            base_result = calculator.equal_principal_method(pv, annual_rate, periods, frequency)
        else:
            # 默认使用等额年金法
            base_result = calculator.equal_annuity_method(pv, annual_rate, periods, frequency)

        base_pmt = base_result["pmt"]

        # 计算IRR
        cash_flows = [-pv] + [base_pmt] * periods
        base_irr = calculator.calculate_irr(cash_flows, frequency)

        # 敏感性分析结果
        sensitivity_analysis = []

        # 1. 利率敏感性分析
        rate_scenarios = [
            annual_rate - rate_variation,  # -变动幅度
            annual_rate - rate_variation / 2,  # -变动幅度/2
            annual_rate,  # 基准值
            annual_rate + rate_variation / 2,  # +变动幅度/2
            annual_rate + rate_variation,  # +变动幅度
        ]

        for rate in rate_scenarios:
            if rate > 0:  # 确保利率为正
                try:
                    if method == "equal_annuity":
                        result = calculator.equal_annuity_method(pv, rate, periods, frequency)
                    else:
                        result = calculator.equal_principal_method(pv, rate, periods, frequency)

                    pmt = result["pmt"]
                    change = rate - annual_rate
                    payment_change = pmt - base_pmt
                    change_rate = (payment_change / base_pmt) * 100 if base_pmt != 0 else 0

                    # 计算敏感度系数：租金变动率 / 利率变动率
                    rate_change_pct = (change / annual_rate) * 100 if annual_rate != 0 else 0
                    sensitivity = change_rate / rate_change_pct if rate_change_pct != 0 else 0

                    sensitivity_analysis.append(
                        {
                            "parameter": "年利率",
                            "change": change,
                            "payment": pmt,
                            "payment_change": payment_change,
                            "change_rate": change_rate,
                            "sensitivity": sensitivity,
                        }
                    )
                except Exception as e:
                    continue

        # 2. 期限敏感性分析
        period_scenarios = [
            max(1, periods - period_variation),  # -变动期数
            max(1, periods - period_variation // 2),  # -变动期数/2
            periods,  # 基准值
            periods + period_variation // 2,  # +变动期数/2
            periods + period_variation,  # +变动期数
        ]

        for period in period_scenarios:
            try:
                if method == "equal_annuity":
                    result = calculator.equal_annuity_method(pv, annual_rate, period, frequency)
                else:
                    result = calculator.equal_principal_method(pv, annual_rate, period, frequency)

                pmt = result["pmt"]
                change = period - periods
                payment_change = pmt - base_pmt
                change_rate = (payment_change / base_pmt) * 100 if base_pmt != 0 else 0

                # 计算敏感度系数
                period_change_pct = (change / periods) * 100 if periods != 0 else 0
                sensitivity = change_rate / period_change_pct if period_change_pct != 0 else 0

                sensitivity_analysis.append(
                    {
                        "parameter": "租赁期数",
                        "change": change,
                        "payment": pmt,
                        "payment_change": payment_change,
                        "change_rate": change_rate,
                        "sensitivity": sensitivity,
                    }
                )
            except Exception as e:
                continue

        # 3. 本金敏感性分析
        pv_scenarios = [
            max(1000, pv - pv_variation),  # -变动金额
            max(1000, pv - pv_variation / 2),  # -变动金额/2
            pv,  # 基准值
            pv + pv_variation / 2,  # +变动金额/2
            pv + pv_variation,  # +变动金额
        ]

        for pv_test in pv_scenarios:
            try:
                if method == "equal_annuity":
                    result = calculator.equal_annuity_method(pv_test, annual_rate, periods, frequency)
                else:
                    result = calculator.equal_principal_method(pv_test, annual_rate, periods, frequency)

                pmt = result["pmt"]
                change = pv_test - pv
                payment_change = pmt - base_pmt
                change_rate = (payment_change / base_pmt) * 100 if base_pmt != 0 else 0

                # 计算敏感度系数
                pv_change_pct = (change / pv) * 100 if pv != 0 else 0
                sensitivity = change_rate / pv_change_pct if pv_change_pct != 0 else 0

                sensitivity_analysis.append(
                    {
                        "parameter": "租赁本金",
                        "change": change,
                        "payment": pmt,
                        "payment_change": payment_change,
                        "change_rate": change_rate,
                        "sensitivity": sensitivity,
                    }
                )
            except Exception as e:
                continue

        # 计算基础信息
        total_interest = base_pmt * periods - pv

        return jsonify(
            {
                "status": "success",
                "sensitivity_analysis": sensitivity_analysis,
                "base_payment": base_pmt,
                "base_irr": base_irr,
                "base_total_interest": total_interest,
                "data": {
                    "base_result": {"pmt": base_pmt, "irr": base_irr, "total_interest": total_interest},
                    "sensitivity_results": sensitivity_analysis,
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        app.logger.error(f"敏感性分析错误: {str(e)}")
        return jsonify({"status": "error", "message": f"敏感性分析失败: {str(e)}", "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/compare", methods=["POST"])
def compare_schemes():
    """多方案对比接口"""
    try:
        data = request.get_json()
        schemes = data["schemes"]

        if len(schemes) > 5:
            return jsonify({"error": "最多支持5个方案对比"}), 400

        results = []

        for i, scheme in enumerate(schemes):
            method = scheme["method"]
            params = scheme["params"]

            # 提取各方法需要的基础参数
            base_params = {
                "pv": float(params["pv"]),
                "annual_rate": float(params["annual_rate"]),
                "periods": int(params["periods"]),
                "frequency": int(params.get("frequency", 12)),
            }

            if method == "equal_annuity":
                result = calculator.equal_annuity_method(**base_params)
            elif method == "equal_principal":
                result = calculator.equal_principal_method(**base_params)
            elif method == "flat_rate":
                # 平息法需要years参数
                flat_params = base_params.copy()
                flat_params["years"] = float(params.get("years", params["periods"] / params.get("frequency", 12)))
                result = calculator.flat_rate_method(
                    flat_params["pv"], flat_params["annual_rate"], flat_params["years"], flat_params["frequency"]
                )
            else:
                continue

            # 处理保证金冲抵
            guarantee = float(params.get("guarantee", 0))
            guarantee_mode = params.get("guarantee_mode", "尾期冲抵")

            if guarantee > 0 and "schedule" in result:
                offset_result = calculator.apply_guarantee_offset(result["schedule"], guarantee, guarantee_mode)
                result["guarantee_offset"] = offset_result

            # 计算IRR
            if "pmt" in result:
                # 等额年金法和平息法有固定的pmt
                cash_flows = [-base_params["pv"]] + [result["pmt"]] * base_params["periods"]
            else:
                # 等额本金法需要从schedule中提取每期payment
                cash_flows = [-base_params["pv"]] + [item["payment"] for item in result["schedule"]]

            result["irr"] = calculator.calculate_irr(cash_flows, base_params["frequency"])
            result["scheme_name"] = scheme.get("name", f"方案{i+1}")
            result["method"] = method

            results.append(result)

        return jsonify({"status": "success", "data": results, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/charts/payment_structure", methods=["POST"])
def generate_payment_structure_chart():
    """生成租金构成图表"""
    try:
        data = request.get_json()
        schedule = data["schedule"]

        periods = [item["period"] for item in schedule]
        principals = [item["principal"] for item in schedule]
        interests = [item["interest"] for item in schedule]

        # 使用Plotly生成交互式图表
        fig = go.Figure(data=[go.Bar(name="本金", x=periods, y=principals), go.Bar(name="利息", x=periods, y=interests)])

        fig.update_layout(title="租金构成分析", xaxis_title="期数", yaxis_title="金额（元）", barmode="stack", template="plotly_white")

        # 转换为JSON
        chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)

        return jsonify({"status": "success", "chart": chart_json, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/charts/cash_flow", methods=["POST"])
def generate_cash_flow_chart():
    """生成现金流图表"""
    try:
        data = request.get_json()
        schedule = data["schedule"]
        initial_payment = float(data.get("initial_payment", 0))

        periods = [0] + [item["period"] for item in schedule]
        cash_flows = [-initial_payment] + [item["payment"] for item in schedule]

        # 累计现金流
        cumulative_cf = []
        running_total = 0
        for cf in cash_flows:
            running_total += cf
            cumulative_cf.append(running_total)

        fig = go.Figure()

        # 每期现金流
        fig.add_trace(go.Scatter(x=periods, y=cash_flows, mode="lines+markers", name="每期现金流", line=dict(color="blue")))

        # 累计现金流
        fig.add_trace(
            go.Scatter(x=periods, y=cumulative_cf, mode="lines+markers", name="累计现金流", line=dict(color="red", dash="dash"))
        )

        fig.update_layout(
            title="现金流分析", xaxis_title="期数", yaxis_title="现金流（元）", template="plotly_white", hovermode="x unified"
        )

        chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)

        return jsonify({"status": "success", "chart": chart_json, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/export/excel", methods=["POST"])
def export_to_excel():
    """导出Excel报告"""
    try:
        data = request.get_json()

        # 提取缺失的参数
        missing_params = extract_missing_params(data)
        complete_data = {**data, **missing_params}

        # 创建Excel文件
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # 基本信息sheet
            basic_info = []

            # 计算方法
            if "method" in complete_data:
                method_cn = FIELD_MAPPING.get(complete_data["method"], complete_data["method"])
                basic_info.append(["计算方法", method_cn])

            # 基本参数
            if "pv" in complete_data:
                basic_info.append(["租赁本金", format_currency(complete_data["pv"])])
            if "annual_rate" in complete_data:
                basic_info.append(["年利率", format_percentage(complete_data["annual_rate"])])
            if "periods" in complete_data:
                basic_info.append(["租赁期限", f"{complete_data['periods']}期"])
            if "frequency" in complete_data:
                freq_map = {12: "月付", 4: "季付", 2: "半年付", 1: "年付"}
                freq_text = freq_map.get(complete_data["frequency"], f"{complete_data['frequency']}次/年")
                basic_info.append(["支付频率", freq_text])

            # 计算结果
            if "pmt" in complete_data:
                basic_info.append(["每期租金", format_currency(complete_data["pmt"])])
            if "total_interest" in complete_data:
                basic_info.append(["总利息", format_currency(complete_data["total_interest"])])
            if "total_payment" in complete_data:
                basic_info.append(["总支付额", format_currency(complete_data["total_payment"])])
            if "irr" in complete_data:
                basic_info.append(["内部收益率(IRR)", format_percentage(complete_data["irr"])])

            # 保证金信息
            if "guarantee" in complete_data and complete_data["guarantee"] > 0:
                basic_info.append(["保证金", format_currency(complete_data["guarantee"])])
            if "guarantee_mode" in complete_data:
                basic_info.append(["保证金处理方式", complete_data.get("guarantee_mode", "尾期冲抵")])
            elif "guarantee_offset" in complete_data:
                # 从保证金冲抵信息推导处理方式
                offset_details = complete_data["guarantee_offset"].get("offset_details", [])
                if offset_details:
                    # 检查冲抵模式：如果最后一期先冲抵，则是尾期冲抵
                    periods = [item["period"] for item in offset_details]
                    if periods and max(periods) in periods[:2]:  # 最大期数在前两个冲抵中
                        basic_info.append(["保证金处理方式", "尾期冲抵"])

            basic_info.append(["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

            basic_info_df = pd.DataFrame(basic_info, columns=["项目", "数值"])
            basic_info_df.to_excel(writer, sheet_name="基本信息", index=False)

            # 还款计划sheet - 使用中文列名
            if "schedule" in complete_data and complete_data["schedule"]:
                schedule_data = []
                for item in complete_data["schedule"]:
                    schedule_row = {
                        "期数": item.get("period", ""),
                        "租金(元)": format_currency(item.get("payment", 0)),
                        "本金(元)": format_currency(item.get("principal", 0)),
                        "利息(元)": format_currency(item.get("interest", 0)),
                        "剩余本金(元)": format_currency(item.get("remaining_balance", 0)),
                    }
                    # 如果有利率信息（浮动利率法）
                    if "rate" in item:
                        schedule_row["当期利率"] = format_percentage(item["rate"])
                    schedule_data.append(schedule_row)

                schedule_df = pd.DataFrame(schedule_data)
                schedule_df.to_excel(writer, sheet_name="还款计划表", index=False)

            # 保证金冲抵详情sheet - 使用中文列名
            if "guarantee_offset" in complete_data and "offset_details" in complete_data["guarantee_offset"]:
                offset_data = []
                for item in complete_data["guarantee_offset"]["offset_details"]:
                    offset_data.append(
                        {
                            "期数": item.get("period", ""),
                            "冲抵金额(元)": format_currency(item.get("offset_amount", 0)),
                            "冲抵后租金(元)": format_currency(item.get("remaining_payment", 0)),
                        }
                    )

                if offset_data:
                    offset_df = pd.DataFrame(offset_data)
                    offset_df.to_excel(writer, sheet_name="保证金冲抵详情", index=False)

                    # 保证金汇总信息
                    guarantee_summary = [
                        ["保证金总额", format_currency(complete_data.get("guarantee", 0))],
                        ["总冲抵金额", format_currency(complete_data["guarantee_offset"].get("total_offset", 0))],
                        ["未用保证金", format_currency(complete_data["guarantee_offset"].get("unused_guarantee", 0))],
                        ["处理方式", complete_data.get("guarantee_mode", "尾期冲抵")],
                    ]
                    guarantee_summary_df = pd.DataFrame(guarantee_summary, columns=["项目", "数值"])
                    guarantee_summary_df.to_excel(writer, sheet_name="保证金汇总", index=False)

        output.seek(0)

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f'融资租赁计算报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        )

    except Exception as e:
        app.logger.error(f"Excel导出错误: {str(e)}")
        return jsonify({"status": "error", "message": f"导出Excel文件失败: {str(e)}", "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/export/json", methods=["POST"])
def export_to_json():
    """导出JSON数据"""
    try:
        data = request.get_json()

        # 提取缺失的参数
        missing_params = extract_missing_params(data)
        complete_data = {**data, **missing_params}

        # 创建导出数据结构
        export_data = {
            "导出信息": {"导出时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "导出格式": "JSON", "系统版本": "融资租赁计算器 v1.0.0"},
            "基本信息": {},
            "计算结果": {},
            "详细数据": {},
        }

        # 基本信息
        if "method" in complete_data:
            method_cn = FIELD_MAPPING.get(complete_data["method"], complete_data["method"])
            export_data["基本信息"]["计算方法"] = method_cn
        if "pv" in complete_data:
            export_data["基本信息"]["租赁本金"] = format_currency(complete_data["pv"])
        if "annual_rate" in complete_data:
            export_data["基本信息"]["年利率"] = format_percentage(complete_data["annual_rate"])
        if "periods" in complete_data:
            export_data["基本信息"]["租赁期限"] = f"{complete_data['periods']}期"
        if "frequency" in complete_data:
            freq_map = {12: "月付", 4: "季付", 2: "半年付", 1: "年付"}
            freq_text = freq_map.get(complete_data["frequency"], f"{complete_data['frequency']}次/年")
            export_data["基本信息"]["支付频率"] = freq_text

        # 保证金信息
        if "guarantee" in complete_data and complete_data.get("guarantee", 0) > 0:
            export_data["基本信息"]["保证金"] = format_currency(complete_data["guarantee"])
        if "guarantee_mode" in complete_data:
            export_data["基本信息"]["保证金处理方式"] = complete_data.get("guarantee_mode", "尾期冲抵")
        elif "guarantee_offset" in complete_data:
            # 从保证金冲抵信息推导处理方式
            offset_details = complete_data["guarantee_offset"].get("offset_details", [])
            if offset_details:
                periods = [item["period"] for item in offset_details]
                if periods and max(periods) in periods[:2]:
                    export_data["基本信息"]["保证金处理方式"] = "尾期冲抵"

        # 计算结果
        if "pmt" in complete_data:
            export_data["计算结果"]["每期租金"] = format_currency(complete_data["pmt"])
        if "total_interest" in complete_data:
            export_data["计算结果"]["总利息"] = format_currency(complete_data["total_interest"])
        if "total_payment" in complete_data:
            export_data["计算结果"]["总支付额"] = format_currency(complete_data["total_payment"])
        if "irr" in complete_data:
            export_data["计算结果"]["内部收益率(IRR)"] = format_percentage(complete_data["irr"])
        if "actual_irr" in complete_data:
            export_data["计算结果"]["实际年利率"] = format_percentage(complete_data["actual_irr"])
        if "flat_rate" in complete_data:
            export_data["计算结果"]["平息年利率"] = format_percentage(complete_data["flat_rate"])

        # 还款计划表 - 使用中文字段名
        if "schedule" in complete_data and complete_data["schedule"]:
            schedule_list = []
            for item in complete_data["schedule"]:
                schedule_item = {
                    "期数": item.get("period", ""),
                    "租金": format_currency(item.get("payment", 0)),
                    "本金": format_currency(item.get("principal", 0)),
                    "利息": format_currency(item.get("interest", 0)),
                    "剩余本金": format_currency(item.get("remaining_balance", 0)),
                }
                # 如果有利率信息（浮动利率法）
                if "rate" in item:
                    schedule_item["当期利率"] = format_percentage(item["rate"])
                schedule_list.append(schedule_item)

            export_data["详细数据"]["还款计划表"] = schedule_list

        # 保证金冲抵详情 - 使用中文字段名
        if "guarantee_offset" in complete_data:
            guarantee_info = {
                "冲抵汇总": {
                    "保证金总额": format_currency(complete_data.get("guarantee", 0)),
                    "总冲抵金额": format_currency(complete_data["guarantee_offset"].get("total_offset", 0)),
                    "未用保证金": format_currency(complete_data["guarantee_offset"].get("unused_guarantee", 0)),
                    "处理方式": complete_data.get("guarantee_mode", "尾期冲抵"),
                }
            }

            if "offset_details" in complete_data["guarantee_offset"] and complete_data["guarantee_offset"]["offset_details"]:
                offset_list = []
                for item in complete_data["guarantee_offset"]["offset_details"]:
                    offset_list.append(
                        {
                            "期数": item.get("period", ""),
                            "冲抵金额": format_currency(item.get("offset_amount", 0)),
                            "冲抵后租金": format_currency(item.get("remaining_payment", 0)),
                        }
                    )
                guarantee_info["冲抵详情"] = offset_list

            export_data["详细数据"]["保证金处理"] = guarantee_info

        # 创建JSON文件
        output = io.BytesIO()
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        output.write(json_str.encode("utf-8"))
        output.seek(0)

        # 强制加charset=utf-8
        return send_file(
            output,
            mimetype="application/json; charset=utf-8",
            as_attachment=True,
            download_name=f'融资租赁计算数据_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
        )

    except Exception as e:
        app.logger.error(f"JSON导出错误: {str(e)}")
        return jsonify({"status": "error", "message": f"导出JSON文件失败: {str(e)}", "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/reverse_calculate", methods=["POST"])
def reverse_calculate():
    """反向计算接口 - 根据目标值推算利率或租金"""
    try:
        data = request.get_json()

        # 验证必要参数
        required_params = ["calculation_type", "method", "pv", "periods", "frequency"]
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"缺少必要参数: {param}"}), 400

        calculation_type = data["calculation_type"]
        method = data["method"]
        pv = float(data["pv"])
        periods = int(data["periods"])
        frequency = int(data["frequency"])
        guarantee = float(data.get("guarantee", 0))
        guarantee_mode = data.get("guarantee_mode", "尾期冲抵")

        result = None

        if calculation_type == "find_rate":
            # 根据目标租金推算年利率
            target_pmt = float(data["target_pmt"])
            result = calculator.reverse_calculate_rate(pv, target_pmt, periods, frequency, method)

        elif calculation_type == "find_irr":
            # 根据目标IRR推算租金
            target_irr = float(data["target_irr"])
            result = calculator.reverse_calculate_pmt(pv, target_irr, periods, frequency, method)

        else:
            return jsonify({"error": f"不支持的计算类型: {calculation_type}"}), 400

        # 添加保证金信息到结果中
        if guarantee > 0:
            result["guarantee"] = guarantee
            result["guarantee_mode"] = guarantee_mode

        return jsonify({"status": "success", "data": result, "timestamp": datetime.now().isoformat()})

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve), "timestamp": datetime.now().isoformat()}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}), 500
# 全局JSON解析错误处理



@app.route("/health", methods=["GET"])
def health_status():
    """健康检查端点"""
    return jsonify({"status": "healthy", "service": "融资租赁计算器", "version": "1.0.0", "timestamp": datetime.now().isoformat()})


# 前端页面路由
@app.route("/")
def serve_index():
    """提供前端主页"""
    # 读取index.html内容，确保DOCTYPE为大写
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            html = f.read()
        # 替换为大写DOCTYPE
        html = html.replace("<!doctype html>", "<!DOCTYPE html>")
        from flask import Response
        return Response(html, mimetype="text/html")
    return "前端页面不存在", 404


# 处理所有其他路由（SPA路由支持）
@app.route("/<path:path>")
def serve_spa_routes(path):
    """处理SPA路由和其他文件"""
    # API路径返回404
    if path.startswith("api/"):
        return jsonify({"error": "API endpoint not found"}), 404

    # health路径
    if path == "health":
        return health_status()

    # 特殊文件处理
    if path in ["favicon.ico", "manifest.json", "logo192.png", "logo512.png", "robots.txt"]:
        file_path = os.path.join(FRONTEND_BUILD_DIR, path)
        if os.path.exists(file_path):
            return send_file(file_path)
        elif path == "manifest.json":
            return jsonify(
                {
                    "short_name": "融资租赁计算器",
                    "name": "专业融资租赁计算器",
                    "start_url": "/",
                    "display": "standalone",
                    "theme_color": "#000000",
                    "background_color": "#ffffff",
                }
            )
        else:
            return "", 204

    # 检查文件是否存在
    file_path = os.path.join(FRONTEND_BUILD_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)

    # 默认返回index.html支持SPA路由
    return send_file(os.path.join(FRONTEND_BUILD_DIR, "index.html"))



# 捕获无效JSON等BadRequest异常，返回400
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({"error": "Invalid JSON or bad request"}), 400

# 捕获所有其他异常，优先处理HTTPException
@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify({"error": e.description}), e.code
    app.logger.error("Server Error: %s", (e))
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    # 对于静态文件404，不要覆盖路由处理
    return jsonify({"error": "Resource not found"}), 404


# 捕获无效JSON等BadRequest异常，返回400
@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({"error": "请求体不是有效的JSON格式", "message": str(e)}), 400


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5002))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
