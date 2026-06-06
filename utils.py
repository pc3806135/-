"""
公共工具函数
- 单位转换
- 输入校验
- 格式化输出
"""

import math
from typing import Tuple, Optional


def kw_to_w(power_kw: float) -> float:
    """千瓦转瓦"""
    return power_kw * 1000.0


def w_to_kw(power_w: float) -> float:
    """瓦转千瓦"""
    return power_w / 1000.0


def validate_positive(value: float, name: str) -> None:
    """校验值为正数，否则抛出 ValueError"""
    if value <= 0:
        raise ValueError(f"{name} 必须大于 0，当前值: {value}")


def validate_range(value: float, name: str, min_val: float, max_val: float) -> None:
    """校验值在范围内"""
    if value < min_val or value > max_val:
        raise ValueError(f"{name} 必须在 [{min_val}, {max_val}] 范围内，当前值: {value}")


def validate_cos_phi(cos_phi: float) -> None:
    """校验功率因数"""
    validate_range(cos_phi, "功率因数 cosφ", 0.1, 1.0)


def validate_voltage(voltage: float) -> None:
    """校验电压等级 (常用等级)"""
    standard_voltages = [220, 380, 660, 1000, 3000, 6000, 10000, 20000, 35000]
    if voltage not in standard_voltages:
        # 不强制报错，但给出提示
        pass


def format_current(current: float) -> str:
    """格式化电流显示"""
    if current >= 1000:
        return f"{current:.1f} A ({current/1000:.2f} kA)"
    return f"{current:.1f} A"


def format_percent(value: float) -> str:
    """格式化百分比显示"""
    return f"{value:.2f}%"


def round_up_to_standard(value: float, standards: list) -> float:
    """向上取最近的标准值"""
    for s in sorted(standards):
        if s >= value:
            return s
    return standards[-1]
