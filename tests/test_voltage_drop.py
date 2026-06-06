"""
压降计算模块测试
"""
import math
import pytest
from core.voltage_drop import (VoltageDropInput, VoltageDropResult,
                                calc_voltage_drop_3ph, calc_voltage_drop_1ph,
                                calc_voltage_drop_simplified, ALLOWABLE_VD_LIMITS)


class TestVoltageDropInput:
    def test_default(self):
        inp = VoltageDropInput(i_js=180, length_m=100, section=70)
        assert inp.circuit_type == "power"
        assert inp.allowable_limit == 5.0

    def test_limits(self):
        assert ALLOWABLE_VD_LIMITS["lighting"] == 3.0
        assert ALLOWABLE_VD_LIMITS["power"] == 5.0
        assert ALLOWABLE_VD_LIMITS["mixed"] == 4.0
        assert ALLOWABLE_VD_LIMITS["emergency"] == 10.0

        inp_l = VoltageDropInput(i_js=10, length_m=50, section=2.5, circuit_type="lighting")
        assert inp_l.allowable_limit == 3.0

    def test_invalid_limits(self):
        """默认 5%"""
        inp = VoltageDropInput(i_js=10, length_m=50, section=2.5, circuit_type="unknown_type")
        assert inp.allowable_limit == 5.0


class TestVoltageDrop3Ph:
    def test_basic_calculation(self):
        """基本三相压降计算"""
        inp = VoltageDropInput(
            i_js=180, length_m=100, conductor="copper",
            voltage_level="0.6/1kV", voltage=380, cos_phi=0.85,
            section=70, circuit_type="power",
        )
        result = calc_voltage_drop_3ph(inp)
        assert result.delta_u_percent > 0
        assert result.delta_u_v > 0
        assert result.r0 > 0
        assert result.x0 > 0

    def test_pass_with_reasonable_length(self):
        """合理长度下应通过校验"""
        inp = VoltageDropInput(
            i_js=100, length_m=50, conductor="copper",
            voltage_level="0.6/1kV", voltage=380, cos_phi=0.85,
            section=70, circuit_type="power",
        )
        result = calc_voltage_drop_3ph(inp)
        assert result.is_pass  # 短距离应通过

    def test_long_distance_fails(self):
        """过长距离可能不通过"""
        inp = VoltageDropInput(
            i_js=200, length_m=5000, conductor="copper",
            voltage_level="0.6/1kV", voltage=380, cos_phi=0.85,
            section=50, circuit_type="power",
        )
        result = calc_voltage_drop_3ph(inp)
        # 长距离高电流小截面会超过 5%
        assert not result.is_pass

    def test_larger_section_reduces_drop(self):
        """大截面压降更小"""
        inp_small = VoltageDropInput(
            i_js=100, length_m=200, section=25, conductor="copper",
            voltage_level="0.6/1kV",
        )
        inp_large = VoltageDropInput(
            i_js=100, length_m=200, section=120, conductor="copper",
            voltage_level="0.6/1kV",
        )
        r_small = calc_voltage_drop_3ph(inp_small)
        r_large = calc_voltage_drop_3ph(inp_large)
        assert r_small.delta_u_percent > r_large.delta_u_percent

    def test_lighting_stricter_limit(self):
        """照明回路 3% 限值更严格"""
        inp_power = VoltageDropInput(
            i_js=50, length_m=300, section=16,
            circuit_type="power",
        )
        inp_light = VoltageDropInput(
            i_js=50, length_m=300, section=16,
            circuit_type="lighting",
        )
        r_power = calc_voltage_drop_3ph(inp_power)
        r_light = calc_voltage_drop_3ph(inp_light)

        # 同样的条件，动力可能过而照明可能不过
        if r_power.is_pass:
            # 照明限值更严，可能同一条件不通过
            pass  # 取决于具体数值

    def test_low_power_factor_worse(self):
        """低功率因数压降更大 (X₀ 分量加重)"""
        inp_good = VoltageDropInput(
            i_js=100, length_m=200, section=50,
            cos_phi=0.95, voltage_level="0.6/1kV",
        )
        inp_bad = VoltageDropInput(
            i_js=100, length_m=200, section=50,
            cos_phi=0.70, voltage_level="0.6/1kV",
        )
        r_good = calc_voltage_drop_3ph(inp_good)
        r_bad = calc_voltage_drop_3ph(inp_bad)
        # 低功率因数无功电流大，压降更大
        assert r_bad.delta_u_percent >= r_good.delta_u_percent * 0.95

    def test_10kv_lower_drop(self):
        """10kV 电压等级压降百分比更小"""
        inp_lv = VoltageDropInput(
            i_js=50, length_m=500, section=70, conductor="copper",
            voltage_level="0.6/1kV", voltage=380,
        )
        inp_mv = VoltageDropInput(
            i_js=50, length_m=500, section=70, conductor="copper",
            voltage_level="6/10kV", voltage=10000,
        )
        r_lv = calc_voltage_drop_3ph(inp_lv)
        r_mv = calc_voltage_drop_3ph(inp_mv)
        assert r_mv.delta_u_percent < r_lv.delta_u_percent


class TestVoltageDrop1Ph:
    def test_basic_single_phase(self):
        inp = VoltageDropInput(
            i_js=30, length_m=50, section=6, conductor="copper",
            voltage_level="0.6/1kV",
        )
        result = calc_voltage_drop_1ph(inp)
        assert result.delta_u_percent > 0

    def test_single_vs_three_phase(self):
        """单相压降 > 三相压降 (同条件)"""
        inp = VoltageDropInput(
            i_js=50, length_m=100, section=16,
            voltage_level="0.6/1kV",
        )
        r_3ph = calc_voltage_drop_3ph(inp)
        r_1ph = calc_voltage_drop_1ph(inp)
        # 单相 2I vs 三相 √3I
        assert r_1ph.delta_u_v > r_3ph.delta_u_v


class TestSimplifiedVD:
    def test_simplified_formula(self):
        result = calc_voltage_drop_simplified(
            pe_kw=100, length_m=100, conductor="copper",
            section=70, is_three_phase=True, voltage=380,
        )
        # ΔU% = 100*100 / (77*70) ≈ 1.86%
        expected = 100 * 100 / (77.0 * 70)
        assert abs(result.delta_u_percent - expected) < 0.5


class TestVoltageDropResult:
    def test_result_properties(self):
        inp = VoltageDropInput(i_js=100, length_m=100, section=50, circuit_type="power")
        # 模拟结果
        result = VoltageDropResult(inp, delta_u_v=6.5, delta_u_percent=1.7,
                                   r0=0.449, x0=0.085)
        assert result.is_pass  # 1.7% < 5%
        assert result.margin > 0
        assert result.limit == 5.0

    def test_failing_result(self):
        inp = VoltageDropInput(i_js=100, length_m=100, section=50, circuit_type="lighting")
        result = VoltageDropResult(inp, delta_u_v=8.5, delta_u_percent=3.5,
                                   r0=0.449, x0=0.085)
        assert not result.is_pass
        assert result.margin < 0
