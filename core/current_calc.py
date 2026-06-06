"""
模块①: 电流计算

符合 GB 50054-2011《低压配电设计规范》

支持:
- 单相/三相平衡负荷
- 需用系数 Kx
- 同时系数 Ks (多负载)
- 功率因数补偿前后对比
"""

import math
from typing import List, Dict, Tuple
from utils import kw_to_w, validate_positive, validate_cos_phi


class LoadInfo:
    """单个负荷信息"""
    def __init__(self, name: str, pe_kw: float, kx: float = 1.0,
                 cos_phi: float = 0.85, is_three_phase: bool = True):
        validate_positive(pe_kw, "设备功率")
        validate_cos_phi(cos_phi)
        self.name = name
        self.pe_kw = pe_kw        # 设备功率 (kW)
        self.kx = kx              # 需用系数
        self.cos_phi = cos_phi    # 功率因数
        self.is_three_phase = is_three_phase

    @property
    def p_js_kw(self) -> float:
        """计算有功功率 (kW)"""
        return self.pe_kw * self.kx

    @property
    def q_js_kvar(self) -> float:
        """计算无功功率 (kvar)"""
        return self.p_js_kw * math.tan(math.acos(self.cos_phi))

    @property
    def s_js_kva(self) -> float:
        """计算视在功率 (kVA)"""
        return self.p_js_kw / self.cos_phi


class CurrentResult:
    """电流计算结果"""
    def __init__(self, load_name: str, i_js: float, p_js: float,
                 q_js: float, s_js: float, voltage: float,
                 cos_phi: float, is_three_phase: bool):
        self.load_name = load_name
        self.i_js = i_js            # 计算电流 (A)
        self.p_js = p_js            # 有功功率 (kW)
        self.q_js = q_js            # 无功功率 (kvar)
        self.s_js = s_js            # 视在功率 (kVA)
        self.voltage = voltage      # 线电压 (V)
        self.cos_phi = cos_phi
        self.is_three_phase = is_three_phase

    def __repr__(self):
        phase_str = "三相" if self.is_three_phase else "单相"
        return (f"<{self.load_name}: I_js={self.i_js:.2f}A, "
                f"P_js={self.p_js:.2f}kW, {phase_str}>")


def calc_current(load: LoadInfo, voltage: float = 380.0) -> CurrentResult:
    """
    计算单个负荷的计算电流。

    三相: I_js = P_js / (√3 × U_n × cosφ)
    单相: I_js = P_js / (U_ph × cosφ)

    参数:
        load: LoadInfo 负荷对象
        voltage: 线电压 (V), 默认 380V

    返回:
        CurrentResult
    """
    p_js = load.p_js_kw
    q_js = load.q_js_kvar
    s_js = load.s_js_kva
    cos_phi = load.cos_phi

    if load.is_three_phase:
        # 三相: U_n = 线电压
        i_js = p_js * 1000 / (math.sqrt(3) * voltage * cos_phi)
    else:
        # 单相: U_ph = 相电压 = 线电压 / √3
        u_ph = voltage / math.sqrt(3)
        i_js = p_js * 1000 / (u_ph * cos_phi)

    return CurrentResult(
        load_name=load.name,
        i_js=i_js,
        p_js=p_js,
        q_js=q_js,
        s_js=s_js,
        voltage=voltage,
        cos_phi=cos_phi,
        is_three_phase=load.is_three_phase,
    )


def calc_total_current(loads: List[LoadInfo], voltage: float = 380.0,
                       ks: float = 1.0) -> Tuple[CurrentResult, List[CurrentResult]]:
    """
    计算多个负荷的总计算电流 (计入同时系数 Ks)。

    参数:
        loads: 负荷列表
        voltage: 线电压 (V)
        ks: 同时系数 (0~1)

    返回:
        (total_result, individual_results)
    """
    # 逐个计算
    results = [calc_current(load, voltage) for load in loads]

    # 汇总
    total_p = sum(r.p_js for r in results) * ks
    total_q = sum(r.q_js for r in results) * ks
    total_s = math.sqrt(total_p ** 2 + total_q ** 2)

    # 加权平均功率因数
    avg_cos_phi = total_p / total_s if total_s > 0 else 1.0

    # 假设所有负荷同相别 (三相)，合并后按三相计算
    total_i = total_p * 1000 / (math.sqrt(3) * voltage * avg_cos_phi)

    total_result = CurrentResult(
        load_name="总计",
        i_js=total_i,
        p_js=total_p,
        q_js=total_q,
        s_js=total_s,
        voltage=voltage,
        cos_phi=avg_cos_phi,
        is_three_phase=True,
    )

    return total_result, results


# ============================================================
# 便捷函数
# ============================================================

def quick_calc_3ph(pe_kw: float, voltage: float = 380.0,
                   cos_phi: float = 0.85, kx: float = 1.0) -> CurrentResult:
    """快捷三相电流计算"""
    load = LoadInfo("负荷", pe_kw, kx=kx, cos_phi=cos_phi)
    return calc_current(load, voltage)


def quick_calc_1ph(pe_kw: float, voltage: float = 380.0,
                   cos_phi: float = 0.85, kx: float = 1.0) -> CurrentResult:
    """快捷单相电流计算"""
    load = LoadInfo("负荷", pe_kw, kx=kx, cos_phi=cos_phi, is_three_phase=False)
    return calc_current(load, voltage)
