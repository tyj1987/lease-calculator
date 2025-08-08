# 轻量版应用 - 可选导入重量级依赖
# app_lite.py - 优化版本，减少Docker镜像大小

import os
import io
import json
import base64
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, jsonify, request, send_file, render_template_string
from flask_cors import CORS, cross_origin
import numpy as np
import numpy_financial as npf
from dateutil.relativedelta import relativedelta

# 可选导入 - 如果没有安装则禁用相关功能
PANDAS_AVAILABLE = False
PLOTLY_AVAILABLE = False
MATPLOTLIB_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.utils import PlotlyJSONEncoder
    PLOTLY_AVAILABLE = True
except ImportError:
    px = go = PlotlyJSONEncoder = None

try:
    import matplotlib
    import matplotlib.pyplot as plt
    import seaborn as sns
    matplotlib.use('Agg')  # 使用非交互式后端
    plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    matplotlib = plt = sns = None

# Excel导出
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

# 导入核心计算模块
from lease_calculator import (
    LeaseCalculator,
    CALCULATION_METHODS,
    INTEREST_CALCULATION_METHODS,
    PMT_FREQUENCIES,
    GUARANTEE_DEPOSIT_METHODS,
    OFFSET_METHODS,
    FLOAT_RATE_METHODS,
)

app = Flask(__name__)
CORS(app)

# 配置
app.config.update({
    'JSON_AS_ASCII': False,
    'JSONIFY_PRETTYPRINT_REGULAR': True,
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
})

def require_feature(feature_name):
    """装饰器：检查可选功能是否可用"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if feature_name == 'pandas' and not PANDAS_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Excel导出功能不可用，请安装pandas库'
                }), 503
            elif feature_name == 'plotly' and not PLOTLY_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': '图表功能不可用，请安装plotly库'
                }), 503
            elif feature_name == 'excel' and not EXCEL_AVAILABLE:
                return jsonify({
                    'success': False,
                    'error': 'Excel导出功能不可用，请安装openpyxl库'
                }), 503
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'features': {
            'pandas': PANDAS_AVAILABLE,
            'plotly': PLOTLY_AVAILABLE,
            'matplotlib': MATPLOTLIB_AVAILABLE,
            'excel': EXCEL_AVAILABLE
        }
    })

@app.route('/api/features', methods=['GET'])
def get_features():
    """获取可用功能列表"""
    return jsonify({
        'success': True,
        'features': {
            'core_calculation': True,  # 核心计算功能总是可用
            'excel_export': EXCEL_AVAILABLE,
            'chart_generation': PLOTLY_AVAILABLE,
            'advanced_charts': MATPLOTLIB_AVAILABLE,
            'dataframe_operations': PANDAS_AVAILABLE
        }
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    return jsonify({
        'success': True,
        'data': {
            'calculation_methods': CALCULATION_METHODS,
            'interest_calculation_methods': INTEREST_CALCULATION_METHODS,
            'pmt_frequencies': PMT_FREQUENCIES,
            'guarantee_deposit_methods': GUARANTEE_DEPOSIT_METHODS,
            'offset_methods': OFFSET_METHODS,
            'float_rate_methods': FLOAT_RATE_METHODS,
        }
    })

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """融资租赁计算"""
    try:
        data = request.get_json()
        
        # 创建计算器实例
        calculator = LeaseCalculator()
        
        # 解析输入参数
        principal = float(data.get('principal', 0))
        annual_rate = float(data.get('annual_rate', 0)) / 100
        periods = int(data.get('periods', 0))
        calculation_method = data.get('calculation_method', '等额年金法')
        
        # 执行计算
        if calculation_method == '等额年金法':
            result = calculator.calculate_equal_annuity(principal, annual_rate, periods)
        elif calculation_method == '等额本金法':
            result = calculator.calculate_equal_principal(principal, annual_rate, periods)
        elif calculation_method == '平息法':
            result = calculator.calculate_flat_rate(principal, annual_rate, periods)
        else:
            return jsonify({
                'success': False,
                'error': f'不支持的计算方法: {calculation_method}'
            }), 400
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/charts/payment-schedule', methods=['POST'])
@require_feature('plotly')
def generate_payment_chart():
    """生成还款计划图表（需要plotly）"""
    try:
        data = request.get_json()
        schedule = data.get('schedule', [])
        
        if not schedule:
            return jsonify({
                'success': False,
                'error': '还款计划数据为空'
            }), 400
        
        periods = [item['period'] for item in schedule]
        principals = [item['principal'] for item in schedule]
        interests = [item['interest'] for item in schedule]
        
        fig = go.Figure(
            data=[
                go.Bar(name="本金", x=periods, y=principals),
                go.Bar(name="利息", x=periods, y=interests),
            ]
        )
        
        fig.update_layout(
            title="还款计划 - 本金与利息分布",
            xaxis_title="期数",
            yaxis_title="金额 (元)",
            barmode="stack",
            template="plotly_white",
        )
        
        return jsonify({
            'success': True,
            'chart': json.dumps(fig, cls=PlotlyJSONEncoder)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export/excel', methods=['POST'])
@require_feature('excel')
def export_excel():
    """导出Excel文件（需要openpyxl）"""
    try:
        data = request.get_json()
        
        # 创建Excel文件
        output = io.BytesIO()
        
        if PANDAS_AVAILABLE:
            # 使用pandas导出（功能更丰富）
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # 基本信息
                basic_info = [
                    ["融资本金", data.get('principal', 0)],
                    ["年利率", f"{data.get('annual_rate', 0)}%"],
                    ["租期", f"{data.get('periods', 0)}期"],
                    ["计算方法", data.get('calculation_method', '')],
                ]
                
                basic_info_df = pd.DataFrame(basic_info, columns=["项目", "数值"])
                basic_info_df.to_excel(writer, sheet_name="基本信息", index=False)
                
                # 还款计划
                schedule = data.get('schedule', [])
                if schedule:
                    schedule_df = pd.DataFrame(schedule)
                    schedule_df.to_excel(writer, sheet_name="还款计划", index=False)
        else:
            # 使用openpyxl直接操作（轻量版）
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "基本信息"
            
            # 写入基本信息
            ws.append(["项目", "数值"])
            ws.append(["融资本金", data.get('principal', 0)])
            ws.append(["年利率", f"{data.get('annual_rate', 0)}%"])
            ws.append(["租期", f"{data.get('periods', 0)}期"])
            ws.append(["计算方法", data.get('calculation_method', '')])
            
            # 保存到字节流
            wb.save(output)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'融资租赁计算结果_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 静态文件服务
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """服务前端文件"""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'build')
    
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_file(os.path.join(frontend_dir, path))
    else:
        return send_file(os.path.join(frontend_dir, 'index.html'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 启动融资租赁计算器服务")
    print(f"📡 端口: {port}")
    print(f"🔧 调试模式: {debug}")
    print(f"📊 可用功能:")
    print(f"   - 核心计算: ✅")
    print(f"   - Excel导出: {'✅' if EXCEL_AVAILABLE else '❌'}")
    print(f"   - 图表生成: {'✅' if PLOTLY_AVAILABLE else '❌'}")
    print(f"   - 高级图表: {'✅' if MATPLOTLIB_AVAILABLE else '❌'}")
    print(f"   - 数据框操作: {'✅' if PANDAS_AVAILABLE else '❌'}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
