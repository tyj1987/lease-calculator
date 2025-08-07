import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from lease_calculator import LeaseCalculator


class TestLeaseCalculator:
    """租赁计算器测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.calculator = LeaseCalculator()
        self.pv = 1000000  # 100万本金
        self.annual_rate = 0.08  # 8%年利率
        self.periods = 36  # 36期
        self.frequency = 12  # 月付
    
    def test_equal_annuity_method(self):
        """测试等额年金法"""
        result = self.calculator.equal_annuity_method(
            self.pv, self.annual_rate, self.periods, self.frequency
        )
        
        assert 'pmt' in result
        assert 'total_interest' in result
        assert 'total_payment' in result
        assert 'schedule' in result
        
        # 验证每期租金大于0
        assert result['pmt'] > 0
        
        # 验证还款计划期数正确
        assert len(result['schedule']) == self.periods
        
        # 验证总支付额 = 每期租金 × 期数
        expected_total = result['pmt'] * self.periods
        assert abs(result['total_payment'] - expected_total) < 0.01
    
    def test_equal_principal_method(self):
        """测试等额本金法"""
        result = self.calculator.equal_principal_method(
            self.pv, self.annual_rate, self.periods, self.frequency
        )
        
        assert 'schedule' in result
        assert len(result['schedule']) == self.periods
        
        # 验证每期本金相等
        principal_payments = [item['principal'] for item in result['schedule']]
        expected_principal = self.pv / self.periods
        
        for principal in principal_payments:
            assert abs(principal - expected_principal) < 0.01
    
    def test_flat_rate_method(self):
        """测试平息法"""
        years = 3  # 3年期
        result = self.calculator.flat_rate_method(
            self.pv, self.annual_rate, years, self.frequency
        )
        
        assert 'pmt' in result
        assert 'flat_rate' in result
        assert 'actual_irr' in result
        
        # 平息法每期租金应该相等
        payments = [item['payment'] for item in result['schedule']]
        assert all(abs(payment - payments[0]) < 0.01 for payment in payments)
    
    def test_calculate_irr(self):
        """测试IRR计算"""
        cash_flows = [-1000000] + [31336.37] * 36  # 典型现金流
        irr = self.calculator.calculate_irr(cash_flows, 12)
        
        assert irr > 0
        assert irr < 1  # IRR应该是合理的百分比
    
    def test_guarantee_offset(self):
        """测试保证金冲抵"""
        # 先生成还款计划
        result = self.calculator.equal_annuity_method(
            self.pv, self.annual_rate, self.periods, self.frequency
        )
        
        guarantee = 50000  # 5万保证金
        guarantee_mode = "尾期冲抵"
        
        offset_result = self.calculator.apply_guarantee_offset(
            result['schedule'], guarantee, guarantee_mode
        )
        
        assert 'total_offset' in offset_result
        assert 'offset_details' in offset_result
        assert offset_result['total_offset'] <= guarantee
    
    def test_invalid_parameters(self):
        """测试无效参数处理"""
        # 测试负数本金
        with pytest.raises((ValueError, Exception)):
            self.calculator.equal_annuity_method(-100000, 0.08, 36, 12)
        
        # 测试零期数
        with pytest.raises((ValueError, ZeroDivisionError, Exception)):
            self.calculator.equal_annuity_method(100000, 0.08, 0, 12)
        
        # 测试极高利率
        result = self.calculator.equal_annuity_method(100000, 5.0, 36, 12)
        assert result['pmt'] > 0  # 应该仍能计算出结果
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试很小的本金
        result = self.calculator.equal_annuity_method(1, 0.08, 12, 12)
        assert result['pmt'] > 0
        
        # 测试0利率
        result = self.calculator.equal_annuity_method(120000, 0, 12, 12)
        expected_pmt = 120000 / 12  # 无利率时等于本金平分
        assert abs(result['pmt'] - expected_pmt) < 0.01


class TestCalculatorResults:
    """测试计算结果的合理性"""
    
    def setup_method(self):
        self.calculator = LeaseCalculator()
    
    def test_pmt_reasonableness(self):
        """测试每期租金的合理性"""
        result = self.calculator.equal_annuity_method(1000000, 0.08, 36, 12)
        
        # 每期租金应该在合理范围内
        monthly_rate = 0.08 / 12
        min_pmt = 1000000 / 36  # 无利率时的最小值
        max_pmt = 1000000 * monthly_rate / (1 - (1 + monthly_rate) ** (-36)) * 1.5
        
        assert min_pmt < result['pmt'] < max_pmt
    
    def test_total_interest_positive(self):
        """测试总利息为正"""
        result = self.calculator.equal_annuity_method(1000000, 0.08, 36, 12)
        assert result['total_interest'] > 0
    
    def test_remaining_balance_decreases(self):
        """测试剩余本金递减"""
        result = self.calculator.equal_annuity_method(1000000, 0.08, 36, 12)
        
        balances = [item['remaining_balance'] for item in result['schedule']]
        
        # 剩余本金应该递减
        for i in range(1, len(balances)):
            assert balances[i] < balances[i-1]
        
        # 最后一期剩余本金应该为0
        assert abs(balances[-1]) < 0.01
