"""
修正系数数据库

数据来源: GB 50217-2018 附录D
"""

# ============================================================
# 环境温度修正系数 Kθ
# 基准温度: PVC=30°C, XLPE=40°C
# ============================================================

# PVC 绝缘, 基准温度 30°C
TEMP_CORRECTION_PVC_AIR = {
    # 环境温度(°C): 修正系数
    10: 1.22,
    15: 1.17,
    20: 1.12,
    25: 1.06,
    30: 1.00,
    35: 0.94,
    40: 0.87,
    45: 0.79,
    50: 0.71,
}

# XLPE 绝缘, 基准温度 40°C
TEMP_CORRECTION_XLPE_AIR = {
    10: 1.18,
    15: 1.14,
    20: 1.10,
    25: 1.05,
    30: 1.00,
    35: 0.95,
    40: 0.90,  # XLPE 在 40°C 空气中载流量打 9 折
    45: 0.85,
    50: 0.80,
    55: 0.74,
    60: 0.68,
}

# 直埋敷设, 基准地温 20°C (PVC) / 25°C (XLPE)
TEMP_CORRECTION_BURIED_PVC = {
    10: 1.10,
    15: 1.05,
    20: 1.00,
    25: 0.95,
    30: 0.89,
    35: 0.84,
    40: 0.77,
}

TEMP_CORRECTION_BURIED_XLPE = {
    10: 1.11,
    15: 1.07,
    20: 1.03,
    25: 0.99,
    30: 0.94,
    35: 0.90,
    40: 0.85,
}

# ============================================================
# 多回路并列敷设修正系数 K₂ (空气中)
# ============================================================
GROUPING_CORRECTION_AIR = {
    # 并列回路数: 修正系数
    1: 1.00,
    2: 0.87,
    3: 0.81,
    4: 0.75,
    5: 0.70,
    6: 0.66,
    8: 0.60,
    10: 0.55,
}

# 多回路并列敷设修正系数 K₂ (直埋)
GROUPING_CORRECTION_BURIED = {
    1: 1.00,
    2: 0.85,
    3: 0.75,
    4: 0.70,
    5: 0.65,
    6: 0.60,
}


def get_temp_correction(insulation: str, method: str, temp: float) -> float:
    """
    获取温度修正系数。

    参数:
        insulation: "pvc" | "xlpe"
        method: "air" | "conduit" | "bridge" | "buried"
        temp: 环境温度 (°C)

    返回:
        修正系数 Kθ
    """
    if method in ("air", "conduit", "bridge"):
        table = TEMP_CORRECTION_XLPE_AIR if insulation == "xlpe" else TEMP_CORRECTION_PVC_AIR
    else:
        table = TEMP_CORRECTION_BURIED_XLPE if insulation == "xlpe" else TEMP_CORRECTION_BURIED_PVC

    # 线性插值
    temps = sorted(table.keys())
    if temp <= temps[0]:
        return table[temps[0]]
    if temp >= temps[-1]:
        return table[temps[-1]]

    for i in range(len(temps) - 1):
        if temps[i] <= temp <= temps[i + 1]:
            t1, t2 = temps[i], temps[i + 1]
            k1, k2 = table[t1], table[t2]
            return k1 + (k2 - k1) * (temp - t1) / (t2 - t1)

    return 1.0


def get_grouping_correction(method: str, num_circuits: int) -> float:
    """
    获取多回路并列修正系数。

    参数:
        method: 敷设方式
        num_circuits: 并列回路数

    返回:
        修正系数 K₂
    """
    if method == "buried":
        table = GROUPING_CORRECTION_BURIED
    else:
        table = GROUPING_CORRECTION_AIR

    if num_circuits <= 1:
        return 1.0
    # 精确匹配
    if num_circuits in table:
        return table[num_circuits]
    # 查找最近值 (保守取较小值)
    keys = sorted(table.keys())
    if num_circuits >= keys[-1]:
        return table[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= num_circuits <= keys[i + 1]:
            # 取较小值 — 更保守 (修正系数更小 → 更安全)
            return table[keys[i]]
    return 1.0


def get_method_factor(method: str) -> float:
    """
    敷设方式基本修正系数 (相对空气中明敷)。

    空气中明敷: 1.0
    桥架: 0.93
    穿管: 0.80
    直埋: 1.05 (散热略好于空气)
    """
    factors = {
        "air": 1.0,
        "bridge": 0.93,
        "conduit": 0.80,
        "buried": 1.05,
    }
    return factors.get(method, 1.0)
