"""
短路热稳定 K 值数据库

数据来源: GB 50054-2011《低压配电设计规范》
附录A: 热稳定系数 K 值

S_min = I_k × √t / K

S_min: 导体最小截面 (mm²)
I_k:   短路电流有效值 (A)
t:     短路持续时间 (s)
K:     热稳定系数
"""

# (导体, 绝缘) → K值
K_VALUES = {
    ("copper", "pvc"):   115,   # 铜芯 PVC 绝缘，初始温度 70°C, 最终温度 160°C
    ("copper", "xlpe"):  143,   # 铜芯 XLPE 绝缘，初始温度 90°C, 最终温度 250°C
    ("aluminum", "pvc"):  76,   # 铝芯 PVC 绝缘
    ("aluminum", "xlpe"): 95,   # 铝芯 XLPE 绝缘
}


def get_k_value(conductor: str, insulation: str) -> float:
    """
    获取短路热稳定系数 K。

    参数:
        conductor: "copper" | "aluminum"
        insulation: "pvc" | "xlpe"

    返回:
        K 值
    """
    key = (conductor, insulation)
    if key not in K_VALUES:
        raise ValueError(f"不支持的组合: conductor={conductor}, insulation={insulation}")
    return K_VALUES[key]


def calc_min_section(ik_a: float, t: float, conductor: str,
                     insulation: str) -> float:
    """
    计算短路热稳定要求的最小截面。

    参数:
        ik_a: 短路电流有效值 (A)
        t: 短路持续时间 (s)
        conductor: "copper" | "aluminum"
        insulation: "pvc" | "xlpe"

    返回:
        S_min (mm²)
    """
    k = get_k_value(conductor, insulation)
    return ik_a * (t ** 0.5) / k
