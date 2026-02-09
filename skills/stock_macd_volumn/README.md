

# A股上涨趋势分析工具

基于技术指标的量化分析工具，用于识别A股市场中具有明显上涨趋势特征的股票。

## 功能特点

- ✅ **核心特征识别**：MACD上涨趋势、成交量放大、低位启动（未破60日均线）
- ✅ **补充特征分析**：RSI、KDJ、布林带、价格形态、量价配合
- ✅ **三级评级系统**：A级推荐、B级关注、C级观察
- ✅ **风险控制**：自动排除连续涨停、短期暴涨、巨量滞涨等高风险股票
- ✅ **回测验证**：验证未来5日涨幅，计算策略胜率
- ✅ **灵活配置**：支持strict/standard/loose三种筛选模式
- ✅ **详细报告**：CSV详细列表 + JSON统计报告
- ✅ **每日自动更新**：定时任务自动追加当日交易数据到CSV文件

## 环境要求

- Python 3.7+
- 依赖库：pandas >= 2.0.0, numpy >= 1.24.0, baostock >= 0.8.8

## 安装依赖

```bash
cd /Users/ellen_li/2026projects/my-skills
source venv/bin/activate
pip install pandas numpy baostock
```

## 快速开始

### 1. 基础使用

```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn
python stock_trend_analyzer.py
```

### 2. 测试运行（分析前100只股票）

```bash
python stock_trend_analyzer.py --limit 100
```

### 3. 实盘模式（不验证未来涨幅）

```bash
python stock_trend_analyzer.py --no-future
```

### 4. 指定筛选模式

```bash
# 严格模式：4个特征全满足
python stock_trend_analyzer.py --mode strict

# 标准模式：至少3个特征满足（推荐）
python stock_trend_analyzer.py --mode standard

# 宽松模式：至少2个特征满足且MACD必须满足
python stock_trend_analyzer.py --mode loose
```

### 5. 自定义路径

```bash
python stock_trend_analyzer.py \
    --data-dir /path/to/stock/data \
    --output-dir /path/to/output
```

---

## 每日数据自动更新

### 功能说明

每日自动更新工具可以在每天**21:00**自动获取当日所有A股的交易数据，并追加到现有的CSV文件中，确保数据始终保持最新。

**特性：**
- ✅ 自动获取当日交易数据（基于Baostock）
- ✅ 智能追加，避免重复数据
- ✅ 跳过停牌或无交易的股票
- ✅ 详细日志记录
- ✅ 定时任务自动执行

---

### 快速设置定时任务

#### 方法1：一键设置（推荐）

```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn
./setup_daily_task.sh
```

脚本会自动：
1. 检查虚拟环境和依赖
2. 配置cron定时任务（每天21:00执行）
3. 创建日志目录
4. 验证配置

---

#### 方法2：手动配置

```bash
# 1. 编辑crontab
crontab -e

# 2. 添加以下行（根据实际路径调整）
0 21 * * * cd /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn && source ../../venv/bin/activate && python daily_data_updater.py >> logs/daily_update.log 2>&1

# 3. 保存并退出
```

---

### 手动运行更新

#### 测试运行（仅更新前10只股票）

```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn
source ../../venv/bin/activate
python daily_data_updater.py --test
```

#### 完整更新（所有股票）

```bash
python daily_data_updater.py
```

#### 指定日期更新

```bash
# 更新指定日期的数据
python daily_data_updater.py --date 2026-02-07
```

---

### 输出示例

```
============================================================
每日股票数据更新工具
============================================================
数据目录: /Users/ellen_li/2026projects/A股近10年日线数据
目标日期: 2026-02-09
运行时间: 2026-02-09 21:00:15
============================================================
正在登录Baostock...
Baostock登录成功
找到 5187 个股票文件
开始更新数据...
进度: 100/5187 | 成功: 95 | 已最新: 3 | 无交易: 2
进度: 200/5187 | 成功: 188 | 已最新: 7 | 无交易: 5
...
============================================================
更新完成!
总文件数: 5187
成功更新: 4980
已是最新: 15
当日无交易: 180
更新失败: 12
============================================================

✅ 数据更新成功完成!
```

---

### 日志查看

```bash
# 查看最新日志
tail -f logs/daily_update.log

# 查看最近100行
tail -n 100 logs/daily_update.log

# 查看今天的更新记录
grep "$(date +%Y-%m-%d)" logs/daily_update.log
```

---

### 管理定时任务

```bash
# 查看所有定时任务
crontab -l

# 查看当前的数据更新任务
crontab -l | grep daily_data_updater

# 编辑定时任务
crontab -e

# 删除定时任务
crontab -e  # 然后删除包含'daily_data_updater.py'的行
```

---

### 注意事项

1. **时间选择**：21:00设定是因为A股收盘时间是15:00，Baostock数据通常在18:00后更新完成
2. **周末和节假日**：工具会自动判断，如果当天是非交易日，会获取最近的交易日数据
3. **重复运行**：如果当日数据已存在，会跳过更新，避免重复
4. **网络问题**：如果更新失败，第二天会自动补充前一天的数据
5. **前复权数据**：默认使用前复权（adjustflag=3），与初始下载保持一致

---

### 数据完整性验证

更新后可以验证数据是否正常：

```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn
source ../../venv/bin/activate
python -c "
import pandas as pd
import glob

csv_files = glob.glob('/Users/ellen_li/2026projects/A股近10年日线数据/*.csv')
sample = csv_files[0]
df = pd.read_csv(sample)
print(f'样本股票: {sample}')
print(f'数据行数: {len(df)}')
print(f'最新日期: {df.iloc[-1][\"date\"]}')
print(f'最新收盘价: {df.iloc[-1][\"close\"]}')
"
```

---

### 故障排除

#### Q1: 定时任务没有执行？

检查步骤：
```bash
# 1. 确认cron服务运行
ps aux | grep cron

# 2. 检查crontab配置
crontab -l

# 3. 查看系统日志
tail -f /var/log/system.log | grep cron
```

#### Q2: 更新失败怎么办？

```bash
# 查看详细错误
tail -n 50 logs/daily_update.log

# 手动运行调试
python daily_data_updater.py --test
```

#### Q3: 如何暂停自动更新？

```bash
# 临时禁用（注释掉cron任务）
crontab -e
# 在任务行前添加 # 号

# 永久删除
crontab -e
# 删除包含 daily_data_updater.py 的行
```

---

## 核心特征说明

### 特征1：MACD上涨趋势（评分机制）

**评分标准**（满分100分，≥50分视为满足）：
- DIF > DEA（金叉状态）：+30分
- DIF > 0 且 DEA > 0（零轴上方）：+20分
- MACD柱状图 > 0：+15分
- DIF连续5天上升：+20分
- MACD柱连续3天递增：+15分

**最少数据需求**：34个交易日

---

### 特征2：成交量放大

**计算方法**：
```
近期日均量 = 最近3天平均成交量
历史日均量 = 前20天平均成交量（排除最近3天）
成交量比率 = 近期日均量 / 历史日均量
```

**判定标准**：成交量比率 ≥ 2.0倍（推荐阈值）

**分级标准**：
- 温和放量：1.5-2.0倍
- 明显放量：2.0-3.0倍
- 剧烈放量：≥3.0倍

**最少数据需求**：23个交易日

---

### 特征3：最高价未高于60日均线

**计算方法**：
```
MA60距离% = (当日最高价 - 60日均线) / 60日均线 × 100
```

**判定标准**：MA60距离% ≤ 0.5%（允许0.5%误差容忍）

**状态分类**：
- **临界突破**（-3% ≤ 距离 ≤ 0.5%）：最佳状态
- **深度蓄势**（距离 < -10%）：需结合其他指标
- **已突破**（距离 > 0.5%）：不符合条件

**备选方案**：数据不足60天时使用30日均线

**最少数据需求**：60个交易日（标准）或30个（备选）

---

### 特征4：未来5日涨幅验证（仅回测模式）

**计算方法**：
```
未来5日最高涨幅% = (未来5日最高价 - 当日收盘价) / 当日收盘价 × 100
```

**判定标准**：未来5日最高涨幅 ≥ 2.0%

**用途说明**：
- 这是**标签数据**，用于历史回测和验证策略有效性
- 实盘模式下不使用（未来数据不可知）
- 用于计算策略胜率和调整参数

---

## 补充特征说明

### 1. RSI相对强弱指标（14日周期）
- **黄金区间**：40 < RSI < 70
- **权重**：+10分

### 2. KDJ随机指标（9,3,3）
- **金叉信号**：K线上穿D线且J值 < 80
- **权重**：+15分

### 3. 布林带突破（20,2）
- **收窄待突破**：带宽 < 0.1
- **权重**：+10分

### 4. 价格形态识别
- **支持形态**：突破平台、V型反转、回调企稳
- **权重**：+15分

### 5. 量价配合检测
- **量价齐升**：价格上涨且成交量放大
- **权重**：+10分

---

## 筛选模式对比

| 模式 | 最少条件数 | 特殊要求 | 精准度 | 数量 | 适用场景 |
|------|-----------|---------|--------|------|---------|
| **strict** | 4个全满足 | - | 最高 | 最少 | 追求精准，可接受少量标的 |
| **standard** | 至少3个 | - | 平衡 | 适中 | 推荐使用，平衡精准度和数量 |
| **loose** | 至少2个 | MACD必须满足 | 较低 | 较多 | 需人工复核，适合挖掘潜力股 |

---

## 评级系统

根据**补充特征总分**（满分60分）进行评级：

| 评级 | 分数范围 | 说明 |
|------|---------|------|
| **A级** | ≥30分 | 强烈推荐，多项补充指标优秀 |
| **B级** | 20-29分 | 值得关注，部分补充指标良好 |
| **C级** | <20分 | 一般观察，补充指标较弱 |

---

## 风险控制

自动排除以下高风险股票：

1. **连续涨停 ≥ 3天**：追高风险
2. **短期暴涨 > 30%**：回调风险
3. **巨量滞涨**：成交额放大5倍但涨幅<3%
4. **远离均线 > 30%**：距离20日均线过远

---

## 输出结果

### 1. CSV详细列表（trend_signals_YYYYMMDD.csv）

包含所有检测到的信号，字段说明：

| 字段 | 说明 |
|------|------|
| 股票代码 | 如sh.600000 |
| 股票名称 | 如浦发银行 |
| 信号日期 | 满足条件的交易日期 |
| 收盘价 | 当日收盘价 |
| MACD评分 | MACD上涨趋势评分（0-100） |
| 成交量比率 | 近期/历史日均成交量比率 |
| MA60距离% | 最高价距离60日均线的百分比 |
| 评级 | A级/B级/C级 |
| 补充特征分 | 补充特征总分（0-60） |
| MACD满足 | True/False |
| 成交量满足 | True/False |
| MA60满足 | True/False |
| 未来5日涨幅% | 仅回测模式，未来5日最高涨幅 |
| 未来涨幅满足 | 仅回测模式，True/False |

### 2. JSON统计报告（analysis_report_YYYYMMDD.json）

包含以下统计信息：

```json
{
  "analysis_date": "2026-02-09 12:00:00",
  "mode": "backtest",
  "config": {
    "filter_mode": "standard",
    "volume_ratio_threshold": 2.0,
    "macd_score_threshold": 50,
    "min_future_return": 2.0
  },
  "summary": {
    "total_stocks": 127,
    "total_signals": 342,
    "avg_signals_per_stock": 2.69
  },
  "rating_distribution": {
    "A级": 42,
    "B级": 138,
    "C级": 162
  },
  "performance_stats": {
    "avg_future_return": 3.1,
    "median_future_return": 2.8,
    "win_rate": 62.5,
    "max_return": 15.3,
    "min_return": -2.1
  },
  "top_stocks": [...]
}
```

---

## 参数配置

所有参数在 [config.py](config.py) 中配置，主要参数：

### 核心参数

```python
# MACD参数
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MACD_SCORE_THRESHOLD = 50

# 成交量参数
VOLUME_RECENT_DAYS = 3
VOLUME_BASELINE_DAYS = 20
VOLUME_RATIO_THRESHOLD = 2.0

# 均线参数
MA_PERIOD = 60
MA_DISTANCE_THRESHOLD = 0.5

# 信号验证参数
FUTURE_DAYS = 5
MIN_FUTURE_RETURN = 2.0

# 筛选模式
FILTER_MODE = "standard"  # strict/standard/loose
```

### 数据路径配置

```python
DATA_DIR = "/Users/ellen_li/2026projects/A股近10年日线数据"
OUTPUT_DIR = "./output"
```

---

## 使用示例

### 场景1：回测历史数据，评估策略有效性

```bash
# 使用标准模式，分析全部股票，启用未来验证
python stock_trend_analyzer.py --mode standard

# 查看输出
# output/trend_signals_20260209.csv - 所有信号详情
# output/analysis_report_20260209.json - 统计报告（包含胜率）
```

**预期输出**：
```
============================================================
A股上涨趋势分析工具
============================================================
数据目录: /Users/ellen_li/2026projects/A股近10年日线数据
输出目录: ./output
筛选模式: standard - 标准模式：平衡精准度和数量（推荐）
回测模式: 开启
待分析股票数: 5187
============================================================
进度: 100/5187 | 有信号: 8 | 信号总数: 23
进度: 200/5187 | 有信号: 15 | 信号总数: 47
...
============================================================
分析完成!
总股票数: 5187
有信号股票: 127 (2.4%)
信号总数: 342
失败数: 0
============================================================
结果已保存:
  CSV: ./output/trend_signals_20260209.csv
  JSON: ./output/analysis_report_20260209.json

分析成功完成!
```

---

### 场景2：实盘筛选当前机会

```bash
# 关闭未来验证，只筛选当前满足条件的股票
python stock_trend_analyzer.py --no-future --mode standard
```

**输出CSV示例**（不含未来涨幅列）：
```csv
股票代码,股票名称,信号日期,收盘价,MACD评分,成交量比率,MA60距离%,评级,补充特征分,MACD满足,成交量满足,MA60满足
sh.600000,浦发银行,2026-02-06,10.12,65,2.35,-0.3,A级,35,True,True,True
sz.000001,平安银行,2026-02-06,12.35,58,2.15,-1.2,B级,25,True,True,True
```

---

### 场景3：快速测试（测试前50只股票）

```bash
python stock_trend_analyzer.py --limit 50
```

---

## 性能预估

- **处理时间**：2-5分钟（5187只股票）
- **内存占用**：峰值约300-500MB
- **预期输出**：50-150只股票，每只1-5个信号点
- **策略胜率**：预计55-65%（未来5日涨幅≥2%的概率）

---

## 常见问题

### Q1: 为什么某些股票没有信号？

A: 可能原因：
1. 数据不足60天（新股）
2. 不满足预筛选条件（停牌、价格超出范围、流动性不足）
3. 不满足核心特征条件（MACD评分<50、成交量未放大、已突破60日均线）
4. 被风险控制排除（连续涨停、短期暴涨、巨量滞涨）

### Q2: 如何调整成交量阈值？

A: 编辑 [config.py](config.py)：
```python
VOLUME_RATIO_THRESHOLD = 1.5  # 降低为1.5倍，会增加信号数量
```

### Q3: A/B/C级评级有何区别？

A: 评级基于**补充特征评分**（RSI、KDJ、布林带、形态、量价配合）：
- **A级**（≥30分）：多项补充指标优秀，建议优先关注
- **B级**（20-29分）：部分补充指标良好，值得关注
- **C级**（<20分）：仅满足核心特征，补充指标较弱

### Q4: 回测模式和实盘模式的区别？

A:
- **回测模式**（默认）：验证未来5日涨幅，计算策略胜率，用于评估策略有效性
- **实盘模式**（--no-future）：不验证未来涨幅，用于筛选当前满足条件的股票

### Q5: 如何找到最优参数？

A: 建议步骤：
1. 使用回测模式分析历史数据
2. 查看JSON报告中的`performance_stats`（胜率、平均收益）
3. 调整config.py中的参数（成交量阈值、MACD阈值等）
4. 重复步骤1-3，找到胜率和收益最优的参数组合

### Q6: 可以并行处理加速吗？

A: 当前版本为单线程处理（2-5分钟）。如需加速，可在[stock_trend_analyzer.py](stock_trend_analyzer.py)中使用`multiprocessing`库实现并行处理。

---

## 文件结构

```
stock_macd_volumn/
├── config.py                      # 参数配置
├── technical_indicators.py        # 技术指标计算
├── signal_detector.py             # 信号检测逻辑
├── stock_trend_analyzer.py        # 主分析器（入口）
├── daily_data_updater.py          # 每日数据更新工具（新增）
├── setup_daily_task.sh            # 定时任务配置脚本（新增）
├── README.md                      # 使用文档（本文件）
├── requirement.md                 # 需求说明
├── output/                        # 输出目录
│   ├── trend_signals_YYYYMMDD.csv
│   ├── analysis_report_YYYYMMDD.json
│   └── analysis.log
└── logs/                          # 日志目录（新增）
    └── daily_update.log
```

---

## 技术实现

- **技术指标计算**：使用Pandas向量化操作，高效计算MACD、RSI、KDJ等指标
- **信号检测**：多条件组合筛选，支持灵活的评分机制
- **风险控制**：自动排除高风险股票，提高策略安全性
- **模块化设计**：配置、计算、检测、分析分离，便于扩展和维护

---

## 后续优化方向

1. **参数优化**：通过网格搜索找到最优参数组合
2. **机器学习**：使用历史数据训练分类模型，提高预测准确率
3. **实时监控**：结合数据下载工具实现每日自动分析
4. **可视化**：为重点股票生成K线+指标图表
5. **性能优化**：使用multiprocessing实现并行处理

---

## 许可证

本项目仅供学习和研究使用。

---

## 相关链接

- [A股数据下载工具](../A_stock_data_download/README.md)
- [数据清洗工具](../basic_data_processing/README.md)
