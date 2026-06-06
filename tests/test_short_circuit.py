"""
短路热稳定校验模块测试
"""
import math
import pytest
from core.short_circuit import (ShortCircuitInput, ShortCircuitResult,
                                 check_short_circuit, calc_required_section)
from data.k_values import get_k_value


class TestKValues:
    def test_copper_pvc(self):
        assert get_k_value("copper", "pvc") == 115

    def test_copper_xlpe(self):
        assert get_k_value("copper", "xlpe") == 143

    def test_aluminum_pvc(self):
        assert get_k_value("aluminum", "pvc") == 76

    def test_aluminum_xlpe(self):
        assert get_k_value("aluminum", "xlpe") == 95

    def test_invalid(self):
        with pytest.raises(ValueError):
            get_k_value("copper", "invalid")


class TestShortCircuit:
    def test_basic_check_pass(self):
        """基本校验: 25kA, 0.2s, 铜芯 XLPE, 120mm²"""
        params = ShortCircuitInput(
            ik_a=25000, t_s=0.2, conductor="copper",
            insulation="xlpe", selected_section=120,
        )
        result = check_short_circuit(params)
        # S_min = 25000 * √0.2 / 143 ≈ 78.2 mm²
        expected_s_min = 25000 * math.sqrt(0.2) / 143
        assert abs(result.s_min - expected_s_min) < 0.5
        assert result.is_pass  # 120 > 78
        assert result.k == 143

    def test_small_section_fails(self):
        """截面过小应不通过"""
        params = ShortCircuitInput(
            ik_a=25000, t_s=0.2, conductor="copper",
            insulation="xlpe", selected_section=50,
        )
        result = check_short_circuit(params)
        assert not result.is_pass
        assert result.required_section > result.input.selected_section

    def test_copper_better_than_aluminum(self):
        """铜芯 K=143 > 铝芯 K=95，铜芯 S_min 更小"""
        s_min_cu = calc_required_section(25000, 0.2, "copper", "xlpe")
        s_min_al = calc_required_section(25000, 0.2, "aluminum", "xlpe")
        assert s_min_cu < s_min_al

    def test_xlpe_better_than_pvc(self):
        """XLPE K=143 > PVC K=115，XLPE S_min 更小"""
        s_min_xlpe = calc_required_section(25000, 0.2, "copper", "xlpe")
        s_min_pvc = calc_required_section(25000, 0.2, "copper", "pvc")
        assert s_min_xlpe < s_min_pvc

    def test_longer_duration_needs_larger(self):
        """持续时间越长，S_min 越大"""
        s_short = calc_required_section(25000, 0.1, "copper", "xlpe")
        s_long = calc_required_section(25000, 0.5, "copper", "xlpe")
        assert s_long > s_short

    def test_larger_current_needs_larger(self):
        """短路电流越大，S_min 越大"""
        s_small = calc_required_section(10000, 0.2, "copper", "xlpe")
        s_large = calc_required_section(40000, 0.2, "copper", "xlpe")
        assert s_large > s_small

    def test_required_section_round_up(self):
        """需要向上取标准截面"""
        params = ShortCircuitInput(
            ik_a=30000, t_s=0.3, conductor="copper",
            insulation="pvc", selected_section=70,
        )
        result = check_short_circuit(params)
        assert not result.is_pass
        assert result.required_section > result.input.selected_section
        # 应取最近的标准截面
        from data.ampacity import STANDARD_SECTIONS
        assert result.required_section in STANDARD_SECTIONS


class TestQuickCalc:
    def test_quick_function(self):
        s_min = calc_required_section(25000, 0.2, "copper", "xlpe")
        expected = 25000 * math.sqrt(0.2) / 143
        assert abs(s_min - expected) < 0.01


class TestShortCircuitResult:
    def test_pass_properties(self):
        """通过时的属性"""
        inp = ShortCircuitInput(ik_a=20000, t_s=0.1, conductor="copper",
                               insulation="xlpe", selected_section=120)
        result = check_short_circuit(inp)
        assert result.is_pass
        assert result.margin > 0
        assert result.required_section == 120  # 不需升级

    def test_fail_properties(self):
        """不通过时需要升级截面"""
        inp = ShortCircuitInput(ik_a=40000, t_s=0.3, conductor="aluminum",
                               insulation="pvc", selected_section=50)
        result = check_short_circuit(inp)
        assert not result.is_pass
        assert result.margin < 0
        assert result.required_section > 50
