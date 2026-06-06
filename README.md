# 电气设计计算工具

基于 **GB 50217-2018** / **GB 50054-2011** 的电气工程设计计算工具。

## 功能

| 功能 | 标准依据 | 说明 |
|------|----------|------|
| ① 电流计算 | GB 50054 | 三相/单相，需用系数、同时系数 |
| ② 电缆自动选型 | GB 50217 附录C | 铜/铝芯，PVC/XLPE，4种敷设方式 |
| ③ 压降校验 | GB 50054 §6.4 | 照明3%、动力5%、混合4%、应急10% |
| ④ 短路热稳定 | GB 50054 §6.2.3 | S_min = I × √t / K |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动交互式 CLI
python main.py

# 3. 运行测试
python run_tests.py
```

## 项目结构

```
电气计算工具/
├── main.py                   # CLI 交互入口
├── run_tests.py              # 测试运行脚本
├── utils.py                  # 公共工具
├── requirements.txt
│
├── core/                     # 核心计算
│   ├── current_calc.py       # 电流计算
│   ├── cable_select.py       # 电缆选型
│   ├── voltage_drop.py       # 压降计算
│   └── short_circuit.py      # 短路热稳定校验
│
├── data/                     # 标准数据库
│   ├── ampacity.py           # 载流量表 (GB 50217)
│   ├── impedance.py          # 单位阻抗参数
│   ├── correction_factors.py # 温度/敷设/并列修正
│   └── k_values.py           # 热稳定 K 值
│
├── output/                   # 输出模块
│   ├── terminal.py           # rich 终端彩色输出
│   ├── excel_export.py       # Excel 计算书
│   └── pdf_export.py         # PDF 计算书
│
└── tests/                    # pytest 测试
    ├── test_current.py
    ├── test_cable.py
    ├── test_voltage_drop.py
    └── test_short_circuit.py
```

## 典型使用

```
python main.py → 选 5 (一键综合计算)

输入:
  设备功率: 150 kW  |  需用系数: 0.85
  电压: 380V  |  功率因数: 0.88
  导体: 铜芯 XLPE  |  敷设: 桥架
  环境温度: 38°C  |  长度: 120m
  短路电流: 25kA  |  持续时间: 0.2s

输出:
  ① I_js = 220.3 A
  ② 推荐截面: 120mm² (XLPE 桥架)
  ③ ΔU% = 2.87% ≤ 5% 合格
  ④ S_min = 78.2mm², 120 ≥ 78.2 合格
  最终选型: ZR-YJV-0.6/1kV 3×120+1×70
```

## 设计规范

- **GB 50217-2018** 电力工程电缆设计标准
- **GB 50054-2011** 低压配电设计规范

## License

MIT
