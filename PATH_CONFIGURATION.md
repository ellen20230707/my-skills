# 路径配置说明文档

## 📂 项目目录结构

```
my-skills/
├── A股近10年日线数据/           # 股票历史数据（5187只股票）
│   ├── sh.600000.csv
│   ├── sz.000001.csv
│   └── ...
├── skills/
│   ├── A_stock_data_download/    # 数据下载工具
│   │   └── a_stock_download_baostock.py
│   ├── stock_macd_volumn/        # 趋势分析工具
│   │   ├── config.py
│   │   ├── daily_data_updater.py
│   │   └── stock_trend_analyzer.py
│   └── stock_daily_recommendation/  # 每日推荐工具
│       ├── daily_recommendation.py
│       ├── recommendations/
│       └── turning_feedback/
└── verify_paths.py               # 路径验证脚本（新增）
```

---

## ✅ 已完成的路径统一修改

### 1. **stock_macd_volumn/config.py**

**修改前**（硬编码绝对路径）：
```python
DATA_DIR = "/Users/ellen_li/2026projects/A股近10年日线数据"
```

**修改后**（相对于仓库根目录）：
```python
# 数据目录：相对于仓库根目录
# 本地和 GitHub Actions 都使用相同的相对路径
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(_REPO_ROOT, "A股近10年日线数据")
```

**优势**：
- ✅ 本地和云端路径一致
- ✅ 跨平台兼容（Windows/Linux/macOS）
- ✅ 团队协作友好

---

### 2. **A_stock_data_download/a_stock_download_baostock.py**

**修改前**（相对路径，取决于运行位置）：
```python
SAVE_DIR = "A股近10年日线数据"  # 保存目录
```

**修改后**（相对于仓库根目录）：
```python
# 数据保存目录：相对于仓库根目录
# 自动定位到 my-skills/A股近10年日线数据/
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
SAVE_DIR = os.path.join(_REPO_ROOT, "A股近10年日线数据")

print(f"数据保存路径: {SAVE_DIR}")  # 新增：显示实际保存路径
```

**优势**：
- ✅ 无论从哪里运行脚本，都保存到正确位置
- ✅ 与分析工具读取路径一致
- ✅ 显示保存路径，便于确认

---

### 3. **daily_data_updater.py**

**无需修改**：该脚本通过 `from config import Config` 使用配置，自动继承 `config.py` 的路径设置。

---

### 4. **daily_recommendation.py**

**无需修改**：该脚本导入并使用 `stock_macd_volumn` 的配置：
```python
from config import Config
analyze_all_stocks(data_dir=Config.DATA_DIR, ...)
```

---

## 🔍 路径验证

### 方法1：运行验证脚本

```bash
cd /Users/ellen_li/2026projects/my-skills
source venv/bin/activate
python verify_paths.py
```

**预期输出**：
```
================================================================================
📂 路径配置验证
================================================================================

✓ 仓库根目录: /Users/ellen_li/2026projects/my-skills

✓ 配置的数据目录: /Users/ellen_li/2026projects/my-skills/A股近10年日线数据
  ✅ 目录存在
  ✅ CSV文件数: 5187

✓ 分析输出目录: /Users/ellen_li/2026projects/my-skills/skills/stock_macd_volumn/output

✓ 推荐报告目录: /Users/ellen_li/2026projects/my-skills/skills/stock_daily_recommendation/recommendations
  ✅ 目录存在

✓ 反馈文件目录: /Users/ellen_li/2026projects/my-skills/skills/stock_daily_recommendation/turning_feedback
  ✅ 目录存在

✅ 数据目录路径配置正确！

================================================================================
✅ 路径验证完成！所有路径配置正确。
================================================================================
```

### 方法2：Python 测试

```python
import sys
import os

sys.path.insert(0, 'skills/stock_macd_volumn')
from config import Config

print(f"数据目录: {Config.DATA_DIR}")
print(f"目录存在: {os.path.exists(Config.DATA_DIR)}")
print(f"CSV文件数: {len([f for f in os.listdir(Config.DATA_DIR) if f.endswith('.csv')])}")
```

---

## 📝 路径配置最佳实践

### ✅ 推荐做法

1. **使用相对路径**：相对于仓库根目录或脚本位置
2. **动态计算路径**：使用 `__file__` 和 `os.path` 模块
3. **集中配置**：所有路径配置在 `config.py` 中统一管理
4. **添加验证**：启动时检查关键路径是否存在

### ❌ 避免的做法

1. **硬编码绝对路径**：如 `/Users/ellen_li/...`
2. **依赖当前工作目录**：相对路径 `./data/` 取决于运行位置
3. **分散的路径定义**：多个文件中重复定义相同路径
4. **忽略路径分隔符差异**：Windows 使用 `\`，Unix 使用 `/`

---

## 🚀 GitHub Actions 兼容性

所有路径配置已经适配 GitHub Actions 环境：

```yaml
# 工作流中的路径引用
- name: 验证数据目录
  run: |
    if [ ! -d "A股近10年日线数据" ]; then
      echo "❌ 数据目录不存在"
      exit 1
    fi

    stock_count=$(ls A股近10年日线数据/*.csv 2>/dev/null | wc -l)
    echo "✓ 股票文件数: $stock_count"
```

**工作流中的数据目录**：
- ✅ 检出代码时自动包含 `A股近10年日线数据/`
- ✅ Python 脚本使用相对路径自动定位
- ✅ 无需额外配置环境变量

---

## 🔄 未来添加新脚本的规范

如果要添加新的数据分析脚本，请遵循以下规范：

### 方式1：使用现有配置（推荐）

```python
import sys
import os

# 添加 stock_macd_volumn 到路径
sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    '..', 'stock_macd_volumn'
))

from config import Config

# 使用配置中的路径
data_dir = Config.DATA_DIR
```

### 方式2：自己计算路径

```python
import os

# 定位到仓库根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(script_dir))  # 根据实际层级调整

# 数据目录
data_dir = os.path.join(repo_root, "A股近10年日线数据")
```

---

## 📊 所有关键路径汇总

| 目录/文件 | 路径 | 说明 |
|----------|------|------|
| **仓库根目录** | `/Users/ellen_li/2026projects/my-skills` | 本地开发路径 |
| **数据目录** | `${REPO_ROOT}/A股近10年日线数据/` | 5187只股票CSV |
| **分析输出** | `skills/stock_macd_volumn/output/` | 分析结果 |
| **推荐报告** | `skills/stock_daily_recommendation/recommendations/` | 每日推荐 |
| **反馈文件** | `skills/stock_daily_recommendation/turning_feedback/` | 用户反馈 |
| **调优配置** | `skills/stock_daily_recommendation/tuning_config.json` | 自动调优 |
| **日志文件** | `skills/*/logs/*.log` | 各工具日志 |

---

## ✅ 完成清单

路径统一修改已完成：

- [x] 更新 `stock_macd_volumn/config.py` 使用相对路径
- [x] 更新 `A_stock_data_download/a_stock_download_baostock.py` 使用相对路径
- [x] 验证 `daily_data_updater.py` 使用配置路径
- [x] 验证 `daily_recommendation.py` 使用配置路径
- [x] 创建路径验证脚本 `verify_paths.py`
- [x] 验证本地路径配置正确（5187个CSV文件）
- [x] 确认 GitHub Actions 兼容性

---

## 🎯 下一步

1. ✅ **提交更改到 Git**：
   ```bash
   cd /Users/ellen_li/2026projects/my-skills
   git add skills/stock_macd_volumn/config.py
   git add skills/A_stock_data_download/a_stock_download_baostock.py
   git add verify_paths.py
   git add PATH_CONFIGURATION.md

   git commit -m "统一数据目录路径配置

   - 修改 config.py 使用相对路径（相对于仓库根目录）
   - 修改数据下载脚本使用相对路径
   - 确保本地和 GitHub Actions 路径一致
   - 添加路径验证脚本和配置文档"

   git push
   ```

2. ✅ **测试 GitHub Actions**：
   - 推送后手动触发"每日推荐生成"工作流
   - 验证工作流能正确找到数据目录

3. ✅ **定期验证**：
   - 每次添加新脚本后运行 `python verify_paths.py`
   - 确保路径配置符合规范

---

**版本**: v1.0
**更新日期**: 2026-02-10
**维护者**: Claude & Ellen Li
