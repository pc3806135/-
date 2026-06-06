"""
GB 50217 载流量数据库

数据来源: GB 50217-2018《电力工程电缆设计标准》
- 附录B: 空气中敷设载流量
- 附录C: 直埋敷设载流量
- 附录D: 穿管敷设载流量参考值

结构:
  CABLE_DATA[conductor][insulation][method][voltage_level] = {
      section: ampacity,
      ...
  }

conductor: "copper" | "aluminum"
insulation: "pvc" | "xlpe"
method: "air" | "conduit" | "bridge" | "buried"
voltage_level: "0.6/1kV" | "6/10kV" | "35kV"
"""

# 标准截面系列 (mm²)
STANDARD_SECTIONS = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150,
                     185, 240, 300, 400, 500, 630]

# ============================================================
# 铜芯 PVC 绝缘电缆载流量 (空气中 30°C / 直埋 20°C)
# ============================================================
COPPER_PVC_AIR_1KV = {
    # section: ampacity (A)
    1.5: 18, 2.5: 25, 4: 32, 6: 42, 10: 59, 16: 79,
    25: 105, 35: 130, 50: 158, 70: 204, 95: 252,
    120: 292, 150: 337, 185: 386, 240: 456, 300: 527,
    400: 618, 500: 710, 630: 815,
}

COPPER_PVC_CONDUIT_1KV = {
    1.5: 15, 2.5: 20, 4: 27, 6: 35, 10: 48, 16: 65,
    25: 85, 35: 105, 50: 128, 70: 163, 95: 200,
    120: 230, 150: 265, 185: 304, 240: 360, 300: 410,
    400: 470, 500: 530, 630: 590,
}

COPPER_PVC_BURIED_1KV = {
    1.5: 22, 2.5: 30, 4: 39, 6: 49, 10: 67, 16: 88,
    25: 115, 35: 140, 50: 169, 70: 214, 95: 260,
    120: 298, 150: 338, 185: 385, 240: 452, 300: 515,
    400: 590, 500: 660, 630: 720,
}

# ============================================================
# 铜芯 XLPE 绝缘电缆载流量 (空气中 40°C / 直埋 25°C)
# ============================================================
COPPER_XLPE_AIR_1KV = {
    1.5: 22, 2.5: 30, 4: 40, 6: 51, 10: 71, 16: 96,
    25: 127, 35: 158, 50: 192, 70: 246, 95: 301,
    120: 346, 150: 399, 185: 456, 240: 538, 300: 621,
    400: 741, 500: 852, 630: 981,
}

COPPER_XLPE_CONDUIT_1KV = {
    1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 56, 16: 76,
    25: 100, 35: 123, 50: 150, 70: 188, 95: 230,
    120: 265, 150: 305, 185: 350, 240: 415, 300: 475,
    400: 550, 500: 630, 630: 720,
}

COPPER_XLPE_BURIED_1KV = {
    1.5: 26, 2.5: 35, 4: 46, 6: 58, 10: 79, 16: 103,
    25: 134, 35: 162, 50: 194, 70: 243, 95: 293,
    120: 335, 150: 379, 185: 430, 240: 502, 300: 572,
    400: 667, 500: 760, 630: 860,
}

COPPER_XLPE_BRIDGE_1KV = {
    # 桥架敷设 (梯架, 多根并列), 载流量略低于空气中明敷
    1.5: 21, 2.5: 28, 4: 37, 6: 47, 10: 66, 16: 89,
    25: 118, 35: 147, 50: 178, 70: 228, 95: 279,
    120: 320, 150: 370, 185: 423, 240: 500, 300: 577,
    400: 688, 500: 790, 630: 910,
}

# ============================================================
# 6/10kV 中压电缆 (铜芯 XLPE)
# ============================================================
COPPER_XLPE_AIR_10KV = {
    25: 140, 35: 170, 50: 205, 70: 260, 95: 318,
    120: 367, 150: 418, 185: 478, 240: 563, 300: 646,
    400: 770, 500: 882, 630: 1012,
}

COPPER_XLPE_BURIED_10KV = {
    25: 137, 35: 165, 50: 197, 70: 246, 95: 296,
    120: 338, 150: 380, 185: 432, 240: 504, 300: 573,
    400: 667, 500: 755, 630: 850,
}

# ============================================================
# 铝芯载流量约为铜芯的 0.78 (按 GB 50217 表折算)
# ============================================================

def _derive_aluminum(copper_data: dict) -> dict:
    """根据铜芯数据推算铝芯载流量"""
    return {k: round(v * 0.78, 1) for k, v in copper_data.items()}


# ============================================================
# 完整数据库结构
# ============================================================
CABLE_DATA = {
    "copper": {
        "pvc": {
            "air": {"0.6/1kV": COPPER_PVC_AIR_1KV},
            "conduit": {"0.6/1kV": COPPER_PVC_CONDUIT_1KV},
            "bridge": {"0.6/1kV": _derive_aluminum(COPPER_PVC_AIR_1KV)},  # 略低于空气
            "buried": {"0.6/1kV": COPPER_PVC_BURIED_1KV},
        },
        "xlpe": {
            "air": {"0.6/1kV": COPPER_XLPE_AIR_1KV,
                     "6/10kV": COPPER_XLPE_AIR_10KV},
            "conduit": {"0.6/1kV": COPPER_XLPE_CONDUIT_1KV},
            "bridge": {"0.6/1kV": COPPER_XLPE_BRIDGE_1KV},
            "buried": {"0.6/1kV": COPPER_XLPE_BURIED_1KV,
                       "6/10kV": COPPER_XLPE_BURIED_10KV},
        },
    },
    "aluminum": {
        "pvc": {
            "air": {"0.6/1kV": _derive_aluminum(COPPER_PVC_AIR_1KV)},
            "conduit": {"0.6/1kV": _derive_aluminum(COPPER_PVC_CONDUIT_1KV)},
            "bridge": {"0.6/1kV": _derive_aluminum(COPPER_PVC_AIR_1KV)},
            "buried": {"0.6/1kV": _derive_aluminum(COPPER_PVC_BURIED_1KV)},
        },
        "xlpe": {
            "air": {"0.6/1kV": _derive_aluminum(COPPER_XLPE_AIR_1KV),
                    "6/10kV": _derive_aluminum(COPPER_XLPE_AIR_10KV)},
            "conduit": {"0.6/1kV": _derive_aluminum(COPPER_XLPE_CONDUIT_1KV)},
            "bridge": {"0.6/1kV": _derive_aluminum(COPPER_XLPE_BRIDGE_1KV)},
            "buried": {"0.6/1kV": _derive_aluminum(COPPER_XLPE_BURIED_1KV),
                       "6/10kV": _derive_aluminum(COPPER_XLPE_BURIED_10KV)},
        },
    },
}


def get_cable_data(conductor: str, insulation: str, method: str,
                   voltage_level: str) -> dict:
    """
    获取指定条件下的载流量表。

    参数:
        conductor: "copper" | "aluminum"
        insulation: "pvc" | "xlpe"
        method: "air" | "conduit" | "bridge" | "buried"
        voltage_level: "0.6/1kV" | "6/10kV"

    返回:
        {section: ampacity} 字典
    """
    return CABLE_DATA[conductor][insulation][method][voltage_level]


def get_available_voltage_levels(conductor: str, insulation: str,
                                  method: str) -> list:
    """获取指定条件下可用的电压等级"""
    return list(CABLE_DATA[conductor][insulation][method].keys())
