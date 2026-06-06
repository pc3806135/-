"""
电缆选型模块测试
"""
import pytest
from core.cable_select import (CableSelectionInput, select_cable,
                                get_all_feasible_sections, CableSelectionResult)


class TestCableSelectionInput:
    def test_default_input(self):
        inp = CableSelectionInput(i_js=180.0)
        assert inp.conductor == "copper"
        assert inp.insulation == "xlpe"
        assert inp.method == "bridge"
        assert inp.voltage_level == "0.6/1kV"

    def test_chinese_names(self):
        inp = CableSelectionInput(i_js=100, conductor="copper", insulation="xlpe")
        assert "铜芯" in inp.conductor_cn
        assert "XLPE" in inp.insulation_cn

    def test_invalid_voltage_level(self):
        with pytest.raises(ValueError):
            CableSelectionInput(i_js=100, conductor="copper", insulation="pvc",
                               method="air", voltage_level="100kV")


class TestSelectCable:
    def test_basic_selection_copper_xlpe(self):
        """基本选型: 铜芯 XLPE 桥架 180A"""
        inp = CableSelectionInput(
            i_js=180.0, conductor="copper", insulation="xlpe",
            method="bridge", voltage_level="0.6/1kV",
            ambient_temp=35.0, num_circuits=1,
        )
        result = select_cable(inp)
        assert result.is_valid
        assert result.selected_section > 0
        # 180A 应在 70mm² 和 95mm² 之间（XLPE 桥架）
        # 70mm² 载流量 228A，修正后应满足
        assert result.selected_section <= 95

    def test_aluminum_needs_larger_section(self):
        """铝芯需要更大截面"""
        inp_copper = CableSelectionInput(
            i_js=180.0, conductor="copper", insulation="xlpe", method="bridge",
        )
        inp_aluminum = CableSelectionInput(
            i_js=180.0, conductor="aluminum", insulation="xlpe", method="bridge",
        )
        r_cu = select_cable(inp_copper)
        r_al = select_cable(inp_aluminum)
        assert r_cu.is_valid
        assert r_al.is_valid
        # 铝芯应选更大的截面
        assert r_al.selected_section >= r_cu.selected_section

    def test_pvc_vs_xlpe(self):
        """PVC 绝缘载流量低于 XLPE，需要更大截面"""
        inp_xlpe = CableSelectionInput(
            i_js=150.0, conductor="copper", insulation="xlpe", method="air",
        )
        inp_pvc = CableSelectionInput(
            i_js=150.0, conductor="copper", insulation="pvc", method="air",
        )
        r_xlpe = select_cable(inp_xlpe)
        r_pvc = select_cable(inp_pvc)
        assert r_xlpe.is_valid
        assert r_pvc.is_valid
        assert r_pvc.selected_section >= r_xlpe.selected_section

    def test_high_temp_reduces_ampacity(self):
        """高温环境需要更大截面"""
        inp_normal = CableSelectionInput(
            i_js=200.0, conductor="copper", insulation="xlpe",
            method="bridge", ambient_temp=30.0,
        )
        inp_hot = CableSelectionInput(
            i_js=200.0, conductor="copper", insulation="xlpe",
            method="bridge", ambient_temp=50.0,
        )
        r_normal = select_cable(inp_normal)
        r_hot = select_cable(inp_hot)
        assert r_hot.selected_section >= r_normal.selected_section

    def test_multi_circuit_grouping(self):
        """多回路并列需要更大截面"""
        inp_single = CableSelectionInput(
            i_js=200.0, conductor="copper", insulation="xlpe",
            method="air", num_circuits=1,
        )
        inp_multi = CableSelectionInput(
            i_js=200.0, conductor="copper", insulation="xlpe",
            method="air", num_circuits=6,
        )
        r_single = select_cable(inp_single)
        r_multi = select_cable(inp_multi)
        assert r_multi.selected_section >= r_single.selected_section

    def test_overload_fails(self):
        """超载应返回失败"""
        inp = CableSelectionInput(
            i_js=5000.0, conductor="copper", insulation="xlpe",
            method="air", voltage_level="0.6/1kV",
        )
        result = select_cable(inp)
        assert not result.is_valid
        assert result.fail_reason != ""

    def test_correction_factors_in_result(self):
        """修正系数应在结果中包含"""
        inp = CableSelectionInput(i_js=100.0)
        result = select_cable(inp)
        assert "k_temp" in result.correction_factors
        assert "k_method" in result.correction_factors
        assert "k_group" in result.correction_factors
        assert "total" in result.correction_factors
        assert result.total_factor > 0

    def test_10kv_selection(self):
        """6/10kV 选型"""
        inp = CableSelectionInput(
            i_js=200.0, conductor="copper", insulation="xlpe",
            method="air", voltage_level="6/10kV",
        )
        result = select_cable(inp)
        assert result.is_valid


class TestFeasibleSections:
    def test_multiple_feasible(self):
        inp = CableSelectionInput(i_js=100.0)
        sections = get_all_feasible_sections(inp)
        assert len(sections) > 0
        # 应从小到大排序
        sizes = [s for s, _ in sections]
        assert sizes == sorted(sizes)
