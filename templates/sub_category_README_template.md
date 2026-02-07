# 数据处理工具集

数据清洗、转换、文件处理相关的工具函数

## 📦 包含的Skills

### data_cleaner.py
**功能：** 数据清洗和预处理

**主要函数：**
- `clean_data(df)` - 清洗DataFrame，处理缺失值和异常值
- `remove_duplicates(df)` - 删除重复行
- `standardize_columns(df)` - 标准化列名

**使用场景：**
- 处理原始数据前的清洗工作
- 数据质量检查
- 数据标准化

**示例：**
```python
from skills.data_processing.data_cleaner import clean_data
import pandas as pd

df = pd.read_csv('raw_data.csv')
cleaned_df = clean_data(df)
```

---

### csv_handler.py
**功能：** CSV文件的读取、处理和保存

**主要函数：**
- `read_csv_safe(filepath)` - 安全读取CSV（自动检测编码）
- `merge_csv_files(file_list)` - 合并多个CSV文件
- `split_csv_by_column(filepath, column)` - 按列值拆分CSV

**使用场景：**
- 批量处理CSV文件
- 合并来自不同来源的数据
- 按条件拆分大文件

**示例：**
```python
from skills.data_processing.csv_handler import merge_csv_files

files = ['data1.csv', 'data2.csv', 'data3.csv']
merged = merge_csv_files(files)
merged.to_csv('merged_output.csv')
```

---

### excel_handler.py
**功能：** Excel文件的高级处理

**主要函数：**
- `read_excel_sheets(filepath)` - 读取所有工作表
- `write_multiple_sheets(data_dict, filepath)` - 写入多个工作表
- `format_excel(filepath)` - 格式化Excel文件

**使用场景：**
- 处理多sheet的Excel文件
- 生成格式化的报表
- 批量Excel操作

**示例：**
```python
from skills.data_processing.excel_handler import read_excel_sheets

sheets = read_excel_sheets('report.xlsx')
for sheet_name, df in sheets.items():
    print(f"Sheet: {sheet_name}, Rows: {len(df)}")
```

## 🔗 依赖
```
pandas>=2.0.0
openpyxl>=3.1.0
chardet>=5.0.0
```

## 📝 添加新工具

在此目录添加新的Python文件后，请在本README中添加说明。

---
最后更新：2024-02-07