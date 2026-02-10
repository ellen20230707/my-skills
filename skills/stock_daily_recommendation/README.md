# 每日股票推荐工具

每天自动分析全市场A股，基于技术指标筛选并推荐第二天可以买入的优质股票，并提供详细的买入理由。

## 功能特点

- ✅ **自动化推荐**：每天22:00自动运行，生成第二天的买入推荐
- ✅ **基于量化分析**：基于[stock_macd_volumn](../stock_macd_volumn/)的多指标综合分析
- ✅ **详细理由**：为每只推荐股票提供详细的买入理由和技术指标说明
- ✅ **多种格式**：生成文本、HTML、JSON三种格式报告
- ✅ **智能排序**：综合评分排序，优先推荐最优股票
- ✅ **风险提示**：包含风险提示和投资建议

## 环境要求

- Python 3.7+
- 依赖库：pandas, numpy, baostock
- 需要先配置[stock_macd_volumn](../stock_macd_volumn/)工具

## 快速开始

### 1. 一键设置定时任务

```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_daily_recommendation
./setup_daily_task.sh
```

设置完成后，每天22:00会自动生成推荐报告。

### 2. 手动运行（立即生成推荐）

```bash
cd /Users/ellen_li/2026projects/my-skills/skills/stock_daily_recommendation
source ../../venv/bin/activate
python daily_recommendation.py
```

### 3. 查看推荐报告

```bash
# 文本报告
cat recommendations/recommendation_*.txt

# HTML报告（在浏览器中打开）
open recommendations/recommendation_*.html

# JSON数据
cat recommendations/recommendation_*.json
```

---

## 推荐逻辑

### 分析流程

```
第一步：运行技术分析
    ↓
调用 stock_macd_volumn 分析工具
分析全市场5187只A股
使用实盘模式（不验证未来涨幅）
    ↓
第二步：筛选过滤
    ↓
评级过滤：只保留 A级 和 B级
补充特征分≥20分
每只股票只取最近的信号
    ↓
第三步：综合评分排序
    ↓
评分公式 = MACD评分×0.3 + 成交量比率×10 + 补充特征分×0.4
按综合得分降序排列
    ↓
第四步：生成推荐报告
    ↓
取前20只股票
为每只股票生成详细买入理由
输出多种格式报告
```

---

### 信号时效性

**只推荐最近7天内产生的信号**：
- 确保推荐的及时性
- 避免过时信号干扰
- 每只股票只取最近的信号

可通过 `SIGNAL_LOOKBACK_DAYS` 参数调整天数。

### 核心筛选标准

推荐的股票需要满足以下**至少3个**核心特征：

1. **MACD上涨趋势** - 评分≥50分
   - DIF > DEA（金叉状态）
   - DIF和DEA在零轴上方
   - MACD柱状图为正
   - DIF连续上升

2. **成交量放大** - ≥2.0倍
   - 近3日均量 > 前20日均量的2倍以上
   - 表示资金开始关注

3. **低位启动** - 未突破60日均线
   - 最高价 ≤ 60日均线 + 0.5%
   - 避免追高，在低位买入

4. **补充指标确认**
   - RSI在黄金区间（40-70）
   - KDJ金叉信号
   - 布林带收窄待突破
   - 价格形态良好（突破平台、V型反转等）
   - 量价齐升

---

### 买入理由说明

每只推荐股票的理由包含以下维度：

#### 📈 MACD分析
- **强势上涨**（80分以上）：多项MACD指标优秀，上涨动能强
- **明确趋势**（65-79分）：金叉信号良好，趋势确立
- **上涨信号**（50-64分）：满足基本上涨条件

#### 💪 成交量分析
- **剧烈放大**（≥3.0倍）：资金大量介入，关注度高
- **明显放大**（2.5-2.9倍）：交投活跃
- **温和放大**（2.0-2.4倍）：交易开始升温

#### 🎯 位置分析
- **临界突破**（-3% ~ 0.5%）：距离60日均线很近，最佳买入点
- **深度蓄势**（< -10%）：远低于均线，上涨空间大
- **低位启动**（其他）：未追高风险

#### ✨ 补充指标
- RSI黄金区间：强弱适中，不超买
- KDJ金叉：短期上涨概率高
- 布林带收窄：即将突破
- 价格形态：突破平台、V型反转、回调企稳
- 量价齐升：上涨动能充足

#### ⭐ 综合评级
- **A级**（≥30分）：多项补充指标优秀，强烈推荐
- **B级**（20-29分）：部分补充指标良好，值得关注

---

## 报告格式

### 1. 文本报告 (recommendation_YYYYMMDD.txt)

```
================================================================================
📊 2026年02月10日 股票买入推荐报告
================================================================================

📈 市场概况：
   • 分析股票数：5187 只
   • 发现信号：342 个
   • 有信号股票：127 只
   • 筛选模式：standard

⭐ 评级分布：
   • A级：42 个信号
   • B级：138 个信号
   • C级：162 个信号

🎯 今日推荐（前20只）：

【1】润禾材料 (sz.300727) - A级
   信号日期：2026-02-09
   当前价格：¥68.50
   MACD评分：85 | 成交量比率：2.85倍 | 综合评分：35

   📝 买入理由：
   📈 MACD强势上涨(85分)，多项指标优秀
   💪 成交量明显放大(2.85倍)，交投活跃
   🎯 临界突破位置(距60日均线-1.2%)，最佳买入点
   ✨ RSI处于黄金区间(58.3)，强弱适中
   ✨ KDJ金叉信号，短期上涨概率高
   ✨ 量价配合良好，上涨动能充足
   ⭐ A级推荐(综合35分)，多项补充指标优秀

--------------------------------------------------------------------------------

【2】数据港 (sh.603881) - A级
   ...
```

### 2. HTML报告 (recommendation_YYYYMMDD.html)

精美的网页格式，包含：
- 响应式设计，支持手机/平板浏览
- 股票卡片展示，悬停效果
- 颜色标识评级（A级红色、B级蓝色）
- 交互式布局，易于阅读

**在浏览器中打开查看效果最佳！**

### 3. JSON数据 (recommendation_YYYYMMDD.json)

```json
{
  "date": "20260210",
  "summary": {
    "total_stocks": 5187,
    "total_signals": 342,
    "stocks_with_signals": 127,
    "filter_mode": "standard",
    "rating_distribution": {
      "A级": 42,
      "B级": 138,
      "C级": 162
    }
  },
  "recommendations": [
    {
      "stock_code": "sz.300727",
      "stock_name": "润禾材料",
      "date": "2026-02-09",
      "close": 68.5,
      "macd_score": 85,
      "volume_ratio": 2.85,
      "ma60_distance": -1.2,
      "rating": "A级",
      "enhanced_score": 35,
      "buy_reason": "..."
    }
  ]
}
```

---

## 配置选项

编辑 `daily_recommendation.py` 中的 `RecommendationConfig` 类：

```python
class RecommendationConfig:
    # 推荐数量
    TOP_N_STOCKS = 20  # 推荐前20只股票

    # 信号日期范围
    SIGNAL_LOOKBACK_DAYS = 7  # 只推荐最近N天内的信号

    # 评级过滤
    MIN_RATING = 'B'  # 最低评级要求（A/B/C）

    # 补充特征分数要求
    MIN_ENHANCED_SCORE = 20  # A级≥30, B级≥20

    # 报告格式
    REPORT_FORMAT = 'both'  # 'text', 'html', 'both'
```

**配置说明：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `TOP_N_STOCKS` | 20 | 推荐股票数量 |
| `SIGNAL_LOOKBACK_DAYS` | 7 | 信号回溯天数（只推荐最近N天的信号） |
| `MIN_RATING` | 'B' | 最低评级（'A'只要A级，'B'要A级和B级，'C'全部） |
| `MIN_ENHANCED_SCORE` | 20 | 补充特征最低分数 |
| `REPORT_FORMAT` | 'both' | 报告格式（'text'/'html'/'both'） |

---

## 定时任务管理

### 查看定时任务

```bash
crontab -l | grep daily_recommendation
```

### 编辑定时任务

```bash
crontab -e
```

### 修改执行时间

编辑crontab，修改时间：

```bash
# 每天22:00执行（默认）
0 22 * * * cd /path/to/script && python daily_recommendation.py

# 改为每天20:00执行
0 20 * * * cd /path/to/script && python daily_recommendation.py

# 改为每周一22:00执行
0 22 * * 1 cd /path/to/script && python daily_recommendation.py
```

### 删除定时任务

```bash
crontab -e
# 删除包含 daily_recommendation.py 的行
```

---

## 使用场景

### 场景1：每日自动推荐

设置定时任务后，每天22:00自动运行：
1. 分析当天的股票数据
2. 生成第二天的买入推荐
3. 保存为多种格式报告

次日早上查看报告，决定买入标的。

### 场景2：手动立即分析

```bash
python daily_recommendation.py
```

立即生成当前推荐，用于：
- 盘中决策参考
- 测试配置效果
- 手动触发分析

### 场景3：查看历史推荐

```bash
# 查看所有历史报告
ls -lh recommendations/

# 查看特定日期的推荐
cat recommendations/recommendation_20260209.txt
```

---

## 性能说明

- **分析时间**：2-5分钟（全市场5187只股票）
- **推荐生成**：<1秒
- **报告大小**：
  - TXT文本：约10-20KB
  - HTML网页：约30-50KB
  - JSON数据：约10-15KB

---

## 注意事项

1. **运行时间**：22:00是因为：
   - 数据更新工具在21:00运行
   - 确保分析的是最新数据
   - 有足够时间在次日开盘前查看

2. **评级说明**：
   - A级：强烈推荐，多项指标优秀
   - B级：值得关注，部分指标良好
   - C级：一般观察（默认不推荐）

3. **风险控制**：
   - 本工具仅供参考，不构成投资建议
   - 股市有风险，投资需谨慎
   - 建议设置止损位
   - 分散投资，控制仓位

4. **数据依赖**：
   - 需要先运行数据更新工具（21:00）
   - 确保CSV数据是最新的
   - 如果数据更新失败，推荐也会受影响

---

## 故障排除

### Q1: 推荐数量很少或为0？

可能原因：
- 市场整体走弱，符合条件的股票少
- 筛选条件过严（降低`MIN_ENHANCED_SCORE`）
- 数据未更新

解决方法：
```python
# 调整配置
MIN_RATING = 'C'  # 放宽评级要求
MIN_ENHANCED_SCORE = 15  # 降低分数要求
TOP_N_STOCKS = 30  # 增加推荐数量
```

### Q2: 定时任务未执行？

检查步骤：
```bash
# 1. 确认cron服务
ps aux | grep cron

# 2. 查看crontab配置
crontab -l

# 3. 查看日志
tail -f logs/recommendation.log

# 4. 手动测试
python daily_recommendation.py
```

### Q3: HTML报告无法打开？

确保使用浏览器打开：
```bash
# macOS
open recommendations/recommendation_*.html

# Linux
xdg-open recommendations/recommendation_*.html

# Windows
start recommendations/recommendation_*.html
```

---

## 文件结构

```
stock_daily_recommendation/
├── daily_recommendation.py        # 主推荐脚本
├── setup_daily_task.sh            # 定时任务配置脚本
├── README.md                      # 使用文档（本文件）
├── logs/                          # 日志目录
│   └── recommendation.log
└── recommendations/               # 推荐报告目录
    ├── recommendation_20260209.txt
    ├── recommendation_20260209.html
    └── recommendation_20260209.json
```

---

## 依赖关系

本工具依赖于：
- [stock_macd_volumn](../stock_macd_volumn/) - 核心技术分析引擎
- [A_stock_data_download](../A_stock_data_download/) - 数据下载工具

建议的完整工作流：
```
21:00 - 数据更新 (stock_macd_volumn/daily_data_updater.py)
   ↓
22:00 - 生成推荐 (stock_daily_recommendation/daily_recommendation.py)
   ↓
次日早上 - 查看报告，决策买入
```

---

## 示例：完整设置流程

```bash
# 1. 确保虚拟环境已配置
cd /Users/ellen_li/2026projects/my-skills
source venv/bin/activate
pip install pandas numpy baostock

# 2. 设置数据更新定时任务（21:00）
cd skills/stock_macd_volumn
./setup_daily_task.sh

# 3. 设置推荐定时任务（22:00）
cd ../stock_daily_recommendation
./setup_daily_task.sh

# 4. 验证定时任务
crontab -l

# 5. 手动测试一次
python daily_recommendation.py

# 6. 查看报告
open recommendations/recommendation_*.html
```

---

## 许可证

本项目仅供学习和研究使用。

---

## 相关链接

- [股票趋势分析工具](../stock_macd_volumn/README.md)
- [A股数据下载工具](../A_stock_data_download/README.md)
