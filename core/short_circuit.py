"""
模块④: 短路热稳定校验

符合 GB 50054-2011《低压配电设计规范》 §6.2.3

S_min = I_k × √t / K

S_min : 导体最小截面 (mm²)
I_k   : 三相短路电流有效值 (A)
t     : 短路持续时间 (s)
K     : 热稳定系数
"""

import math
from dataclasses import dataclass
from data.k_values import get_k_value


@dataclass
class ShortCircuitInput:
    """短路热稳定校验输入"""
    ik_a: float          # 短路电流有效值 (A)
    t_s: float           # 短路持续时间 (s)
    conductor: str       # "copper" | "aluminum"
    insulation: str      # "pvc" | "xlpe"
    selected_section: float  # 已选电缆截面 (mm²)
    description: str = ""   # 描述


class ShortCircuitResult:
    """短路热稳定校验结果"""
    def __init__(self, input_params: ShortCircuitInput,
                 s_min: float, k: float):
        self.input = input_params
        self.s_min = s_min              # 要求的最小截面 (mm²)
        self.k = k                      # 热稳定系数

    @property
    def is_pass(self) -> bool:
        """是否通过校验"""
        return self.input.selected_section >= self.s_min

    @property
    def margin(self) -> float:
        """截面裕量"""
        return self.input.selected_section - self.s_min

    @property
    def required_section(self) -> float:
        """若不通过，需要升级到的截面（向上取最近标准截面）"""
        if self.is_pass:
            return self.input.selected_section
        from data.ampacity import STANDARD_SECTIONS
        for s in STANDARD_SECTIONS:
            if s >= self.s_min:
                return s
        return STANDARD_SECTIONS[-1]

    def __repr__(self):
        status = "✓ 合格" if self.is_pass else "✗ 不合格"
        return (f"<S_min={self.s_min:.1f}mm², 已选={self.input.selected_section}mm² "
                f"{status}>")


def check_short_circuit(params: ShortCircuitInput) -> ShortCircuitResult:
    """
    短路热稳定校验。

    参数:
        params: ShortCircuitInput

    返回:
        ShortCircuitResult
    """
    k = get_k_value(params.conductor, params.insulation)
    s_min = params.ik_a * math.sqrt(params.t_s) / k

    return ShortCircuitResult(params, s_min, k)


def calc_required_section(ik_a: float, t_s: float,
                          conductor: str, insulation: str) -> float:
    """
    快速计算短路热稳定要求的最小截面。

    参数:
        ik_a: 短路电流 (A)
        t_s: 持续时间 (s)
        conductor: "copper" | "aluminum"
        insulation: "pvc" | "xlpe"

    返回:
        S_min (mm²)
    """
    k = get_k_value(conductor, insulation)
    return ik_a * math.sqrt(t_s) / k
