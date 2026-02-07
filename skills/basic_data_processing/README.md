# 数据处理工具集

数据清洗、转换、文件处理相关的工具函数

## 📦 包含的Skills

### data_cleaner.py
**功能：** 全面的数据清洗和质量检查工具

**主要函数：**

#### `clean_data(df, **options)`
一站式数据清洗函数，支持多种清洗选项
- 删除重复行
- 处理缺失值（删除/填充均值/中位数/零值）
- 标准化列名
- 移除异常值

**参数：**
- `drop_duplicates`: 是否删除重复行（默认True）
- `handle_missing`: 缺失值处理方式 ('drop', 'fill_mean', 'fill_median', 'fill_zero')
- `standardize_columns`: 是否标准化列名（默认True）
- `remove_outliers`: 是否移除异常值（默认False）
- `outlier_threshold`: 异常值Z-score阈值（默认3.0）

#### `standardize_column_names(df)`
标准化列名：转小写、去空格、替换特殊字符

#### `handle_missing_values(df, method, columns)`
灵活的缺失值处理

#### `remove_outliers_zscore(df, threshold, columns)`
使用Z-score方法识别并移除异常值

#### `get_data_quality_report(df)`
生成详细的数据质量报告（字典格式）

#### `print_quality_report(df)`
打印格式化的数据质量报告

**使用场景：**
- 📊 数据分析前的预处理
- 🔍 原始数据质量检查
- 🧹 批量数据清洗
- 📈 数据标准化

**完整示例：**
```python
from skills.data_processing.data_cleaner import clean_data, print_quality_report
import pandas as pd

# 读取原始数据
df = pd.read_csv('raw_data.csv')

# 查看数据质量
print_quality_report(df)

# 清洗数据
cleaned_df = clean_data(
    df,
    drop_duplicates=True,
    handle_missing='fill_median',
    standardize_columns=True,
    remove_outliers=True,
    outlier_threshold=3.0
)

# 保存清洗后的数据
cleaned_df.to_csv('cleaned_data.csv', index=False)
```

**单独使用各个函数：**
```python
from skills.data_processing.data_cleaner import (
    standardize_column_names,
    handle_missing_values,
    remove_outliers_zscore
)

# 只标准化列名
df = standardize_column_names(df)

# 只处理缺失值
df = handle_missing_values(df, method='fill_mean', columns=['age', 'salary'])

# 只移除异常值
df = remove_outliers_zscore(df, threshold=2.5, columns=['salary'])
```

---

## 🔗 依赖
```
pandas>=2.0.0
numpy>=1.24.0
```

## 📝 添加新工具

在此目录添加新的Python文件后，请在本README中添加说明。

---
最后更新：2024-02-07