"""
核心计算模块
"""
from .current_calc import (LoadInfo, CurrentResult, calc_current,
                           calc_total_current, quick_calc_3ph, quick_calc_1ph)
from .cable_select import (CableSelectionInput, CableSelectionResult,
                           select_cable, get_all_feasible_sections)
from .voltage_drop import (VoltageDropInput, VoltageDropResult,
                           calc_voltage_drop_3ph, calc_voltage_drop_1ph,
                           calc_voltage_drop_simplified, ALLOWABLE_VD_LIMITS)
from .short_circuit import (ShortCircuitInput, ShortCircuitResult,
                            check_short_circuit, calc_required_section)

__all__ = [
    # 电流计算
    "LoadInfo", "CurrentResult", "calc_current", "calc_total_current",
    "quick_calc_3ph", "quick_calc_1ph",
    # 电缆选型
    "CableSelectionInput", "CableSelectionResult", "select_cable",
    "get_all_feasible_sections",
    # 压降计算
    "VoltageDropInput", "VoltageDropResult",
    "calc_voltage_drop_3ph", "calc_voltage_drop_1ph",
    "calc_voltage_drop_simplified", "ALLOWABLE_VD_LIMITS",
    # 短路校验
    "ShortCircuitInput", "ShortCircuitResult",
    "check_short_circuit", "calc_required_section",
]
