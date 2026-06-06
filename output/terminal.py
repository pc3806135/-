"""
终端输出模块 (基于 rich)

提供彩色表格和格式化输出。
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from core.current_calc import CurrentResult
from core.cable_select import CableSelectionResult
from core.voltage_drop import VoltageDropResult
from core.short_circuit import ShortCircuitResult
from utils import format_current, format_percent

console = Console()


# ============================================================
# 颜色常量
# ============================================================
COLOR_PASS = "green"
COLOR_FAIL = "red"
COLOR_TITLE = "bold cyan"
COLOR_VALUE = "bold yellow"
COLOR_LABEL = "dim"


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║       电气设计计算工具 v1.0  (GB 50217 / GB 50054)        ║
║       电流计算 · 电缆选型 · 压降校验 · 短路热稳定          ║
╚══════════════════════════════════════════════════════════╝
"""
    console.print(banner, style=COLOR_TITLE)


def print_current_result(result: CurrentResult):
    """打印电流计算结果"""
    table = Table(title=f"\n[1] 电流计算结果 - {result.load_name}", box=box.ROUNDED)
    table.add_column("参数", style=COLOR_LABEL, width=20)
    table.add_column("数值", style=COLOR_VALUE, width=25)
    table.add_column("说明", style="dim", width=25)

    phase_str = "三相" if result.is_three_phase else "单相"
    table.add_row("相别", phase_str, "")
    table.add_row("线电压", f"{result.voltage:.0f} V", "")
    table.add_row("功率因数", f"{result.cos_phi:.2f}", "")
    table.add_row("有功功率 P_js", f"{result.p_js:.2f} kW", "计算有功")
    table.add_row("无功功率 Q_js", f"{result.q_js:.2f} kvar", "计算无功")
    table.add_row("视在功率 S_js", f"{result.s_js:.2f} kVA", "计算视在")
    table.add_row("", "", "")
    table.add_row("> 计算电流 I_js",
                  f"[bold bright_white]{result.i_js:.2f} A[/]",
                  "GB 50054 公式")

    console.print(table)


def print_total_current_result(total: CurrentResult, individuals: list):
    """打印总负荷计算结果"""
    # 逐个负荷表
    ind_table = Table(title="\n[*] 各负荷计算电流", box=box.ROUNDED)
    ind_table.add_column("负荷名称", style="cyan")
    ind_table.add_column("P_e (kW)", justify="right")
    ind_table.add_column("Kx", justify="right")
    ind_table.add_column("cosφ", justify="right")
    ind_table.add_column("P_js (kW)", justify="right")
    ind_table.add_column("Q_js (kvar)", justify="right")
    ind_table.add_column("I_js (A)", justify="right", style="bold yellow")

    for r in individuals:
        ind_table.add_row(
            r.load_name, f"{r.p_js / 1.0:.1f}", "1.0",
            f"{r.cos_phi:.2f}", f"{r.p_js:.2f}",
            f"{r.q_js:.2f}", f"{r.i_js:.2f}",
        )

    console.print(ind_table)

    # 汇总
    print_current_result(total)


def print_cable_result(result: CableSelectionResult):
    """打印电缆选型结果"""
    inp = result.input
    table = Table(title=f"\n[2] 电缆选型结果", box=box.ROUNDED)
    table.add_column("项目", style=COLOR_LABEL, width=22)
    table.add_column("内容", style=COLOR_VALUE, width=40)

    table.add_row("导体材料", inp.conductor_cn)
    table.add_row("绝缘类型", inp.insulation_cn)
    table.add_row("敷设方式", inp.method_cn)
    table.add_row("电压等级", inp.voltage_level)
    table.add_row("环境温度", f"{inp.ambient_temp:.0f} °C")
    table.add_row("并列回路数", f"{inp.num_circuits} 回")
    table.add_row("", "")
    table.add_row("计算电流 I_js", f"{inp.i_js:.2f} A")

    # 修正系数
    k = result.correction_factors
    table.add_row("", "")
    table.add_row("温度修正 Kθ", f"{k.get('k_temp', 0):.2f}")
    table.add_row("敷设修正 K1", f"{k.get('k_method', 0):.2f}")
    table.add_row("并列修正 K2", f"{k.get('k_group', 0):.2f}")
    table.add_row("综合修正系数 K", f"[bold]{k.get('total', 0):.3f}[/]")
    table.add_row("要求载流量", f"{inp.i_js / k.get('total', 1):.1f} A (≥ I_js/K)")

    # 选型结果
    table.add_row("", "")
    if result.is_valid:
        table.add_row("> 推荐截面",
                      f"[bold bright_green]{result.selected_section} mm²[/]")
        table.add_row("  基准载流量", f"{result.raw_ampacity:.0f} A")
        table.add_row("  修正后载流量",
                      f"{result.corrected_ampacity:.0f} A "
                      f"({'✓' if result.corrected_ampacity >= inp.i_js else '✗'})")
    else:
        table.add_row("> 选型结果", f"[bold red]失败[/]")
        table.add_row("  原因", result.fail_reason)

    console.print(table)


def print_voltage_drop_result(result: VoltageDropResult):
    """打印压降计算结果"""
    inp = result.input
    status = "✓ 合格" if result.is_pass else "✗ 不合格"
    color = COLOR_PASS if result.is_pass else COLOR_FAIL

    table = Table(title=f"\n[3] 压降计算结果", box=box.ROUNDED)
    table.add_column("项目", style=COLOR_LABEL, width=20)
    table.add_column("内容", style=COLOR_VALUE, width=40)

    table.add_row("回路类型", inp.circuit_type)
    table.add_row("电缆长度", f"{inp.length_m:.0f} m")
    table.add_row("电缆截面", f"{inp.section} mm²")
    table.add_row("线电压", f"{inp.voltage:.0f} V")
    table.add_row("功率因数", f"{inp.cos_phi:.2f}")
    table.add_row("", "")
    table.add_row("单位电阻 R₀", f"{result.r0:.4f} Ω/km")
    table.add_row("单位电抗 X₀", f"{result.x0:.4f} Ω/km")
    table.add_row("", "")
    table.add_row("压降 ΔU", f"{result.delta_u_v:.2f} V")
    table.add_row("> 压降百分比 ΔU%",
                  f"[bold {color}]{result.delta_u_percent:.2f}%[/]")
    table.add_row("允许限值", f"{result.limit:.1f}%")
    table.add_row("判定", f"[bold {color}]{status}[/]")
    table.add_row("裕量", f"{result.margin:.2f}%")

    console.print(table)


def print_short_circuit_result(result: ShortCircuitResult):
    """打印短路热稳定校验结果"""
    inp = result.input
    status = "✓ 合格" if result.is_pass else "✗ 不合格"
    color = COLOR_PASS if result.is_pass else COLOR_FAIL

    table = Table(title=f"\n[4] 短路热稳定校验结果", box=box.ROUNDED)
    table.add_column("项目", style=COLOR_LABEL, width=24)
    table.add_column("内容", style=COLOR_VALUE, width=40)

    table.add_row("短路电流 I\"k3", f"{inp.ik_a:.0f} A ({inp.ik_a/1000:.2f} kA)")
    table.add_row("持续时间 t", f"{inp.t_s:.2f} s")
    table.add_row("热稳定系数 K", f"{result.k:.0f}")
    table.add_row("", "")
    table.add_row("> 最小截面 S_min",
                  f"[bold {color}]{result.s_min:.1f} mm²[/]")
    table.add_row("已选截面", f"{inp.selected_section} mm²")
    table.add_row("判定", f"[bold {color}]{status}[/]")

    if not result.is_pass:
        table.add_row("需升级到", f"[bold red]{result.required_section} mm²[/]")

    console.print(table)


def print_comprehensive_report(current_result: CurrentResult,
                                cable_result: CableSelectionResult,
                                vd_result: VoltageDropResult,
                                sc_result: ShortCircuitResult):
    """打印综合计算报告"""
    console.rule("[bold cyan] 综合计算报告")

    print_current_result(current_result)
    print_cable_result(cable_result)
    print_voltage_drop_result(vd_result)
    print_short_circuit_result(sc_result)

    # 最终结论
    all_pass = (cable_result.is_valid and vd_result.is_pass and sc_result.is_pass)
    conclusion_color = COLOR_PASS if all_pass else COLOR_FAIL
    conclusion_text = "✅ 全部校验通过" if all_pass else "❌ 存在不合格项，请调整参数"

    console.rule(f"[bold {conclusion_color}] {conclusion_text}")

    if not all_pass:
        issues = []
        if not cable_result.is_valid:
            issues.append(f"  • 电缆选型: {cable_result.fail_reason}")
        if not vd_result.is_pass:
            issues.append(f"  • 压降超限: {vd_result.delta_u_percent:.2f}% > {vd_result.limit:.1f}%")
        if not sc_result.is_pass:
            issues.append(f"  • 短路热稳定不足: 需 ≥ {sc_result.required_section} mm²")

        for issue in issues:
            console.print(issue, style=COLOR_FAIL)


def print_help():
    """打印帮助信息"""
    help_text = """
[bold cyan]常用命令[/]

[bold]电流计算:[/]
  输入设备功率、需用系数、功率因数、电压和相数，得到计算电流。

[bold]电缆选型:[/]
  输入计算电流、导体材料、绝缘类型、敷设条件和环境温度，自动匹配标准截面。

[bold]压降计算:[/]
  输入电流、电缆长度和截面，校验压降是否满足 GB 50054 限值。

[bold]短路热稳定:[/]
  输入短路电流和持续时间，按 GB 50054 §6.2.3 校验最小截面。

[bold]综合计算:[/]
  一次性完成 电流 → 选型 → 压降 → 短路 全流程。

[bold]GB 标准依据:[/]
  • GB 50217-2018 电力工程电缆设计标准
  • GB 50054-2011 低压配电设计规范
"""
    console.print(Panel(help_text, title="帮助"))
