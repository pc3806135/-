"""
电气设计计算工具  —  主入口

基于 GB 50217-2018 / GB 50054-2011

功能:
  1. 电流计算
  2. 电缆选型
  3. 压降计算
  4. 短路热稳定校验
  5. 综合计算 (①→②→③→④)
  6. 导出计算书 (Excel/PDF)
"""

import os
import sys
import math
from datetime import datetime

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm
from rich.text import Text

# 核心计算模块
from core.current_calc import (LoadInfo, calc_current, calc_total_current,
                                CurrentResult)
from core.cable_select import (CableSelectionInput, select_cable,
                                get_all_feasible_sections, CableSelectionResult)
from core.voltage_drop import (VoltageDropInput, calc_voltage_drop_3ph,
                                calc_voltage_drop_1ph, VoltageDropResult,
                                ALLOWABLE_VD_LIMITS)
from core.short_circuit import (ShortCircuitInput, check_short_circuit,
                                ShortCircuitResult)

# 输出模块
from output.terminal import (print_banner, print_current_result,
                              print_cable_result, print_voltage_drop_result,
                              print_short_circuit_result,
                              print_comprehensive_report, print_help,
                              print_total_current_result)
from output.excel_export import export_excel, export_excel_simple
from output.pdf_export import export_pdf

console = Console()

# 全局状态: 存储上次计算结果，方便各步骤间传递数据
_session = {
    "last_current": None,      # CurrentResult
    "last_cable": None,        # CableSelectionResult
    "last_vd": None,           # VoltageDropResult
    "last_sc": None,           # ShortCircuitResult
}


def main():
    """主入口"""
    print_banner()

    while True:
        _show_menu()
        try:
            choice = Prompt.ask("请选择", choices=["1", "2", "3", "4", "5", "6", "7", "0"])
        except KeyboardInterrupt:
            console.print("\n\n再见！", style="bold yellow")
            break

        if choice == "1":
            menu_current_calc()
        elif choice == "2":
            menu_cable_select()
        elif choice == "3":
            menu_voltage_drop()
        elif choice == "4":
            menu_short_circuit()
        elif choice == "5":
            menu_comprehensive()
        elif choice == "6":
            menu_export()
        elif choice == "7":
            print_help()
        elif choice == "0":
            console.print("\n再见！", style="bold yellow")
            break


def _show_menu():
    """显示主菜单"""
    console.print()
    console.rule("[bold cyan] 主菜单")
    console.print("[1] 电流计算")
    console.print("[2] 电缆选型")
    console.print("[3] 压降计算")
    console.print("[4] 短路热稳定校验")
    console.print("[5] 一键综合计算 (①→②→③→④)")
    console.print("[6] 导出计算书 (Excel/PDF)")
    console.print("[7] 帮助")
    console.print("[0] 退出")
    console.print()


# ============================================================
# 菜单①: 电流计算
# ============================================================
def menu_current_calc():
    console.rule("[bold cyan] ① 电流计算")
    console.print("[1] 单个负荷计算")
    console.print("[2] 多负荷汇总计算")
    console.print()

    sub = Prompt.ask("选择", choices=["1", "2"], default="1")

    if sub == "1":
        _single_load_calc()
    else:
        _multi_load_calc()


def _single_load_calc():
    """单个负荷电流计算"""
    console.print("\n--- 单负荷电流计算 ---\n")

    pe_kw = FloatPrompt.ask("设备功率 P_e (kW)", default=100.0)
    kx = FloatPrompt.ask("需用系数 Kx (0~1)", default=0.85)
    cos_phi = FloatPrompt.ask("功率因数 cosφ", default=0.85)
    voltage = FloatPrompt.ask("线电压 (V)", default=380.0)
    phase = Prompt.ask("相数", choices=["3", "1"], default="3")

    load = LoadInfo(
        name="负荷-1",
        pe_kw=pe_kw,
        kx=kx,
        cos_phi=cos_phi,
        is_three_phase=(phase == "3"),
    )

    result = calc_current(load, voltage)
    _session["last_current"] = result
    print_current_result(result)

    console.print("\n[dim]提示: 此电流结果已保存，可直接进入 [2] 电缆选型[/]")


def _multi_load_calc():
    """多负荷汇总计算"""
    console.print("\n--- 多负荷汇总电流计算 ---\n")

    num = IntPrompt.ask("负荷数量", default=3)
    loads = []

    for i in range(1, num + 1):
        console.print(f"\n[bold]负荷 {i}:[/]")
        name = Prompt.ask("  负荷名称", default=f"负荷-{i}")
        pe_kw = FloatPrompt.ask("  设备功率 P_e (kW)", default=50.0)
        kx = FloatPrompt.ask("  需用系数 Kx", default=0.8)
        cos_phi = FloatPrompt.ask("  功率因数 cosφ", default=0.85)
        phase = Prompt.ask("  相数 (3/1)", choices=["3", "1"], default="3")
        loads.append(LoadInfo(name, pe_kw, kx, cos_phi, phase == "3"))

    voltage = FloatPrompt.ask("\n线电压 (V)", default=380.0)
    ks = FloatPrompt.ask("同时系数 Ks (0~1)", default=0.9)

    total, individuals = calc_total_current(loads, voltage, ks)

    # 将各负荷的 LoadInfo 折算为 CurrentResult 用于打印
    ind_results = [calc_current(ld, voltage) for ld in loads]
    print_total_current_result(total, ind_results)
    _session["last_current"] = total

    console.print("\n[dim]提示: 总计算电流已保存，可直接进入 [2] 电缆选型[/]")


# ============================================================
# 菜单②: 电缆选型
# ============================================================
def menu_cable_select():
    console.rule("[bold cyan] ② 电缆选型")

    # 尝试使用上次计算结果
    i_js = None
    if _session["last_current"]:
        cr = _session["last_current"]
        console.print(f"\n[dim]上次计算电流: {cr.i_js:.2f} A ({cr.load_name})[/]")
        if Confirm.ask("使用上次的电流值?", default=True):
            i_js = cr.i_js

    if i_js is None:
        i_js = FloatPrompt.ask("计算电流 I_js (A)", default=180.0)

    console.print()
    conductor = Prompt.ask("导体材料", choices=["铜芯", "铝芯"], default="铜芯")
    insulation = Prompt.ask("绝缘类型", choices=["XLPE", "PVC"], default="XLPE")
    method = Prompt.ask(
        "敷设方式",
        choices=["桥架敷设", "空气中明敷", "穿管敷设", "直埋敷设"],
        default="桥架敷设"
    )

    # 电压等级自动推断
    if _session["last_current"]:
        v = _session["last_current"].voltage
        voltage_level = "0.6/1kV" if v <= 1000 else ("6/10kV" if v <= 10000 else "35kV")
    else:
        vl_choice = Prompt.ask("电压等级", choices=["0.6/1kV", "6/10kV"], default="0.6/1kV")
        voltage_level = vl_choice

    ambient_temp = FloatPrompt.ask("环境温度 (°C)", default=35.0)
    num_circuits = IntPrompt.ask("并列回路数", default=1)

    # 转换中文到英文
    params = CableSelectionInput(
        i_js=i_js,
        conductor="copper" if conductor == "铜芯" else "aluminum",
        insulation="xlpe" if insulation == "XLPE" else "pvc",
        method={"桥架敷设": "bridge", "空气中明敷": "air",
                "穿管敷设": "conduit", "直埋敷设": "buried"}[method],
        voltage_level=voltage_level,
        ambient_temp=ambient_temp,
        num_circuits=num_circuits,
    )

    result = select_cable(params)
    _session["last_cable"] = result

    print_cable_result(result)

    # 显示其他可选截面
    if result.is_valid:
        all_feasible = get_all_feasible_sections(params)
        if len(all_feasible) > 1:
            console.print("\n[dim]其他可选截面:[/]")
            for s, amp in all_feasible:
                marker = " ← 推荐" if s == result.selected_section else ""
                console.print(f"  • {s} mm² (修正载流量 {amp:.0f} A){marker}")

    console.print("\n[dim]提示: 选型结果已保存，可直接进入 [3] 压降计算[/]")


# ============================================================
# 菜单③: 压降计算
# ============================================================
def menu_voltage_drop():
    console.rule("[bold cyan] ③ 压降计算")

    # 尝试从上次选型拿到截面
    i_js = None
    section = 0
    voltage = 380.0
    cos_phi = 0.85

    if _session["last_current"]:
        cr = _session["last_current"]
        i_js = cr.i_js
        voltage = cr.voltage
        cos_phi = cr.cos_phi
        console.print(f"\n[dim]上次计算电流: {cr.i_js:.2f} A[/]")

    if _session["last_cable"] and _session["last_cable"].is_valid:
        s = _session["last_cable"].selected_section
        console.print(f"[dim]上次选型截面: {s} mm²[/]")
        if Confirm.ask("使用上次的截面?", default=True):
            section = s

    if i_js is None:
        i_js = FloatPrompt.ask("计算电流 I_js (A)", default=180.0)

    length = FloatPrompt.ask("电缆长度 (m)", default=100.0)

    if section == 0:
        section = FloatPrompt.ask("电缆截面 (mm²)", default=70.0)

    conductor = "copper"
    insulation = "xlpe"
    if _session["last_cable"]:
        conductor = _session["last_cable"].input.conductor
        insulation = _session["last_cable"].input.insulation
    voltage_level = "0.6/1kV" if voltage <= 1000 else "6/10kV"

    console.print()
    ct = Prompt.ask("回路类型", choices=["动力", "照明", "混合", "应急照明/安防"], default="动力")
    ct_map = {"动力": "power", "照明": "lighting", "混合": "mixed", "应急照明/安防": "emergency"}

    params = VoltageDropInput(
        i_js=i_js, length_m=length, conductor=conductor,
        voltage_level=voltage_level, voltage=voltage,
        cos_phi=cos_phi, section=section,
        circuit_type=ct_map[ct],
    )

    result = calc_voltage_drop_3ph(params)
    _session["last_vd"] = result

    print_voltage_drop_result(result)


# ============================================================
# 菜单④: 短路热稳定校验
# ============================================================
def menu_short_circuit():
    console.rule("[bold cyan] ④ 短路热稳定校验 (GB 50054 §6.2.3)")

    section = 0
    conductor = "copper"
    insulation = "xlpe"

    if _session["last_cable"]:
        r = _session["last_cable"]
        if r.is_valid:
            console.print(f"\n[dim]上次选型截面: {r.selected_section} mm²[/]")
            if Confirm.ask("使用上次的截面?", default=True):
                section = r.selected_section
                conductor = r.input.conductor
                insulation = r.input.insulation

    if section == 0:
        section = FloatPrompt.ask("电缆截面 (mm²)", default=120.0)

    ik = FloatPrompt.ask("三相短路电流有效值 I\"ₖ₃ (kA)", default=25.0)
    t = FloatPrompt.ask("短路持续时间 t (s)", default=0.2)

    # 转换为 A
    ik_a = ik * 1000

    params = ShortCircuitInput(
        ik_a=ik_a, t_s=t, conductor=conductor,
        insulation=insulation, selected_section=section,
        description="电缆短路热稳定校验",
    )

    result = check_short_circuit(params)
    _session["last_sc"] = result

    print_short_circuit_result(result)


# ============================================================
# 菜单⑤: 综合计算
# ============================================================
def menu_comprehensive():
    """一键完成 ①→②→③→④ 全流程"""
    console.rule("[bold cyan] ⑤ 综合计算 (一键完成全流程)")

    console.print("\n[bold]══════ 第一步: 输入负荷参数 ══════[/]\n")

    pe_kw = FloatPrompt.ask("设备功率 P_e (kW)", default=150.0)
    kx = FloatPrompt.ask("需用系数 Kx", default=0.85)
    cos_phi = FloatPrompt.ask("功率因数 cosφ", default=0.88)
    voltage = FloatPrompt.ask("线电压 (V)", default=380.0)

    console.print("\n[bold]══════ 第二步: 输入电缆参数 ══════[/]\n")

    conductor = Prompt.ask("导体材料", choices=["铜芯", "铝芯"], default="铜芯")
    insulation = Prompt.ask("绝缘类型", choices=["XLPE", "PVC"], default="XLPE")
    method = Prompt.ask(
        "敷设方式",
        choices=["桥架敷设", "空气中明敷", "穿管敷设", "直埋敷设"],
        default="桥架敷设"
    )
    voltage_level = "0.6/1kV" if voltage <= 1000 else "6/10kV"
    ambient_temp = FloatPrompt.ask("环境温度 (°C)", default=38.0)
    num_circuits = IntPrompt.ask("并列回路数", default=2)
    length = FloatPrompt.ask("电缆长度 (m)", default=120.0)

    ct = Prompt.ask("回路类型", choices=["动力", "照明", "混合", "应急照明/安防"], default="动力")
    ct_map = {"动力": "power", "照明": "lighting", "混合": "mixed", "应急照明/安防": "emergency"}

    console.print("\n[bold]══════ 第三步: 输入短路参数 ══════[/]\n")

    ik = FloatPrompt.ask("三相短路电流 I\"ₖ₃ (kA)", default=25.0)
    t = FloatPrompt.ask("短路持续时间 t (s)", default=0.2)

    # ─── 执行计算 ───
    conductor_key = "copper" if conductor == "铜芯" else "aluminum"
    insulation_key = "xlpe" if insulation == "XLPE" else "pvc"
    method_map = {"桥架敷设": "bridge", "空气中明敷": "air",
                  "穿管敷设": "conduit", "直埋敷设": "buried"}
    method_key = method_map[method]

    # ① 电流计算
    load = LoadInfo("综合负荷", pe_kw, kx, cos_phi)
    current_result = calc_current(load, voltage)

    # ② 电缆选型
    cable_input = CableSelectionInput(
        i_js=current_result.i_js, conductor=conductor_key,
        insulation=insulation_key, method=method_key,
        voltage_level=voltage_level, ambient_temp=ambient_temp,
        num_circuits=num_circuits,
    )
    cable_result = select_cable(cable_input)

    # ③ 压降计算
    if cable_result.is_valid:
        vd_input = VoltageDropInput(
            i_js=current_result.i_js, length_m=length,
            conductor=conductor_key, voltage_level=voltage_level,
            voltage=voltage, cos_phi=cos_phi,
            section=cable_result.selected_section,
            circuit_type=ct_map[ct],
        )
        vd_result = calc_voltage_drop_3ph(vd_input)
    else:
        vd_result = VoltageDropResult(
            VoltageDropInput(0, length, conductor_key, voltage_level,
                             voltage, cos_phi, 0, ct_map[ct]),
            0, 0, 0, 0,
        )

    # ④ 短路热稳定
    section_for_sc = cable_result.selected_section if cable_result.is_valid else 0
    sc_input = ShortCircuitInput(
        ik_a=ik * 1000, t_s=t, conductor=conductor_key,
        insulation=insulation_key, selected_section=section_for_sc,
    )
    sc_result = check_short_circuit(sc_input)

    # 保存会话
    _session["last_current"] = current_result
    _session["last_cable"] = cable_result
    _session["last_vd"] = vd_result
    _session["last_sc"] = sc_result

    # 输出综合报告
    print_comprehensive_report(current_result, cable_result, vd_result, sc_result)

    # 推荐电缆型号
    if cable_result.is_valid:
        _print_cable_model(cable_result, conductor_key, insulation_key, voltage_level)


def _print_cable_model(result: CableSelectionResult, conductor: str,
                       insulation: str, voltage_level: str):
    """打印推荐电缆型号"""
    sec = result.selected_section

    # 导体代号
    t = "T" if conductor == "copper" else "L"  # 铜不标

    # 绝缘代号
    ins = "YJ" if insulation == "xlpe" else "V"

    # 电压等级
    v = "0.6/1kV" if voltage_level == "0.6/1kV" else "6/10kV"

    console.print()
    console.rule("[bold green] 推荐电缆型号")

    # 三相+中性线
    if t == "T":
        model = f"ZR-YJV-{v} 3×{sec}+1×{max(sec/2, 10):.0f}"
    else:
        model = f"ZR-YJLV-{v} 3×{sec}+1×{max(sec/2, 16):.0f}"

    console.print(f"  [bold green]{model}[/]")
    console.print(f"  [dim]说明: ZR-阻燃型, {ins}绝缘, {v}电压等级[/]")


# ============================================================
# 菜单⑥: 导出计算书
# ============================================================
def menu_export():
    console.rule("[bold cyan] ⑥ 导出计算书")

    if not any([_session["last_current"], _session["last_cable"],
                _session["last_vd"], _session["last_sc"]]):
        console.print("\n[bold red]尚未进行任何计算，请先完成计算再导出。[/]")
        return

    console.print("\n[1] 导出 Excel 计算书 (.xlsx)")
    console.print("[2] 导出 PDF 计算书 (.pdf)")
    console.print("[3] 导出全部 (Excel + PDF)")
    fmt = Prompt.ask("选择", choices=["1", "2", "3"], default="1")

    try:
        cr = _session["last_current"]
        cr = cr or CurrentResult("N/A", 0, 0, 0, 0, 380, 0.85, True)

        cbl_default = CableSelectionInput(0, "copper", "xlpe", "bridge", "0.6/1kV", 35, 1)
        cbl = _session["last_cable"]
        cbl = cbl or CableSelectionResult(cbl_default, 0, 0, 0, {})

        vd_default = VoltageDropInput(0, 0, "copper", "0.6/1kV", 380, 0.85, 0, "power")
        vd = _session["last_vd"]
        vd = vd or VoltageDropResult(vd_default, 0, 0, 0, 0)

        sc_default = ShortCircuitInput(0, 0, "copper", "xlpe", 0)
        sc = _session["last_sc"]
        sc = sc or ShortCircuitResult(sc_default, 0, 0)

        files = []
        if fmt in ("1", "3"):
            filepath = export_excel(cr, cbl, vd, sc)
            files.append(filepath)
            console.print(f"  [green][OK] Excel 已保存: {filepath}[/]")

        if fmt in ("2", "3"):
            filepath = export_pdf(cr, cbl, vd, sc)
            files.append(filepath)
            console.print(f"  [green][OK] PDF 已保存: {filepath}[/]")

        console.print(f"\n[bold green]共导出 {len(files)} 个文件[/]")

    except ImportError as e:
        console.print(f"\n[bold red]缺少依赖库: {e}[/]")
        console.print("请运行: [dim]pip install openpyxl reportlab[/]")


if __name__ == "__main__":
    main()
