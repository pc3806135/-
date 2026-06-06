"""
模块②: 电缆自动选型

符合 GB 50217-2018《电力工程电缆设计标准》

选型流程:
  计算电流 I_js → 环境温度修正 → 并列回路修正 → 敷设修正
  → 查载流量表 → 匹配最小截面
"""

from typing import Tuple, List, Optional
from data.ampacity import (get_cable_data, STANDARD_SECTIONS,
                           get_available_voltage_levels)
from data.correction_factors import (get_temp_correction,
                                      get_grouping_correction,
                                      get_method_factor)


class CableSelectionInput:
    """电缆选型输入参数"""
    def __init__(self, i_js: float,
                 conductor: str = "copper",
                 insulation: str = "xlpe",
                 method: str = "bridge",
                 voltage_level: str = "0.6/1kV",
                 ambient_temp: float = 35.0,
                 num_circuits: int = 1):
        """
        参数:
            i_js: 计算电流 (A)
            conductor: "copper" | "aluminum"
            insulation: "pvc" | "xlpe"
            method: "air" | "conduit" | "bridge" | "buried"
            voltage_level: "0.6/1kV" | "6/10kV"
            ambient_temp: 环境温度 (°C)
            num_circuits: 并列回路数
        """
        self.i_js = i_js
        self.conductor = conductor
        self.insulation = insulation
        self.method = method
        self.voltage_level = voltage_level
        self.ambient_temp = ambient_temp
        self.num_circuits = num_circuits

        # 校验电压等级
        available_levels = get_available_voltage_levels(conductor, insulation, method)
        if voltage_level not in available_levels:
            raise ValueError(
                f"不支持的电压等级: {voltage_level}。"
                f"可选: {available_levels}"
            )

    @property
    def conductor_cn(self) -> str:
        return "铜芯" if self.conductor == "copper" else "铝芯"

    @property
    def insulation_cn(self) -> str:
        return "PVC" if self.insulation == "pvc" else "XLPE"

    @property
    def method_cn(self) -> str:
        names = {"air": "空气中明敷", "conduit": "穿管敷设",
                 "bridge": "桥架敷设", "buried": "直埋敷设"}
        return names.get(self.method, self.method)


class CableSelectionResult:
    """电缆选型结果"""
    def __init__(self, input_params: CableSelectionInput,
                 selected_section: float,
                 corrected_ampacity: float,
                 raw_ampacity: float,
                 correction_factors: dict,
                 fail_reason: str = ""):
        self.input = input_params
        self.selected_section = selected_section  # 选中的截面 (mm²)
        self.corrected_ampacity = corrected_ampacity  # 修正后载流量 (A)
        self.raw_ampacity = raw_ampacity          # 基准载流量 (A)
        self.correction_factors = correction_factors  # 各修正系数
        self.fail_reason = fail_reason            # 失败原因（若失败）

        # 修正后的电缆载流量
        self.all_corrected = {
            s: raw * correction_factors["total"]
            for s, raw in correction_factors.get("raw_table", {}).items()
        }

    @property
    def is_valid(self) -> bool:
        return self.selected_section > 0 and not self.fail_reason

    @property
    def total_factor(self) -> float:
        return self.correction_factors.get("total", 1.0)

    def __repr__(self):
        if not self.is_valid:
            return f"<选型失败: {self.fail_reason}>"
        return (f"<选型: {self.input.conductor_cn} "
                f"{self.input.insulation_cn} "
                f"{self.selected_section}mm² "
                f"(修正载流量 {self.corrected_ampacity:.0f}A)>")


def select_cable(params: CableSelectionInput) -> CableSelectionResult:
    """
    根据计算电流和敷设条件，自动匹配电缆截面。

    逻辑:
    1. 获取载流量表
    2. 计算综合修正系数 K = Kθ × K₁ × K₂
    3. 要求修正载流量 ≥ I_js
    4. 查表匹配最小截面

    参数:
        params: CableSelectionInput

    返回:
        CableSelectionResult
    """
    # 1. 获取载流量表
    ampacity_table = get_cable_data(
        params.conductor, params.insulation,
        params.method, params.voltage_level
    )

    # 2. 计算修正系数
    k_temp = get_temp_correction(params.insulation, params.method,
                                  params.ambient_temp)
    k_method = get_method_factor(params.method)
    k_group = get_grouping_correction(params.method, params.num_circuits)

    k_total = k_temp * k_method * k_group

    # 3. 要求电流 ≥ I_js / K_total (修正后的载流量要满足计算电流)
    required_ampacity = params.i_js / k_total if k_total > 0 else float("inf")

    # 4. 查表匹配
    selected = _find_min_section(ampacity_table, required_ampacity)

    correction_factors = {
        "k_temp": k_temp,
        "k_method": k_method,
        "k_group": k_group,
        "total": k_total,
        "raw_table": ampacity_table,
    }

    if selected is None:
        max_section = max(ampacity_table.keys()) if ampacity_table else 0
        return CableSelectionResult(
            input_params=params,
            selected_section=0,
            corrected_ampacity=0,
            raw_ampacity=ampacity_table.get(max_section, 0),
            correction_factors=correction_factors,
            fail_reason=f"电缆截面不足：最大截面 {max_section}mm² 仍不满足要求电流 {required_ampacity:.1f}A"
        )

    raw_ampacity = ampacity_table[selected]
    corrected_ampacity = raw_ampacity * k_total

    return CableSelectionResult(
        input_params=params,
        selected_section=selected,
        corrected_ampacity=corrected_ampacity,
        raw_ampacity=raw_ampacity,
        correction_factors=correction_factors,
    )


def _find_min_section(ampacity_table: dict, required_ampacity: float) -> Optional[float]:
    """在载流量表中查找满足要求的最小截面"""
    for section in sorted(ampacity_table.keys()):
        if ampacity_table[section] >= required_ampacity:
            return section
    return None


def get_all_feasible_sections(params: CableSelectionInput) -> List[Tuple[float, float]]:
    """
    获取所有满足要求的截面选项。

    返回:
        [(section, corrected_ampacity), ...] 列表，从小到大排序
    """
    ampacity_table = get_cable_data(
        params.conductor, params.insulation,
        params.method, params.voltage_level
    )

    k_total = (
        get_temp_correction(params.insulation, params.method, params.ambient_temp)
        * get_method_factor(params.method)
        * get_grouping_correction(params.method, params.num_circuits)
    )

    required = params.i_js / k_total
    feasible = []

    for section in sorted(ampacity_table.keys()):
        if ampacity_table[section] >= required:
            feasible.append((section, round(ampacity_table[section] * k_total, 1)))

    return feasible
