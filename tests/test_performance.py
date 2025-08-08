"""
性能测试模块
测试各种计算方法的性能表现
"""

import pytest
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lease_calculator import LeaseCalculator
from app import app


class TestPerformance:
    """性能测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.calculator = LeaseCalculator()
        self.app = app.test_client()
        self.app.testing = True
    
    def test_calculation_performance(self):
        """测试计算方法性能"""
        pv = 1000000
        annual_rate = 0.08
        periods = 360  # 30年，月付
        frequency = 12
        
        # 测试等额年金法性能
        start_time = time.time()
        result = self.calculator.equal_annuity_method(pv, annual_rate, periods, frequency)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        assert calculation_time < 1.0, f"等额年金法计算时间过长: {calculation_time:.3f}秒"
        assert len(result['schedule']) == periods
    
    def test_batch_calculation_performance(self):
        """测试批量计算性能"""
        test_cases = [
            (1000000, 0.08, 36, 12),
            (5000000, 0.10, 60, 12),
            (10000000, 0.12, 120, 12),
            (500000, 0.06, 24, 12),
            (2000000, 0.09, 48, 12),
        ]
        
        start_time = time.time()
        for pv, rate, periods, freq in test_cases:
            result = self.calculator.equal_annuity_method(pv, rate, periods, freq)
            assert 'pmt' in result
            assert result['pmt'] > 0
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / len(test_cases)
        
        assert total_time < 5.0, f"批量计算总时间过长: {total_time:.3f}秒"
        assert avg_time < 1.0, f"平均计算时间过长: {avg_time:.3f}秒"
    
    def test_api_response_time(self):
        """测试API响应时间"""
        payload = {
            'method': 'equal_annuity',
            'pv': 1000000,
            'annual_rate': 0.08,
            'periods': 36,
            'frequency': 12
        }
        
        start_time = time.time()
        response = self.app.post('/api/calculate', json=payload)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0, f"API响应时间过长: {response_time:.3f}秒"
        assert response.status_code == 200
    
    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 进行大量计算
        for i in range(100):
            result = self.calculator.equal_annuity_method(
                1000000 + i * 10000, 0.08, 36, 12
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长不应超过50MB
        assert memory_increase < 50, f"内存增长过大: {memory_increase:.2f}MB"
    
    def test_concurrent_calculations(self):
        """测试并发计算"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def worker():
            try:
                result = self.calculator.equal_annuity_method(1000000, 0.08, 36, 12)
                results_queue.put(result)
            except Exception as e:
                errors_queue.put(e)
        
        # 创建10个并发线程
        threads = []
        start_time = time.time()
        
        for i in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 检查结果
        assert errors_queue.empty(), "并发计算出现错误"
        assert results_queue.qsize() == 10, "并发计算结果数量不正确"
        assert total_time < 5.0, f"并发计算时间过长: {total_time:.3f}秒"
