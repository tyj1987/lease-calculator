"""
融资租赁核心计算算法模块
实现等额年金法、等额本金法、平息法、浮动利率法等核心算法
"""

from decimal import Decimal, getcontext, DivisionByZero
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math

# 导入numpy_financial
try:
    import numpy_financial as npf
except ImportError:
    npf = None

# 设置高精度计算
getcontext().prec = 15


class LeaseCalculator:
    """融资租赁计算器核心类"""

    def __init__(self):
        self.precision = Decimal("0.01")  # 精度到分

    def _validate_parameters(self, pv: float, annual_rate: float, periods: int, frequency: int):
        """验证输入参数"""
        if pv <= 0:
            raise ValueError("租赁本金必须大于0")
        if annual_rate < 0:
            raise ValueError("年利率不能为负数")
        if periods <= 0:
            raise ValueError("期数必须大于0")
        if frequency <= 0:
            raise ValueError("年付次数必须大于0")

    def equal_annuity_method(self, pv: float, annual_rate: float, periods: int, frequency: int = 12) -> Dict:
        """
        等额年金法（等额本息法）

        Args:
            pv: 租赁本金
            annual_rate: 年利率
            periods: 总期数
            frequency: 年付次数（默认12为月付）

        Returns:
            Dict: 包含每期租金、总利息、还款计划等
        """
        self._validate_parameters(pv, annual_rate, periods, frequency)

        pv = Decimal(str(pv))
        period_rate = Decimal(str(annual_rate)) / Decimal(str(frequency))
        n = Decimal(str(periods))

        # 处理0利率情况
        if period_rate == 0:
            pmt = pv / n
        else:
            # PMT = PV * [i * (1+i)^n] / [(1+i)^n - 1]
            factor = (1 + period_rate) ** n
            pmt = pv * (period_rate * factor) / (factor - 1)

        pmt = pmt.quantize(self.precision)

        # 生成还款计划
        schedule = []
        remaining_balance = pv
        total_interest = Decimal("0")

        for period in range(1, int(periods) + 1):
            interest = remaining_balance * period_rate
            interest = interest.quantize(self.precision)

            principal = pmt - interest
            principal = principal.quantize(self.precision)

            remaining_balance -= principal

            # 最后一期处理剩余余额精度问题
            if period == int(periods):
                remaining_balance = Decimal("0")
            else:
                remaining_balance = remaining_balance.quantize(self.precision)

            total_interest += interest

            schedule.append(
                {
                    "period": period,
                    "payment": float(pmt),
                    "principal": float(principal),
                    "interest": float(interest),
                    "remaining_balance": float(remaining_balance),
                }
            )

        return {
            "method": "等额年金法",
            "pmt": float(pmt),
            "total_interest": float(total_interest),
            "total_payment": float(pmt * n),
            "schedule": schedule,
        }

    def equal_principal_method(self, pv: float, annual_rate: float, periods: int, frequency: int = 12) -> Dict:
        """
        等额本金法

        Args:
            pv: 租赁本金
            annual_rate: 年利率
            periods: 总期数
            frequency: 年付次数

        Returns:
            Dict: 包含每期租金、总利息、还款计划等
        """
        pv = Decimal(str(pv))
        period_rate = Decimal(str(annual_rate)) / Decimal(str(frequency))
        n = int(periods)

        # 每期本金
        principal_per_period = pv / Decimal(str(n))
        principal_per_period = principal_per_period.quantize(self.precision)

        schedule = []
        remaining_balance = pv
        total_interest = Decimal("0")
        total_payment = Decimal("0")

        for period in range(1, n + 1):
            interest = remaining_balance * period_rate
            interest = interest.quantize(self.precision)

            pmt = principal_per_period + interest
            pmt = pmt.quantize(self.precision)

            remaining_balance -= principal_per_period
            remaining_balance = remaining_balance.quantize(self.precision)

            total_interest += interest
            total_payment += pmt

            schedule.append(
                {
                    "period": period,
                    "payment": float(pmt),
                    "principal": float(principal_per_period),
                    "interest": float(interest),
                    "remaining_balance": float(remaining_balance),
                }
            )

        return {
            "method": "等额本金法",
            "total_interest": float(total_interest),
            "total_payment": float(total_payment),
            "schedule": schedule,
        }

    def flat_rate_method(self, pv: float, flat_rate: float, years: float, frequency: int = 12) -> Dict:
        """
        平息法计算

        Args:
            pv: 租赁本金
            flat_rate: 平息年利率
            years: 年数
            frequency: 年付次数

        Returns:
            Dict: 包含每期租金、总利息、实际IRR等
        """
        pv = Decimal(str(pv))
        flat_rate = Decimal(str(flat_rate))
        years = Decimal(str(years))
        n = int(years * frequency)

        # 总利息 = PV * 平息率 * 年数
        total_interest = pv * flat_rate * years
        total_interest = total_interest.quantize(self.precision)

        # 每期租金 = (本金 + 总利息) / 期数
        pmt = (pv + total_interest) / Decimal(str(n))
        pmt = pmt.quantize(self.precision)

        # 计算实际IRR
        cash_flows = [-float(pv)] + [float(pmt)] * n
        irr = self.calculate_irr(cash_flows, frequency)

        schedule = []
        for period in range(1, n + 1):
            schedule.append(
                {
                    "period": period,
                    "payment": float(pmt),
                    "principal": float(pv / Decimal(str(n))),
                    "interest": float(total_interest / Decimal(str(n))),
                    "remaining_balance": float(pv * (n - period) / Decimal(str(n))),
                }
            )

        return {
            "method": "平息法",
            "pmt": float(pmt),
            "total_interest": float(total_interest),
            "total_payment": float(pmt * Decimal(str(n))),
            "flat_rate": float(flat_rate),
            "actual_irr": irr,
            "schedule": schedule,
        }

    def floating_rate_method(
        self, pv: float, initial_rate: float, periods: int, rate_reset_schedule: List[Dict], frequency: int = 12
    ) -> Dict:
        """
        浮动利率法

        Args:
            pv: 租赁本金
            initial_rate: 初始年利率
            periods: 总期数
            rate_reset_schedule: 利率重置计划 [{'period': 6, 'new_rate': 0.065}, ...]
            frequency: 年付次数

        Returns:
            Dict: 包含每期租金、总利息、还款计划等
        """
        schedule = []
        remaining_balance = Decimal(str(pv))
        current_rate = Decimal(str(initial_rate))
        total_interest = Decimal("0")
        total_payment = Decimal("0")

        # 创建利率变化映射
        rate_changes = {item["period"]: Decimal(str(item["new_rate"])) for item in rate_reset_schedule}

        period = 1
        while period <= periods and remaining_balance > 0:
            # 检查是否需要重置利率
            if period in rate_changes:
                current_rate = rate_changes[period]

            # 计算剩余期数
            remaining_periods = periods - period + 1

            # 使用等额年金法计算当前利率下的租金
            period_rate = current_rate / Decimal(str(frequency))

            if remaining_periods == 1:
                pmt = remaining_balance
                interest = Decimal("0")
                principal = remaining_balance
            else:
                factor = (1 + period_rate) ** remaining_periods
                pmt = remaining_balance * (period_rate * factor) / (factor - 1)
                pmt = pmt.quantize(self.precision)

                interest = remaining_balance * period_rate
                interest = interest.quantize(self.precision)

                principal = pmt - interest
                principal = principal.quantize(self.precision)

            remaining_balance -= principal
            remaining_balance = remaining_balance.quantize(self.precision)

            total_interest += interest
            total_payment += pmt

            schedule.append(
                {
                    "period": period,
                    "payment": float(pmt),
                    "principal": float(principal),
                    "interest": float(interest),
                    "rate": float(current_rate),
                    "remaining_balance": float(remaining_balance),
                }
            )

            period += 1

        return {
            "method": "浮动利率法",
            "total_interest": float(total_interest),
            "total_payment": float(total_payment),
            "schedule": schedule,
        }

    def calculate_irr(self, cash_flows: List[float], frequency: int = 12) -> float:
        """
        计算内部收益率(IRR)

        Args:
            cash_flows: 现金流序列
            frequency: 年付次数

        Returns:
            float: 年化IRR
        """
        try:
            # 使用numpy_financial的IRR计算
            if npf is not None:
                period_irr = npf.irr(cash_flows)
            else:
                period_irr = np.irr(cash_flows)

            if np.isnan(period_irr):
                return 0.0

            # 转换为年化IRR
            annual_irr = (1 + period_irr) ** frequency - 1
            return round(annual_irr, 6)
        except:
            # 如果numpy.irr不可用，使用牛顿法求解
            return self._newton_irr(cash_flows, frequency)

    def _newton_irr(
        self, cash_flows: List[float], frequency: int = 12, tolerance: float = 1e-6, max_iterations: int = 100
    ) -> float:
        """
        使用牛顿法计算IRR
        """

        def npv(rate):
            return sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))

        def npv_derivative(rate):
            return sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))

        rate = 0.1  # 初始猜测

        for _ in range(max_iterations):
            npv_val = npv(rate)
            if abs(npv_val) < tolerance:
                break

            npv_deriv = npv_derivative(rate)
            if abs(npv_deriv) < tolerance:
                break

            rate = rate - npv_val / npv_deriv

        # 转换为年化率
        annual_irr = (1 + rate) ** frequency - 1
        return round(annual_irr, 6)

    def apply_guarantee_offset(self, schedule: List[Dict], guarantee: float, mode: str = "尾期冲抵") -> Dict:
        """
        保证金冲抵处理

        Args:
            schedule: 还款计划
            guarantee: 保证金金额
            mode: 冲抵模式（尾期冲抵、按比例分摊、首期冲抵）

        Returns:
            Dict: 处理后的还款计划和冲抵详情
        """
        guarantee = Decimal(str(guarantee))
        modified_schedule = schedule.copy()
        offset_details = []
        remaining_guarantee = guarantee

        if mode == "尾期冲抵":
            # 从最后一期向前冲抵
            for i in range(len(modified_schedule) - 1, -1, -1):
                if remaining_guarantee <= 0:
                    break

                original_payment = Decimal(str(modified_schedule[i]["payment"]))

                if remaining_guarantee >= original_payment:
                    offset_amount = original_payment
                    remaining_guarantee -= original_payment
                    modified_schedule[i]["payment"] = 0.0
                else:
                    offset_amount = remaining_guarantee
                    modified_schedule[i]["payment"] = float(original_payment - remaining_guarantee)
                    remaining_guarantee = Decimal("0")

                if offset_amount > 0:
                    offset_details.append(
                        {
                            "period": modified_schedule[i]["period"],
                            "offset_amount": float(offset_amount),
                            "remaining_payment": modified_schedule[i]["payment"],
                        }
                    )

        elif mode == "按比例分摊":
            # 按比例平均冲抵各期
            total_periods = len(modified_schedule)
            avg_offset = guarantee / Decimal(str(total_periods))

            for i, payment_info in enumerate(modified_schedule):
                original_payment = Decimal(str(payment_info["payment"]))
                offset_amount = min(avg_offset, original_payment)

                modified_schedule[i]["payment"] = float(original_payment - offset_amount)
                remaining_guarantee -= offset_amount

                if offset_amount > 0:
                    offset_details.append(
                        {
                            "period": payment_info["period"],
                            "offset_amount": float(offset_amount),
                            "remaining_payment": modified_schedule[i]["payment"],
                        }
                    )

        elif mode == "首期冲抵":
            # 从第一期开始冲抵
            for i, payment_info in enumerate(modified_schedule):
                if remaining_guarantee <= 0:
                    break

                original_payment = Decimal(str(payment_info["payment"]))

                if remaining_guarantee >= original_payment:
                    offset_amount = original_payment
                    remaining_guarantee -= original_payment
                    modified_schedule[i]["payment"] = 0.0
                else:
                    offset_amount = remaining_guarantee
                    modified_schedule[i]["payment"] = float(original_payment - remaining_guarantee)
                    remaining_guarantee = Decimal("0")

                if offset_amount > 0:
                    offset_details.append(
                        {
                            "period": payment_info["period"],
                            "offset_amount": float(offset_amount),
                            "remaining_payment": modified_schedule[i]["payment"],
                        }
                    )

        return {
            "modified_schedule": modified_schedule,
            "offset_details": offset_details,
            "unused_guarantee": float(remaining_guarantee),
            "total_offset": float(guarantee - remaining_guarantee),
        }

    def sensitivity_analysis(self, base_params: Dict, sensitivity_params: Dict) -> Dict:
        """
        敏感性分析

        Args:
            base_params: 基准参数（必须包含pv, annual_rate, periods, frequency）
            sensitivity_params: 敏感性参数设置

        Returns:
            Dict: 敏感性分析结果
        """
        results = {}
        base_result = self.equal_annuity_method(**base_params)
        base_irr = self.calculate_irr(
            [-base_params["pv"]] + [base_result["pmt"]] * base_params["periods"], base_params["frequency"]
        )

        for param_name, variations in sensitivity_params.items():
            results[param_name] = []

            for variation in variations:
                modified_params = base_params.copy()

                if param_name == "annual_rate":
                    modified_params["annual_rate"] = float(variation)
                elif param_name == "periods":
                    modified_params["periods"] = int(variation)
                elif param_name == "pv":
                    modified_params["pv"] = float(variation)
                elif param_name == "frequency":
                    modified_params["frequency"] = int(variation)

                try:
                    result = self.equal_annuity_method(**modified_params)
                    irr = self.calculate_irr(
                        [-modified_params["pv"]] + [result["pmt"]] * modified_params["periods"], modified_params["frequency"]
                    )

                    results[param_name].append(
                        {
                            "param_value": variation,
                            "pmt": result["pmt"],
                            "irr": irr,
                            "pmt_change_pct": (result["pmt"] - base_result["pmt"]) / base_result["pmt"] * 100,
                            "irr_change_pct": (irr - base_irr) / base_irr * 100 if base_irr != 0 else 0,
                        }
                    )
                except Exception as e:
                    results[param_name].append({"param_value": variation, "error": str(e)})

        return {"base_result": {"pmt": base_result["pmt"], "irr": base_irr}, "sensitivity_results": results}

    def reverse_calculate_rate(
        self,
        pv: float,
        target_pmt: float,
        periods: int,
        frequency: int = 12,
        method: str = "equal_annuity",
        tolerance: float = 0.01,
        max_iterations: int = 100,
    ) -> Dict:
        """
        反向计算年利率

        Args:
            pv: 租赁本金
            target_pmt: 目标每期租金
            periods: 总期数
            frequency: 年付次数
            method: 计算方法
            tolerance: 误差容忍度
            max_iterations: 最大迭代次数

        Returns:
            Dict: 包含计算得出的年利率和相关信息
        """
        # 使用二分法求解年利率
        low_rate = 0.001  # 最低利率0.1%
        high_rate = 1.0  # 最高利率100%
        iterations = 0

        for i in range(max_iterations):
            iterations = i + 1
            test_rate = (low_rate + high_rate) / 2

            # 计算在当前利率下的租金
            if method == "equal_annuity":
                result = self.equal_annuity_method(pv, test_rate, periods, frequency)
                calculated_pmt = result["pmt"]
            elif method == "equal_principal":
                result = self.equal_principal_method(pv, test_rate, periods, frequency)
                # 等额本金法取平均租金
                calculated_pmt = sum(item["payment"] for item in result["schedule"]) / periods
            elif method == "flat_rate":
                years = periods / frequency
                result = self.flat_rate_method(pv, test_rate, years, frequency)
                calculated_pmt = result["pmt"]
            else:
                raise ValueError(f"不支持的计算方法: {method}")

            # 检查误差
            error = calculated_pmt - target_pmt
            if abs(error) <= tolerance:
                break

            # 调整搜索范围
            if calculated_pmt > target_pmt:
                high_rate = test_rate
            else:
                low_rate = test_rate

        # 计算最终结果
        final_result = None
        if method == "equal_annuity":
            final_result = self.equal_annuity_method(pv, test_rate, periods, frequency)
        elif method == "equal_principal":
            final_result = self.equal_principal_method(pv, test_rate, periods, frequency)
        elif method == "flat_rate":
            years = periods / frequency
            final_result = self.flat_rate_method(pv, test_rate, years, frequency)

        return {
            "calculated_rate": test_rate,
            "target_pmt": target_pmt,
            "actual_pmt": calculated_pmt,
            "error": error,
            "iterations": iterations,
            "method": method,
            "pv": pv,
            "periods": periods,
            "frequency": frequency,
            "total_interest": final_result.get("total_interest", 0),
            "total_payment": final_result.get("total_payment", 0),
        }

    def reverse_calculate_pmt(
        self,
        pv: float,
        target_irr: float,
        periods: int,
        frequency: int = 12,
        method: str = "equal_annuity",
        tolerance: float = 0.0001,
        max_iterations: int = 100,
    ) -> Dict:
        """
        根据目标IRR反向计算租金

        Args:
            pv: 租赁本金
            target_irr: 目标IRR
            periods: 总期数
            frequency: 年付次数
            method: 计算方法
            tolerance: 误差容忍度
            max_iterations: 最大迭代次数

        Returns:
            Dict: 包含计算得出的租金和相关信息
        """
        # 使用二分法求解租金
        low_pmt = pv / periods  # 最低租金（不含利息）
        high_pmt = pv * 2 / periods  # 最高租金（估算）
        iterations = 0

        for i in range(max_iterations):
            iterations = i + 1
            test_pmt = (low_pmt + high_pmt) / 2

            # 构建现金流
            cash_flows = [-pv] + [test_pmt] * periods
            calculated_irr = self.calculate_irr(cash_flows, frequency)

            # 检查误差
            irr_error = calculated_irr - target_irr
            if abs(irr_error) <= tolerance:
                break

            # 调整搜索范围
            if calculated_irr > target_irr:
                high_pmt = test_pmt
            else:
                low_pmt = test_pmt

        # 计算相关财务指标
        total_payment = test_pmt * periods
        total_interest = total_payment - pv

        return {
            "calculated_pmt": test_pmt,
            "target_irr": target_irr,
            "actual_irr": calculated_irr,
            "irr_error": irr_error,
            "iterations": iterations,
            "method": method,
            "pv": pv,
            "periods": periods,
            "frequency": frequency,
            "total_interest": total_interest,
            "total_payment": total_payment,
        }


# 增加numpy的金融函数兼容性
def np_irr_fallback(values):
    """numpy.irr的替代实现"""

    def npv(rate, values):
        return np.sum([v / (1 + rate) ** i for i, v in enumerate(values)])

    def npv_derivative(rate, values):
        return np.sum([-i * v / (1 + rate) ** (i + 1) for i, v in enumerate(values)])

    rate = 0.1
    tolerance = 1e-6
    max_iterations = 100

    for _ in range(max_iterations):
        npv_val = npv(rate, values)
        if abs(npv_val) < tolerance:
            break

        npv_deriv = npv_derivative(rate, values)
        if abs(npv_deriv) < tolerance:
            break

        rate = rate - npv_val / npv_deriv

    return rate


# 替换numpy.irr函数（兼容性处理）
if not hasattr(np, "irr") and npf is None:
    np.irr = np_irr_fallback
