# 电气设计计算工具

基于 **GB 50217-2018** / **GB 50054-2011** / **工业与民用配电设计手册(第四版)** 的电气工程设计计算工具。

📱 **PWA 在线版:** https://pc3806135.github.io/-/

---

## 功能

### 低压 0.6/1kV 综合计算

| 步骤 | 功能 | 标准依据 |
|------|------|----------|
| ① 电流计算 | 三相/单相，需用系数 Kx | GB 50054 |
| ② 电缆选型 | 11种常见型号 / 单芯·三芯·3+2·4+1 / 铜铝·XLPE·PVC / 4种敷设 / 品字形·一字形排列 | GB 50217 附录C |
| ③ 压降校验 | 动力5% / 照明3% / 混合4% / 应急10% | GB 50054 §6.4 |
| ④ 多根并联 | 大电流自动匹配 1~6 根电缆并联，计入并联降容系数 | 配电手册 |

### 高压 10/24/35kV 综合计算

| 步骤 | 功能 | 标准依据 |
|------|------|----------|
| ① 电流计算 | 10kV / 24kV / 35kV | GB 50054 |
| ② 电缆选型 | 铜铝 / XLPE / 明敷·直埋·排管 | GB 50217 |
| ③ 压降校验 | 限值 5% | GB 50054 |
| ④ 热稳定校验 | S_min = I × √t / K | GB 50054 §6.2.3 |
| ⑤ 动稳定校验 | i_p = √2 × K_p × I"k | 配电手册 |

### 输出

| 格式 | 说明 |
|------|------|
| 终端彩色输出 | rich 表格 (Python CLI) |
| Word 计算书 | 完整计算过程 + 修正系数 + 签名栏 (PWA 导出) |
| Excel 计算书 | openpyxl 生成 (Python CLI) |
| PDF 计算书 | reportlab 生成 (Python CLI) |

---

## PWA 网页版（推荐）

**在线地址:** https://pc3806135.github.io/-/

- 手机浏览器打开即用，无需安装
- 添加到桌面 → 像原生 APP 一样运行
- 完全离线可用（Service Worker 缓存）
- 一键导出 Word 计算书

```
docs/
├── index.html       # PWA 主体 (单文件)
├── sw.js            # Service Worker
├── manifest.json    # PWA 配置
├── server.py        # 本地服务器
├── icon-192.png
└── icon-512.png
```

---

## Python CLI 版

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python main.py

# 运行测试
python run_tests.py
```

```
电气计算工具/
├── main.py                   # CLI 交互入口
├── run_tests.py              # 测试运行脚本
├── utils.py
├── requirements.txt
├── core/                     # 核心计算
│   ├── current_calc.py       # 电流计算
│   ├── cable_select.py       # 电缆选型
│   ├── voltage_drop.py       # 压降计算
│   └── short_circuit.py      # 短路热稳定校验
├── data/                     # GB标准数据库
│   ├── ampacity.py           # 载流量表
│   ├── impedance.py          # 单位阻抗参数
│   ├── correction_factors.py # 温度/敷设/并列修正
│   └── k_values.py           # 热稳定 K 值
├── output/                   # 输出模块
│   ├── terminal.py           # 终端彩色输出
│   ├── excel_export.py       # Excel 计算书
│   └── pdf_export.py         # PDF 计算书
├── tests/                    # pytest 测试
└── docs/                     # PWA 网页版
```

---

## 电缆型号

| 型号 | 导体 | 绝缘 | 特点 |
|------|------|------|------|
| YJV | 铜 | XLPE | 最常用 |
| YJLV | 铝 | XLPE | 铝芯经济型 |
| ZR-YJV | 铜 | XLPE | 阻燃 |
| NH-YJV | 铜 | XLPE | 耐火 |
| WDZ-YJY | 铜 | XLPE | 低烟无卤 |
| YJV22 / YJLV22 | 铜/铝 | XLPE | 钢带铠装 |
| VV / VLV | 铜/铝 | PVC | 传统型 |
| VV22 / VLV22 | 铜/铝 | PVC | 铠装 |

---

## 设计规范

- **GB 50217-2018** 电力工程电缆设计标准
- **GB 50054-2011** 低压配电设计规范
- **工业与民用配电设计手册 (第四版)**

---

## License

MIT — design by pc
