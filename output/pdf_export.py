"""
PDF 计算书导出模块

使用 reportlab 生成 PDF 计算书。
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (getSampleStyleSheet, ParagraphStyle)
from reportlab.lib.colors import (HexColor, black, white, green, red)
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, PageBreak)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core.current_calc import CurrentResult
from core.cable_select import CableSelectionResult
from core.voltage_drop import VoltageDropResult
from core.short_circuit import ShortCircuitResult


# ============================================================
# 字体注册
# ============================================================
def _register_fonts():
    """注册中文字体"""
    # 尝试多种可能的字体路径
    font_candidates = [
        ("SimHei", "C:/Windows/Fonts/simhei.ttf"),
        ("SimHei", "C:/Windows/Fonts/SimHei.ttf"),
        ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
        ("SimSun", "C:/Windows/Fonts/SimSun.ttc"),
        ("MicrosoftYaHei", "C:/Windows/Fonts/msyh.ttc"),
        ("MicrosoftYaHei", "C:/Windows/Fonts/msyhbd.ttc"),
    ]

    for name, path in font_candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                continue

    # 如果找不到中文字体，使用内置字体 (不支持中文)
    return None


_CN_FONT = _register_fonts()


def _get_styles():
    """获取样式"""
    styles = getSampleStyleSheet()

    font_name = _CN_FONT or "Helvetica"

    styles.add(ParagraphStyle(
        name="CN_Title", fontName=font_name, fontSize=18,
        leading=22, alignment=TA_CENTER, textColor=HexColor("#1F4E79"),
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CN_Heading", fontName=font_name, fontSize=13,
        leading=16, textColor=HexColor("#1F4E79"),
        spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="CN_Normal", fontName=font_name, fontSize=10,
        leading=14, textColor=HexColor("#333333"),
    ))
    styles.add(ParagraphStyle(
        name="CN_Pass", fontName=font_name, fontSize=11,
        leading=14, textColor=green,
    ))
    styles.add(ParagraphStyle(
        name="CN_Fail", fontName=font_name, fontSize=11,
        leading=14, textColor=red,
    ))

    return styles


def _build_table(headers: list, data: list, col_widths: list = None):
    """构建格式化的 PDF 表格"""
    styles = _get_styles()

    # 包装为 Paragraph
    header_row = [Paragraph(f"<b>{h}</b>", styles["CN_Normal"]) for h in headers]
    data_rows = [[Paragraph(str(c), styles["CN_Normal"]) for c in row]
                 for row in data]

    table_data = [header_row] + data_rows

    tbl = Table(table_data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E75B6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#999999")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#D6E4F0")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    return tbl


def export_pdf(current_result: CurrentResult,
               cable_result: CableSelectionResult,
               vd_result: VoltageDropResult,
               sc_result: ShortCircuitResult,
               filepath: str = None) -> str:
    """
    导出完整计算书到 PDF。

    参数:
        current_result: 电流计算结果
        cable_result:  电缆选型结果
        vd_result:      压降计算结果
        sc_result:      短路校验结果
        filepath:       保存路径

    返回:
        文件路径
    """
    if filepath is None:
        filepath = f"电气计算书_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    styles = _get_styles()
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    story = []

    # 标题
    story.append(Paragraph("电气设计计算书", styles["CN_Title"]))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(
        f"设计依据: GB 50217-2018 / GB 50054-2011 &nbsp;&nbsp;"
        f"计算日期: {datetime.now().strftime('%Y-%m-%d')}",
        styles["CN_Normal"]
    ))
    story.append(Spacer(1, 6*mm))

    # ========================================
    # ① 电流计算
    # ========================================
    story.append(Paragraph("① 电流计算", styles["CN_Heading"]))
    story.append(Spacer(1, 2*mm))

    phase_str = "三相" if current_result.is_three_phase else "单相"
    current_data = [
        ["相别", phase_str],
        ["线电压 U_n", f"{current_result.voltage:.0f} V"],
        ["功率因数 cosφ", f"{current_result.cos_phi:.2f}"],
        ["有功功率 P_js", f"{current_result.p_js:.2f} kW"],
        ["无功功率 Q_js", f"{current_result.q_js:.2f} kvar"],
        ["视在功率 S_js", f"{current_result.s_js:.2f} kVA"],
        ["计算电流 I_js", f"{current_result.i_js:.2f} A"],
    ]
    tbl = _build_table(["参数", "数值"], current_data, [60*mm, 80*mm])
    story.append(tbl)
    story.append(Spacer(1, 4*mm))

    # ========================================
    # ② 电缆选型
    # ========================================
    story.append(Paragraph("② 电缆选型 (GB 50217)", styles["CN_Heading"]))
    story.append(Spacer(1, 2*mm))

    inp = cable_result.input
    k = cable_result.correction_factors
    cable_data = [
        ["导体材料", inp.conductor_cn, ""],
        ["绝缘类型", inp.insulation_cn, ""],
        ["敷设方式", inp.method_cn, ""],
        ["电压等级", inp.voltage_level, ""],
        ["环境温度", f"{inp.ambient_temp:.0f} °C", ""],
        ["并列回路", f"{inp.num_circuits} 回", ""],
        ["计算电流 I_js", f"{inp.i_js:.2f} A", ""],
        ["温度修正 Kθ", f"{k.get('k_temp', 0):.3f}", ""],
        ["敷设修正 K₁", f"{k.get('k_method', 0):.3f}", ""],
        ["并列修正 K₂", f"{k.get('k_group', 0):.3f}", ""],
        ["综合修正 K", f"{k.get('total', 0):.3f}", ""],
    ]

    if cable_result.is_valid:
        cable_data.append(["➤ 推荐截面", f"{cable_result.selected_section} mm²", "✓"])
        cable_data.append(["修正后载流量", f"{cable_result.corrected_ampacity:.0f} A", ""])
    else:
        cable_data.append(["选型结果", "失败", "✗"])

    tbl = _build_table(["项目", "内容", "判定"], cable_data, [50*mm, 70*mm, 20*mm])
    story.append(tbl)
    story.append(Spacer(1, 4*mm))

    # ========================================
    # ③ 压降计算
    # ========================================
    story.append(Paragraph("③ 压降校验 (GB 50054 §6.4)", styles["CN_Heading"]))
    story.append(Spacer(1, 2*mm))

    vd_status = "✓ 合格" if vd_result.is_pass else "✗ 不合格"
    status_style = styles["CN_Pass"] if vd_result.is_pass else styles["CN_Fail"]

    vd_data = [
        ["回路类型", vd_result.input.circuit_type],
        ["电缆长度", f"{vd_result.input.length_m:.0f} m"],
        ["电缆截面", f"{vd_result.input.section} mm²"],
        ["压降 ΔU", f"{vd_result.delta_u_v:.2f} V"],
        ["压降百分比 ΔU%", f"{vd_result.delta_u_percent:.2f}%"],
        ["允许限值", f"{vd_result.limit:.1f}%"],
        ["判定", vd_status],
    ]
    tbl = _build_table(["项目", "内容"], vd_data, [60*mm, 80*mm])
    story.append(tbl)
    story.append(Spacer(1, 4*mm))

    # ========================================
    # ④ 短路热稳定
    # ========================================
    story.append(Paragraph("④ 短路热稳定校验 (GB 50054 §6.2.3)", styles["CN_Heading"]))
    story.append(Spacer(1, 2*mm))

    sc_status = "✓ 合格" if sc_result.is_pass else f"✗ 不合格"
    sc_data = [
        ["短路电流 I\"ₖ₃", f"{sc_result.input.ik_a:.0f} A"],
        ["持续时间 t", f"{sc_result.input.t_s:.2f} s"],
        ["热稳定系数 K", f"{sc_result.k:.0f}"],
        ["要求最小截面 S_min", f"{sc_result.s_min:.1f} mm²"],
        ["已选截面", f"{sc_result.input.selected_section} mm²"],
        ["判定", sc_status],
    ]
    if not sc_result.is_pass:
        sc_data.append(["需升级到", f"{sc_result.required_section} mm²"])

    tbl = _build_table(["项目", "内容"], sc_data, [60*mm, 80*mm])
    story.append(tbl)
    story.append(Spacer(1, 8*mm))

    # ========================================
    # 结论
    # ========================================
    all_pass = (cable_result.is_valid and vd_result.is_pass and sc_result.is_pass)
    conclusion = ("✅ 全部校验通过，电缆选型满足 GB 50217 / GB 50054 要求。"
                  if all_pass else
                  "❌ 存在不合格项，请调整参数后重新计算。")
    conclusion_style = styles["CN_Pass"] if all_pass else styles["CN_Fail"]

    story.append(Paragraph("最终结论", styles["CN_Heading"]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(conclusion, conclusion_style))

    # 构建
    doc.build(story)
    return filepath
