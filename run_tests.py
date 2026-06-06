"""直接运行测试的脚本"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("电气计算工具 - 模块测试")
print("=" * 60)

errors = []

# ─── 测试电流计算模块 ───
print("\n[1/4] 测试电流计算模块...")
try:
    from core.current_calc import (LoadInfo, calc_current,
                                    calc_total_current, quick_calc_3ph)
    import math

    # 三相基本计算
    load = LoadInfo("测试", pe_kw=100, kx=1.0, cos_phi=1.0)
    result = calc_current(load, 380)
    expected = 100000 / (math.sqrt(3) * 380 * 1.0)
    assert abs(result.i_js - expected) < 0.1, f"I_js={result.i_js}, expected={expected}"
    assert result.is_three_phase

    # 需用系数 + 功率因数
    load2 = LoadInfo("测试2", pe_kw=100, kx=0.85, cos_phi=0.85)
    r2 = calc_current(load2, 380)
    assert r2.p_js == 85.0
    assert r2.i_js > 0

    # 单相
    load3 = LoadInfo("单相", pe_kw=10, kx=1.0, cos_phi=1.0, is_three_phase=False)
    r3 = calc_current(load3, 380)
    assert r3.i_js > 0
    assert not r3.is_three_phase

    # 多负荷汇总
    loads = [
        LoadInfo("A", pe_kw=50, kx=0.8, cos_phi=0.85),
        LoadInfo("B", pe_kw=30, kx=0.7, cos_phi=0.8),
    ]
    total, ind = calc_total_current(loads, 380, ks=0.9)
    assert len(ind) == 2
    assert total.i_js > 0

    # 电压等级
    r4 = quick_calc_3ph(pe_kw=1000, voltage=10000, cos_phi=0.9)
    assert r4.i_js > 0

    print("  [PASS] 电流计算: 全部通过 (6 tests)")
except Exception as e:
    errors.append(f"电流计算: {e}")
    print(f"  [FAIL] 失败: {e}")

# ─── 测试电缆选型模块 ───
print("\n[2/4] 测试电缆选型模块...")
try:
    from core.cable_select import (CableSelectionInput, select_cable,
                                    get_all_feasible_sections)

    # 基本选型
    inp = CableSelectionInput(i_js=180.0, conductor="copper", insulation="xlpe",
                              method="bridge", voltage_level="0.6/1kV")
    result = select_cable(inp)
    assert result.is_valid
    assert result.selected_section > 0

    # 铝芯需要更大截面
    inp_al = CableSelectionInput(i_js=180.0, conductor="aluminum", insulation="xlpe",
                                  method="bridge")
    r_al = select_cable(inp_al)
    assert r_al.selected_section >= result.selected_section

    # 高温环境
    inp_hot = CableSelectionInput(i_js=200.0, conductor="copper", insulation="xlpe",
                                   method="bridge", ambient_temp=50.0)
    inp_cool = CableSelectionInput(i_js=200.0, conductor="copper", insulation="xlpe",
                                    method="bridge", ambient_temp=30.0)
    r_hot = select_cable(inp_hot)
    r_cool = select_cable(inp_cool)
    assert r_hot.selected_section >= r_cool.selected_section

    # 多回路
    inp_m = CableSelectionInput(i_js=200.0, num_circuits=6, method="air")
    inp_s = CableSelectionInput(i_js=200.0, num_circuits=1, method="air")
    r_m = select_cable(inp_m)
    r_s = select_cable(inp_s)
    assert r_m.selected_section >= r_s.selected_section

    # 修正系数
    assert result.total_factor > 0
    assert "k_temp" in result.correction_factors

    # 可选截面
    secs = get_all_feasible_sections(inp)
    assert len(secs) > 0

    # 超载失败
    inp_over = CableSelectionInput(i_js=5000.0)
    r_over = select_cable(inp_over)
    assert not r_over.is_valid

    # 6/10kV
    inp_10kv = CableSelectionInput(i_js=200.0, conductor="copper", insulation="xlpe",
                                    method="air", voltage_level="6/10kV")
    r_10kv = select_cable(inp_10kv)
    assert r_10kv.is_valid

    print("  [PASS] 电缆选型: 全部通过 (9 tests)")
except Exception as e:
    errors.append(f"电缆选型: {e}")
    print(f"  [FAIL] 失败: {e}")

# ─── 测试压降计算模块 ───
print("\n[3/4] 测试压降计算模块...")
try:
    from core.voltage_drop import (VoltageDropInput, calc_voltage_drop_3ph,
                                    calc_voltage_drop_1ph, ALLOWABLE_VD_LIMITS)

    # 基本三相计算
    inp_vd = VoltageDropInput(i_js=180, length_m=100, section=70,
                               conductor="copper", voltage_level="0.6/1kV",
                               voltage=380, cos_phi=0.85, circuit_type="power")
    r_vd = calc_voltage_drop_3ph(inp_vd)
    assert r_vd.delta_u_percent > 0
    assert r_vd.r0 > 0
    assert r_vd.x0 > 0

    # 合理距离通过
    inp_ok = VoltageDropInput(i_js=100, length_m=50, section=70, circuit_type="power")
    r_ok = calc_voltage_drop_3ph(inp_ok)
    assert r_ok.is_pass

    # 超长距离不通过
    inp_long = VoltageDropInput(i_js=200, length_m=5000, section=50,
                                 circuit_type="power")
    r_long = calc_voltage_drop_3ph(inp_long)
    assert not r_long.is_pass

    # 大截面压降更小
    inp_s = VoltageDropInput(i_js=100, length_m=200, section=25)
    inp_l = VoltageDropInput(i_js=100, length_m=200, section=120)
    r_s = calc_voltage_drop_3ph(inp_s)
    r_l = calc_voltage_drop_3ph(inp_l)
    assert r_s.delta_u_percent > r_l.delta_u_percent

    # 10kV 压降更小
    inp_10 = VoltageDropInput(i_js=50, length_m=500, section=70,
                               voltage=10000, voltage_level="6/10kV")
    r_10 = calc_voltage_drop_3ph(inp_10)
    assert r_10.delta_u_percent < 0.5  # 10kV 下压降应很小

    # 单相
    r_1ph = calc_voltage_drop_1ph(inp_vd)
    assert r_1ph.delta_u_percent > 0

    # 限值配置
    assert ALLOWABLE_VD_LIMITS["lighting"] == 3.0
    assert ALLOWABLE_VD_LIMITS["power"] == 5.0

    # 裕量和判定
    assert r_vd.is_pass
    assert r_vd.margin > 0

    print("  [PASS] 压降计算: 全部通过 (8 tests)")
except Exception as e:
    errors.append(f"压降计算: {e}")
    print(f"  [FAIL] 失败: {e}")

# ─── 测试短路热稳定模块 ───
print("\n[4/4] 测试短路热稳定模块...")
try:
    from core.short_circuit import (ShortCircuitInput, check_short_circuit,
                                     calc_required_section)
    import math

    # 基本校验通过
    params = ShortCircuitInput(ik_a=25000, t_s=0.2, conductor="copper",
                               insulation="xlpe", selected_section=120)
    result = check_short_circuit(params)
    expected_s_min = 25000 * math.sqrt(0.2) / 143
    assert abs(result.s_min - expected_s_min) < 0.5
    assert result.is_pass

    # 截面不足
    params_small = ShortCircuitInput(ik_a=25000, t_s=0.2, conductor="copper",
                                      insulation="xlpe", selected_section=50)
    r_small = check_short_circuit(params_small)
    assert not r_small.is_pass
    assert r_small.required_section > 50

    # 铜芯优于铝芯
    s_cu = calc_required_section(25000, 0.2, "copper", "xlpe")
    s_al = calc_required_section(25000, 0.2, "aluminum", "xlpe")
    assert s_cu < s_al

    # XLPE 优于 PVC
    s_xlpe = calc_required_section(25000, 0.2, "copper", "xlpe")
    s_pvc = calc_required_section(25000, 0.2, "copper", "pvc")
    assert s_xlpe < s_pvc

    # 时间越长 S_min 越大
    assert calc_required_section(25000, 0.5, "copper", "xlpe") > \
           calc_required_section(25000, 0.1, "copper", "xlpe")

    # 电流越大 S_min 越大
    assert calc_required_section(30000, 0.2, "copper", "xlpe") > \
           calc_required_section(10000, 0.2, "copper", "xlpe")

    # K 值
    from data.k_values import get_k_value
    assert get_k_value("copper", "xlpe") == 143
    assert get_k_value("copper", "pvc") == 115

    # 裕量和升级
    assert result.margin > 0
    assert result.required_section == 120  # 不需升级

    print("  [PASS] 短路校验: 全部通过 (8 tests)")
except Exception as e:
    errors.append(f"短路校验: {e}")
    print(f"  [FAIL] 失败: {e}")

# ─── 数据模块测试 ───
print("\n[附加] 测试数据模块...")
try:
    from data.ampacity import (get_cable_data, STANDARD_SECTIONS)

    # 载流量表可访问
    tbl = get_cable_data("copper", "xlpe", "bridge", "0.6/1kV")
    assert len(tbl) > 0

    # 标准截面
    assert 1.5 in STANDARD_SECTIONS
    assert 630 in STANDARD_SECTIONS
    assert len(STANDARD_SECTIONS) == 19

    from data.impedance import get_impedance
    r0, x0 = get_impedance("copper", "0.6/1kV", 70)
    assert r0 > 0
    assert x0 > 0

    from data.correction_factors import (get_temp_correction,
                                          get_grouping_correction)
    assert get_temp_correction("xlpe", "air", 35) < 1.0
    assert get_temp_correction("xlpe", "air", 10) > 1.0
    assert get_grouping_correction("air", 2) < 1.0

    from data.k_values import K_VALUES
    assert ("copper", "xlpe") in K_VALUES

    print("  [PASS] 数据模块: 全部通过")
except Exception as e:
    errors.append(f"数据模块: {e}")
    print(f"  [FAIL] 失败: {e}")

# ─── 输出模块测试 ───
print("\n[附加] 测试输出模块...")
try:
    from core.current_calc import quick_calc_3ph
    from core.cable_select import CableSelectionInput, select_cable
    from output.terminal import (print_current_result, print_cable_result,
                                  print_voltage_drop_result,
                                  print_short_circuit_result)
    from core.voltage_drop import VoltageDropInput, calc_voltage_drop_3ph
    from core.short_circuit import ShortCircuitInput, check_short_circuit

    # 验证所有导入成功
    cr = quick_calc_3ph(100)
    inp_c = CableSelectionInput(i_js=180)
    r_c = select_cable(inp_c)
    inp_v = VoltageDropInput(i_js=180, length_m=100, section=70)
    r_v = calc_voltage_drop_3ph(inp_v)
    inp_s = ShortCircuitInput(ik_a=25000, t_s=0.2, conductor="copper",
                              insulation="xlpe", selected_section=120)
    r_s = check_short_circuit(inp_s)

    # 验证 Excel/PDF 导出模块可导入
    from output.excel_export import export_excel
    from output.pdf_export import export_pdf

    print("  [PASS] 输出模块: 全部可导入 (6 modules)")
except Exception as e:
    errors.append(f"输出模块: {e}")
    print(f"  [FAIL] 失败: {e}")

# ─── 总结 ───
print()
print("=" * 60)
if errors:
    print(f"[FAIL] 测试完成，{len(errors)} 个模块失败:")
    for e in errors:
        print(f"  - {e}")
else:
    print("[PASS] 全部模块测试通过!")
print("=" * 60)
