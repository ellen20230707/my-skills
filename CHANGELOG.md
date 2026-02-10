# 更新日志 (Changelog)

## 2026-02-10 (下午更新)

### ✨ 新增功能

#### 1. CSV格式推荐报告
- ✅ 添加CSV格式的推荐输出（`recommendation_YYYYMMDD.csv`）
- ✅ 包含所有推荐股票的详细信息
- ✅ 便于Excel/Numbers分析和数据处理
- ✅ 与TXT/HTML/JSON格式同时生成

**修改文件**：
- `skills/stock_daily_recommendation/daily_recommendation.py`

**CSV包含字段**：
- 股票代码、股票名称、信号日期
- 收盘价、MACD评分、成交量比率、MA60距离%
- 评级、补充特征分、买入理由

---

#### 2. 反馈分析与自动调优系统 🎯

**核心功能**：基于用户反馈自动优化推荐参数

##### 2.1 反馈分析器 (`feedback_analyzer.py`)
- ✅ 读取用户反馈CSV文件
- ✅ 计算推荐准确性指标（精确率、召回率、F1分数）
- ✅ 分析混淆矩阵（真阳性、假阳性、假阴性、真阴性）
- ✅ 分析推荐时机（提前天数分布）
- ✅ 生成调优建议
- ✅ 自动生成调优配置文件

**新增文件**：
- `skills/stock_daily_recommendation/feedback_analyzer.py`

##### 2.2 反馈分析运行脚本 (`run_feedback_analysis.py`)
- ✅ 自动查找最新反馈文件
- ✅ 自动查找最新推荐CSV
- ✅ 完整的分析流程和日志输出
- ✅ 生成 `tuning_config.json`

**新增文件**：
- `skills/stock_daily_recommendation/run_feedback_analysis.py`

##### 2.3 自动加载调优配置
- ✅ 推荐工具启动时自动加载 `tuning_config.json`
- ✅ 动态调整推荐参数：
  - `SIGNAL_LOOKBACK_DAYS` - 信号回溯天数
  - `MIN_ENHANCED_SCORE` - 最低补充特征分
  - `MIN_RATING` - 最低评级要求
  - `TOP_N_STOCKS` - 推荐数量
- ✅ 日志显示参数调整前后对比
- ✅ 显示调优依据和统计数据

**修改文件**：
- `skills/stock_daily_recommendation/daily_recommendation.py` - 添加 `load_tuning_config()` 方法

##### 2.4 GitHub Actions自动化反馈分析
- ✅ 每天18:30 GMT+8自动运行反馈分析
- ✅ 自动查找最新反馈文件
- ✅ 生成调优配置并提交到仓库
- ✅ 支持手动触发
- ✅ 详细的执行摘要和日志

**新增文件**：
- `.github/workflows/feedback-analysis.yml`

##### 2.5 反馈文件模板和文档
- ✅ 反馈CSV模板文件
- ✅ 完整的使用指南（反馈格式、填写规则、使用流程）
- ✅ 故障排除和最佳实践

**新增文件**：
- `skills/stock_daily_recommendation/turning_feedback/feedback_template.csv`
- `skills/stock_daily_recommendation/turning_feedback/README.md`

---

### 🔄 完整反馈闭环流程

```
Day 1 (22:00) - 生成推荐报告
    ↓
Day 2-5 - 用户观察推荐股票表现
    ↓
Day 5 (18:00前) - 用户提交反馈CSV
    格式: stock\tBest recommendation buy day
    示例: sh.600000\t20260205 或 sz.000001\tnot recommended
    ↓
Day 5 (18:30) - GitHub Actions自动分析反馈
    • 计算精确率、召回率、F1分数
    • 分析推荐时机
    • 生成调优建议
    • 保存 tuning_config.json
    • 提交到仓库
    ↓
Day 6 (22:00) - 应用新参数生成推荐
    • 自动加载 tuning_config.json
    • 使用优化后的参数
    • 日志显示参数变化
    ↓
持续优化...
```

---

### 📊 调优指标说明

**精确率 (Precision)**：正确推荐数 / 总推荐数
- 低精确率 → 假阳性多 → 提高筛选标准

**召回率 (Recall)**：正确推荐数 / 应推荐总数
- 低召回率 → 遗漏多 → 放宽筛选标准

**F1分数**：精确率和召回率的调和平均
- 综合评价指标

**推荐时机**：推荐日期与最佳买入日期的时间差
- 平均提前过多 → 减少SIGNAL_LOOKBACK_DAYS
- 平均提前过少 → 增加SIGNAL_LOOKBACK_DAYS

---

### 💡 使用示例

#### 创建反馈文件

```bash
# 基于今天的推荐创建反馈
cd skills/stock_daily_recommendation/turning_feedback
cp feedback_template.csv tuning_feedback_20260210.csv

# 编辑文件，填写每只股票的反馈
# 格式: stock[TAB]Best recommendation buy day
# 示例:
#   sh.600000	20260210        # 推荐正确，当天最佳
#   sz.000001	not recommended  # 推荐错误，不应推荐
#   sh.600036	20260208        # 应该更早推荐（提前2天）
```

#### 手动运行反馈分析

```bash
cd skills/stock_daily_recommendation
python run_feedback_analysis.py
```

#### 查看调优配置

```bash
cat tuning_config.json
```

输出示例：
```json
{
  "SIGNAL_LOOKBACK_DAYS": 5,
  "MIN_ENHANCED_SCORE": 25,
  "MIN_RATING": "B",
  "TOP_N_STOCKS": 20,
  "tuning_date": "2026-02-10",
  "feedback_stats": {
    "precision": 0.45,
    "recall": 0.64,
    "f1_score": 0.53
  },
  "tuning_reason": "根据反馈分析自动调优"
}
```

---

## 2026-02-10 (上午更新)

### ✨ 新增功能

#### 1. GitHub Actions 自动化支持
- ✅ 添加每日数据更新工作流（21:00 GMT+8自动执行）
- ✅ 添加每日推荐生成工作流（22:00 GMT+8自动执行）
- ✅ 添加手动测试工作流
- ✅ 支持云端全自动运行，不依赖本地电脑
- ✅ 正确处理时区转换（GMT+8 → UTC）

**相关文件**：
- `.github/workflows/daily-data-update.yml`
- `.github/workflows/daily-recommendation.yml`
- `.github/workflows/manual-test.yml`
- `GITHUB_ACTIONS_SETUP.md` - 完整配置指南
- `QUICK_START_GITHUB_ACTIONS.md` - 快速开始指南

#### 2. 信号时效性优化
- ✅ **推荐范围调整**：从"仅当天信号"改为"最近7天信号"
- ✅ 增加可配置参数 `SIGNAL_LOOKBACK_DAYS`
- ✅ 自动去重：每只股票只保留最近的信号
- ✅ 日志显示每日信号分布统计

**修改文件**：
- `skills/stock_daily_recommendation/daily_recommendation.py`

**原因和优势**：
- 📈 **捕获更多机会**：不错过最近几天产生的优质信号
- 🎯 **更符合实际**：很多信号在产生后的几天内都有效
- ⚡ **灵活可调**：可通过配置参数调整回溯天数
- 📊 **智能去重**：每只股票只保留最新的高分信号

---

### 🔧 技术改进

#### 信号筛选逻辑优化

**修改前**：
```python
# 只保留信号日期是当天的股票
today = pd.Timestamp.now().normalize()
df = df[df['信号日期'].dt.normalize() == today]
```

**修改后**：
```python
# 只保留信号日期是最近N天的股票
today = pd.Timestamp.now().normalize()
lookback_date = today - pd.Timedelta(days=RecommendationConfig.SIGNAL_LOOKBACK_DAYS)
df = df[df['信号日期'].dt.normalize() >= lookback_date]

# 每只股票只保留最近的信号
df = df.sort_values('信号日期', ascending=False)
df = df.drop_duplicates(subset=['股票代码'], keep='first')
```

**新增配置参数**：
```python
class RecommendationConfig:
    # 信号日期范围
    SIGNAL_LOOKBACK_DAYS = 7  # 只推荐最近N天内的信号（默认7天）
```

---

### 📊 数据统计增强

#### 新增日志输出

```python
logger.info(f"最近{RecommendationConfig.SIGNAL_LOOKBACK_DAYS}天信号数: {len(df)}")

# 统计每天的信号数量
daily_counts = df.groupby(df['信号日期'].dt.date).size()
logger.info(f"每日信号分布:\n{daily_counts}")
```

**输出示例**：
```
最近7天信号数: 342
每日信号分布:
2026-02-03    45
2026-02-04    52
2026-02-05    48
2026-02-06    67
2026-02-07    58
2026-02-08    42
2026-02-09    30
```

---

### 📝 文档更新

#### 更新的文档

1. **`skills/stock_daily_recommendation/README.md`**
   - ✅ 添加"信号时效性"章节
   - ✅ 更新配置参数说明
   - ✅ 更新示例输出

2. **`GITHUB_ACTIONS_SETUP.md`** (新增)
   - ✅ 完整的GitHub Actions配置指南
   - ✅ 详细的故障排除说明
   - ✅ 时区转换说明

3. **`QUICK_START_GITHUB_ACTIONS.md`** (新增)
   - ✅ 5分钟快速部署指南
   - ✅ 常用操作速查表
   - ✅ 移动端访问说明

---

### 🎨 报告格式更新

#### 文本报告
```
🎯 本周推荐（前20只，最近7天信号）：
```

#### HTML报告
```html
<h3>🎯 本周推荐（最近7天信号）</h3>
```

---

## 配置参数对照表

### 推荐配置 (RecommendationConfig)

| 参数 | 默认值 | 说明 | 修改位置 |
|------|--------|------|---------|
| `TOP_N_STOCKS` | 20 | 推荐股票数量 | daily_recommendation.py |
| `SIGNAL_LOOKBACK_DAYS` | 7 | 信号回溯天数 | daily_recommendation.py (新增) |
| `MIN_RATING` | 'B' | 最低评级要求 | daily_recommendation.py |
| `MIN_ENHANCED_SCORE` | 20 | 最低补充特征分数 | daily_recommendation.py |
| `REPORT_FORMAT` | 'both' | 报告格式 | daily_recommendation.py |

---

## 使用示例

### 调整信号回溯天数

**场景1：只要最近3天的信号（更保守）**
```python
class RecommendationConfig:
    SIGNAL_LOOKBACK_DAYS = 3  # 改为3天
```

**场景2：扩大到最近14天（更宽松）**
```python
class RecommendationConfig:
    SIGNAL_LOOKBACK_DAYS = 14  # 改为14天
```

**场景3：只要当天的信号（最严格）**
```python
class RecommendationConfig:
    SIGNAL_LOOKBACK_DAYS = 1  # 改为1天（即当天）
```

---

## 测试验证

### 本地测试
```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_daily_recommendation
source ../../venv/bin/activate
python daily_recommendation.py
```

### 查看结果
```bash
# 查看最新推荐
cat recommendations/recommendation_*.txt | head -50

# 查看日志
tail -f logs/recommendation.log
```

### 验证信号日期范围
检查生成的报告，确认所有推荐的股票信号日期都在最近7天内。

---

## 向后兼容性

✅ **完全向后兼容**
- 默认配置保持推荐前20只股票
- 默认信号回溯7天，可调整为1天恢复原行为
- 所有其他功能和参数保持不变
- 报告格式和字段保持一致

---

## 升级建议

### 对于本地运行用户
1. ✅ 拉取最新代码
2. ✅ 无需修改配置（默认值已优化）
3. ✅ 直接运行即可

### 对于使用GitHub Actions用户
1. ✅ 提交最新代码到GitHub
2. ✅ 工作流会自动使用新逻辑
3. ✅ 无需修改工作流文件

---

## 已知问题

无

---

## 下一步计划

- [ ] 添加Slack/邮件通知功能
- [ ] 支持多个回测周期对比
- [ ] 添加推荐历史跟踪和回测统计
- [ ] 支持自定义评分权重
- [ ] 添加可视化图表生成

---

## 贡献者

- Claude (AI Assistant)
- Ellen Li (Project Owner)

---

**版本**: v1.1.0
**发布日期**: 2026-02-10
**更新类型**: 功能增强 + 自动化支持
