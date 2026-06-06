"""
电流计算模块测试
"""
import math
import pytest
from core.current_calc import (LoadInfo, CurrentResult, calc_current,
                                calc_total_current, quick_calc_3ph, quick_calc_1ph)


class TestLoadInfo:
    def test_basic_load(self):
        load = LoadInfo("测试负荷", pe_kw=100, kx=0.85, cos_phi=0.85)
        assert load.name == "测试负荷"
        assert load.pe_kw == 100
        assert load.kx == 0.85
        assert load.cos_phi == 0.85

    def test_p_js_kw(self):
        load = LoadInfo("负荷", pe_kw=100, kx=0.8)
        assert load.p_js_kw == 80.0

    def test_q_js_kvar(self):
        load = LoadInfo("负荷", pe_kw=100, kx=1.0, cos_phi=0.8)  # tanφ=0.75
        expected_q = 100 * math.tan(math.acos(0.8))
        assert abs(load.q_js_kvar - expected_q) < 0.01

    def test_s_js_kva(self):
        load = LoadInfo("负荷", pe_kw=100, kx=1.0, cos_phi=0.8)
        assert abs(load.s_js_kva - 125.0) < 0.01

    def test_validation(self):
        with pytest.raises(ValueError):
            LoadInfo("无效", pe_kw=-100)
        with pytest.raises(ValueError):
            LoadInfo("无效", pe_kw=100, cos_phi=1.5)


class TestCalcCurrent:
    def test_three_phase_basic(self):
        """三相基本计算: 100kW, 380V, cosφ=1.0, Kx=1.0"""
        load = LoadInfo("测试", pe_kw=100, kx=1.0, cos_phi=1.0)
        result = calc_current(load, 380)
        # I = 100000 / (1.732 * 380 * 1.0) = 151.93A
        expected = 100000 / (math.sqrt(3) * 380 * 1.0)
        assert abs(result.i_js - expected) < 0.1
        assert result.is_three_phase is True

    def test_three_phase_with_kx_and_cos(self):
        """三相: 100kW, Kx=0.85, cosφ=0.85, 380V"""
        load = LoadInfo("测试", pe_kw=100, kx=0.85, cos_phi=0.85)
        result = calc_current(load, 380)
        # I = 85000 / (1.732 * 380 * 0.85) = 151.93A
        p_js = 100 * 0.85
        expected = p_js * 1000 / (math.sqrt(3) * 380 * 0.85)
        assert abs(result.i_js - expected) < 0.1

    def test_single_phase(self):
        """单相: 10kW, 220V 相电压, cosφ=1.0"""
        load = LoadInfo("测试", pe_kw=10, kx=1.0, cos_phi=1.0,
                        is_three_phase=False)
        result = calc_current(load, 380)  # 线电压380V → 相电压220V
        u_ph = 380 / math.sqrt(3)
        expected = 10 * 1000 / (u_ph * 1.0)
        assert abs(result.i_js - expected) < 0.1
        assert result.is_three_phase is False

    def test_different_voltage(self):
        """10kV 电压等级"""
        load = LoadInfo("高压", pe_kw=1000, kx=1.0, cos_phi=0.9)
        result = calc_current(load, 10000)
        expected = 1000000 / (math.sqrt(3) * 10000 * 0.9)
        assert abs(result.i_js - expected) < 0.1

    def test_result_fields(self):
        """验证结果对象字段完整"""
        load = LoadInfo("测试", pe_kw=100, kx=0.85, cos_phi=0.85)
        result = calc_current(load, 380)
        assert result.i_js > 0
        assert result.p_js == 85.0
        assert result.q_js > 0
        assert result.s_js == 100.0
        assert result.voltage == 380
        assert result.cos_phi == 0.85


class TestQuickCalc:
    def test_quick_3ph(self):
        result = quick_calc_3ph(pe_kw=100, voltage=380, cos_phi=1.0, kx=1.0)
        expected = 100000 / (math.sqrt(3) * 380)
        assert abs(result.i_js - expected) < 0.1

    def test_quick_1ph(self):
        result = quick_calc_1ph(pe_kw=10, voltage=380, cos_phi=1.0, kx=1.0)
        u_ph = 380 / math.sqrt(3)
        expected = 10000 / u_ph
        assert abs(result.i_js - expected) < 0.1


class TestTotalCurrent:
    def test_multiple_loads(self):
        loads = [
            LoadInfo("A", pe_kw=50, kx=0.8, cos_phi=0.85),
            LoadInfo("B", pe_kw=30, kx=0.7, cos_phi=0.8),
            LoadInfo("C", pe_kw=20, kx=0.9, cos_phi=0.9),
        ]
        total, individuals = calc_total_current(loads, 380, ks=0.9)

        assert len(individuals) == 3
        assert total.i_js > 0
        assert total.load_name == "总计"
        # 各负荷结果
        assert individuals[0].p_js == 40.0  # 50*0.8
        assert individuals[1].p_js == 21.0  # 30*0.7
        assert individuals[2].p_js == 18.0  # 20*0.9

    def test_ks_factor(self):
        """同时系数 Ks < 1 应减小总电流"""
        loads = [LoadInfo("A", pe_kw=100, kx=1.0, cos_phi=1.0)]
        total_full, _ = calc_total_current(loads, 380, ks=1.0)
        total_half, _ = calc_total_current(loads, 380, ks=0.5)
        assert total_full.i_js > total_half.i_js
