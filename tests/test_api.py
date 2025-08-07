import pytest
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPI:
    """API接口测试"""
    
    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_calculate_equal_annuity(self, client):
        """测试等额年金法计算接口"""
        payload = {
            'method': 'equal_annuity',
            'pv': 1000000,
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12,
            'guarantee': 50000,
            'guarantee_mode': '尾期冲抵'
        }
        
        response = client.post('/api/calculate', 
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'data' in data
        
        result = data['data']
        assert 'pmt' in result
        assert 'total_interest' in result
        assert 'schedule' in result
        assert len(result['schedule']) == 36
    
    def test_calculate_equal_principal(self, client):
        """测试等额本金法计算接口"""
        payload = {
            'method': 'equal_principal',
            'pv': 500000,
            'annual_rate': 0.12,
            'periods': 24,
            'frequency': 12
        }
        
        response = client.post('/api/calculate',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
    
    def test_calculate_missing_params(self, client):
        """测试缺少参数的情况"""
        payload = {
            'method': 'equal_annuity',
            'pv': 1000000
            # 缺少其他必要参数
        }
        
        response = client.post('/api/calculate',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_calculate_invalid_method(self, client):
        """测试无效的计算方法"""
        payload = {
            'method': 'invalid_method',
            'pv': 1000000,
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12
        }
        
        response = client.post('/api/calculate',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        assert response.status_code == 400
    
    def test_export_excel(self, client):
        """测试Excel导出"""
        # 先计算得到结果
        calc_payload = {
            'method': 'equal_annuity',
            'pv': 500000,
            'annual_rate': 0.08,
            'periods': 24,
            'frequency': 12
        }
        
        calc_response = client.post('/api/calculate',
                                   data=json.dumps(calc_payload),
                                   content_type='application/json')
        
        calc_data = json.loads(calc_response.data)['data']
        
        # 导出Excel
        export_response = client.post('/api/export/excel',
                                     data=json.dumps(calc_data),
                                     content_type='application/json')
        
        assert export_response.status_code == 200
        assert export_response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    def test_export_json(self, client):
        """测试JSON导出"""
        # 先计算得到结果
        calc_payload = {
            'method': 'equal_annuity',
            'pv': 300000,
            'annual_rate': 0.06,
            'periods': 12,
            'frequency': 12
        }
        
        calc_response = client.post('/api/calculate',
                                   data=json.dumps(calc_payload),
                                   content_type='application/json')
        
        calc_data = json.loads(calc_response.data)['data']
        
        # 导出JSON
        export_response = client.post('/api/export/json',
                                     data=json.dumps(calc_data),
                                     content_type='application/json')
        
        assert export_response.status_code == 200
        assert export_response.content_type == 'application/json; charset=utf-8'
        
        # 检查导出的JSON内容
        exported_data = json.loads(export_response.data)
        assert '基本信息' in exported_data
        assert '计算结果' in exported_data
        assert '详细数据' in exported_data
    
    def test_export_empty_data(self, client):
        """测试导出空数据"""
        response = client.post('/api/export/excel',
                              data=json.dumps({}),
                              content_type='application/json')
        
        # 应该能处理空数据而不报错
        assert response.status_code == 200


class TestFrontend:
    """前端页面测试"""
    
    def test_index_page(self, client):
        """测试主页"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data
    
    def test_static_files(self, client):
        """测试静态文件访问"""
        # 测试CSS文件
        response = client.get('/static/css/main.3cad2f5b.css')
        if response.status_code == 200:  # 如果文件存在
            assert 'text/css' in response.content_type
    
    def test_404_page(self, client):
        """测试404页面"""
        response = client.get('/nonexistent-page')
        # 应该返回404.html或重定向到主页
        assert response.status_code in [200, 404]


class TestErrorHandling:
    """错误处理测试"""
    
    def test_invalid_json(self, client):
        """测试无效JSON"""
        response = client.post('/api/calculate',
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400
    
    def test_large_numbers(self, client):
        """测试极大数值"""
        payload = {
            'method': 'equal_annuity',
            'pv': 999999999999,  # 非常大的数
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12
        }
        
        response = client.post('/api/calculate',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        # 应该能处理或返回合理的错误
        assert response.status_code in [200, 400]
    
    def test_zero_values(self, client):
        """测试零值输入"""
        payload = {
            'method': 'equal_annuity',
            'pv': 0,  # 零本金
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12
        }
        
        response = client.post('/api/calculate',
                              data=json.dumps(payload),
                              content_type='application/json')
        
        # 零本金应该返回错误或特殊处理
        assert response.status_code in [200, 400]
