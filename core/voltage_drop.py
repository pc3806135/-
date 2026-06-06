"""
模块③: 压降计算

符合 GB 50054-2011《低压配电设计规范》 §6.4
允许压降限值:
  - 照明回路: ≤ 3%
  - 动力回路: ≤ 5%
  - 混合回路: ≤ 4%
  - 应急照明/安防: ≤ 10%
"""

import math
from typing import Tuple
from data.impedance import get_impedance


# GB 50054 允许压降限值
ALLOWABLE_VD_LIMITS = {
    "lighting": 3.0,     # 照明
    "power": 5.0,        # 动力
    "mixed": 4.0,        # 混合
    "emergency": 10.0,   # 应急照明/安防
}


class VoltageDropInput:
    """压降计算输入参数"""
    def __init__(self, i_js: float, length_m: float,
                 conductor: str = "copper",
                 voltage_level: str = "0.6/1kV",
                 voltage: float = 380.0,
                 cos_phi: float = 0.85,
                 section: float = 0,
                 circuit_type: str = "power"):
        """
        参数:
            i_js: 计算电流 (A)
            length_m: 电缆长度 (m)
            conductor: "copper" | "aluminum"
            voltage_level: "0.6/1kV" | "6/10kV"
            voltage: 线电压 (V)
            cos_phi: 功率因数
            section: 电缆截面 (mm²)。为 0 时需后续设置
            circuit_type: 回路类型 "lighting"|"power"|"mixed"|"emergency"
        """
        self.i_js = i_js
        self.length_m = length_m
        self.conductor = conductor
        self.voltage_level = voltage_level
        self.voltage = voltage
        self.cos_phi = cos_phi
        self.section = section
        self.circuit_type = circuit_type

    @property
    def allowable_limit(self) -> float:
        return ALLOWABLE_VD_LIMITS.get(self.circuit_type, 5.0)


class VoltageDropResult:
    """压降计算结果"""
    def __init__(self, input_params: VoltageDropInput,
                 delta_u_v: float, delta_u_percent: float,
                 r0: float, x0: float):
        self.input = input_params
        self.delta_u_v = delta_u_v          # 压降绝对值 (V)
        self.delta_u_percent = delta_u_percent  # 压降百分比 (%)
        self.r0 = r0                        # 单位电阻 (Ω/km)
        self.x0 = x0                        # 单位电抗 (Ω/km)
        self.limit = input_params.allowable_limit

    @property
    def is_pass(self) -> bool:
        """是否通过压降校验"""
        return self.delta_u_percent <= self.limit

    @property
    def margin(self) -> float:
        """裕量百分比"""
        return self.limit - self.delta_u_percent

    def __repr__(self):
        status = "✓ 合格" if self.is_pass else "✗ 超限"
        return (f"<ΔU={self.delta_u_percent:.2f}% "
                f"(限值 {self.limit}%) {status}>")


def calc_voltage_drop_3ph(params: VoltageDropInput) -> VoltageDropResult:
    """
    三相线路压降计算 (精确公式)。

    ΔU = √3 × I × L × (R₀·cosφ + X₀·sinφ) / 1000  [V]
    ΔU% = ΔU / U_n × 100

    参数:
        params: VoltageDropInput

    返回:
        VoltageDropResult
    """
    r0, x0 = _get_r0x0(params)

    sin_phi = math.sin(math.acos(params.cos_phi))

    # 三相压降 (V)
    delta_u_v = (math.sqrt(3) * params.i_js * params.length_m
                 * (r0 * params.cos_phi + x0 * sin_phi) / 1000)

    delta_u_percent = delta_u_v / params.voltage * 100

    return VoltageDropResult(params, delta_u_v, delta_u_percent, r0, x0)


def calc_voltage_drop_1ph(params: VoltageDropInput) -> VoltageDropResult:
    """
    单相线路压降计算。

    ΔU = 2 × I × L × (R₀·cosφ + X₀·sinφ) / 1000  [V]
    ΔU% = ΔU / U_ph × 100

    参数:
        params: VoltageDropInput

    返回:
        VoltageDropResult
    """
    r0, x0 = _get_r0x0(params)

    sin_phi = math.sin(math.acos(params.cos_phi))
    u_ph = params.voltage / math.sqrt(3)

    # 单相压降 (V)，2 倍因为往返
    delta_u_v = (2 * params.i_js * params.length_m
                 * (r0 * params.cos_phi + x0 * sin_phi) / 1000)

    delta_u_percent = delta_u_v / u_ph * 100

    return VoltageDropResult(params, delta_u_v, delta_u_percent, r0, x0)


def calc_voltage_drop_simplified(pe_kw: float, length_m: float,
                                 conductor: str, section: float,
                                 is_three_phase: bool = True,
                                 voltage: float = 380.0) -> VoltageDropResult:
    """
    简化压降计算公式 (小截面电缆近似)。

    ΔU% = (P × L) / (C × S)

    C 为计算系数:
      - 三相铜芯 380V:  C≈77
      - 单相铜芯 220V:  C≈12.8
      - 三相铝芯 380V:  C≈46
      - 单相铝芯 220V:  C≈7.7

    参数:
        pe_kw: 传输功率 (kW)
        length_m: 距离 (m)
        conductor: "copper" | "aluminum"
        section: 截面 (mm²)
        is_three_phase: 是否三相
        voltage: 线电压 (V)

    返回:
        VoltageDropResult
    """
    # 选择计算系数 C
    if is_three_phase:
        c = 77.0 if conductor == "copper" else 46.0
    else:
        c = 12.8 if conductor == "copper" else 7.7

    delta_u_percent = (pe_kw * length_m) / (c * section)

    input_params = VoltageDropInput(
        i_js=0, length_m=length_m, conductor=conductor,
        voltage=voltage, section=section,
    )
    return VoltageDropResult(input_params, 0, delta_u_percent, 0, 0)


def _get_r0x0(params: VoltageDropInput) -> Tuple[float, float]:
    """获取阻抗参数"""
    from data.impedance import get_impedance
    return get_impedance(params.conductor, params.voltage_level, params.section)
