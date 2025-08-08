"""
端到端测试模块
测试完整的用户场景和工作流
"""

import pytest
import json
import sys
import os
import requests
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


class TestEndToEnd:
    """端到端测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.app = app.test_client()
        self.app.testing = True
        self.base_url = 'http://localhost:5002'
    
    def test_complete_calculation_workflow(self):
        """测试完整的计算工作流"""
        
        # 1. 健康检查
        response = self.app.get('/api/health')
        assert response.status_code == 200
        
        # 2. 基本计算
        calculation_payload = {
            'method': 'equal_annuity',
            'pv': 1000000,
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12,
            'guarantee': 50000,
            'guarantee_mode': '尾期冲抵'
        }
        
        response = self.app.post('/api/calculate', json=calculation_payload)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'pmt' in data['data']
        
        # 保存结果用于后续测试
        calculation_result = data['data']
        
        # 3. Excel导出测试
        export_payload = {
            'data': calculation_result,
            'format': 'excel'
        }
        
        response = self.app.post('/api/export/excel', json=export_payload)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # 4. JSON导出测试
        export_payload['format'] = 'json'
        response = self.app.post('/api/export/json', json=export_payload)
        assert response.status_code == 200
        assert response.headers['Content-Type'].startswith('application/json')
        
        exported_data = json.loads(response.data)
        assert '基本信息' in exported_data
        assert '计算结果' in exported_data
    
    def test_multiple_calculation_methods(self):
        """测试多种计算方法的端到端流程"""
        methods = [
            'equal_annuity',
            'equal_principal', 
            'flat_rate',
            'floating_rate'
        ]
        
        base_payload = {
            'pv': 1000000,
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12
        }
        
        results = {}
        
        for method in methods:
            payload = base_payload.copy()
            payload['method'] = method
            
            # 特殊方法的额外参数
            if method == 'floating_rate':
                payload['rate_changes'] = [
                    {'period': 12, 'new_rate': 0.09},
                    {'period': 24, 'new_rate': 0.07}
                ]
            
            response = self.app.post('/api/calculate', json=payload)
            assert response.status_code == 200, f"方法 {method} 计算失败"
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            results[method] = data['data']
        
        # 验证不同方法产生不同结果
        pmts = [results[method]['pmt'] for method in methods if 'pmt' in results[method]]
        assert len(set(pmts)) > 1, "不同计算方法应该产生不同的结果"
    
    def test_error_handling_workflow(self):
        """测试错误处理工作流"""
        
        # 测试无效参数
        invalid_payloads = [
            # 缺少必需参数
            {'method': 'equal_annuity'},
            
            # 无效的方法
            {
                'method': 'invalid_method',
                'pv': 1000000,
                'annual_rate': 0.08,
                'periods': 36,
                'frequency': 12
            },
            
            # 负数参数
            {
                'method': 'equal_annuity',
                'pv': -1000000,
                'annual_rate': 0.08,
                'periods': 36,
                'frequency': 12
            },
            
            # 零期数
            {
                'method': 'equal_annuity',
                'pv': 1000000,
                'annual_rate': 0.08,
                'periods': 0,
                'frequency': 12
            }
        ]
        
        for payload in invalid_payloads:
            response = self.app.post('/api/calculate', json=payload)
            assert response.status_code in [400, 422], f"应该返回错误状态码，payload: {payload}"
    
    def test_data_validation_workflow(self):
        """测试数据验证工作流"""
        
        # 边界值测试
        boundary_tests = [
            # 最小值
            {
                'method': 'equal_annuity',
                'pv': 1,
                'annual_rate': 0.001,
                'periods': 1,
                'frequency': 12
            },
            
            # 最大合理值
            {
                'method': 'equal_annuity',
                'pv': 100000000,  # 1亿
                'annual_rate': 0.30,  # 30%
                'periods': 600,  # 50年
                'frequency': 12
            }
        ]
        
        for payload in boundary_tests:
            response = self.app.post('/api/calculate', json=payload)
            assert response.status_code == 200, f"边界值测试失败，payload: {payload}"
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_irr_calculation_workflow(self):
        """测试IRR计算工作流"""
        
        # 首先进行基本计算
        calculation_payload = {
            'method': 'equal_annuity',
            'pv': 1000000,
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12
        }
        
        response = self.app.post('/api/calculate', json=calculation_payload)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        schedule = data['data']['schedule']
        
        # 提取现金流
        cash_flows = [-calculation_payload['pv']]  # 初始投资
        cash_flows.extend([period['payment'] for period in schedule])
        
        # 验证IRR已经在计算结果中
        assert 'irr' in data['data']
        
        # IRR应该接近原始利率
        irr = data['data']['irr']
        original_rate = calculation_payload['annual_rate']
        assert abs(irr - original_rate) < 0.01, f"IRR {irr} 与原始利率 {original_rate} 差异过大"
    
    def test_concurrent_users_simulation(self):
        """模拟并发用户测试"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def simulate_user(user_id):
            """模拟单个用户的操作"""
            try:
                # 用户进行一系列操作
                # 1. 健康检查
                response = self.app.get('/api/health')
                assert response.status_code == 200
                
                # 2. 计算
                payload = {
                    'method': 'equal_annuity',
                    'pv': 1000000 + user_id * 10000,  # 每个用户不同的金额
                    'annual_rate': 0.08,
                    'periods': 36,
                    'frequency': 12
                }
                
                response = self.app.post('/api/calculate', json=payload)
                assert response.status_code == 200
                
                data = json.loads(response.data)
                assert data['status'] == 'success'
                
                results_queue.put(f"用户{user_id}操作成功")
                
            except Exception as e:
                errors_queue.put(f"用户{user_id}操作失败: {str(e)}")
        
        # 创建5个并发用户
        threads = []
        for i in range(5):
            t = threading.Thread(target=simulate_user, args=(i,))
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 检查结果
        assert errors_queue.empty(), f"并发测试有错误: {list(errors_queue.queue)}"
        assert results_queue.qsize() == 5, "并发测试结果数量不正确"
    
    def test_frontend_integration(self):
        """测试前端集成"""
        
        # 测试静态文件服务
        response = self.app.get('/')
        assert response.status_code == 200
        
        # 检查是否包含预期的HTML内容
        html_content = response.data.decode('utf-8')
        assert '融资租赁计算器' in html_content or 'lease-calculator' in html_content
        
        # 测试静态资源
        response = self.app.get('/static/js/main.2e2ece20.js')
        assert response.status_code == 200
        
        response = self.app.get('/static/css/main.3cad2f5b.css')
        assert response.status_code == 200
