# [分类名称]

[一句话描述这个分类的用途]

## 📦 包含的Skills

### skill_name.py
**功能：** [简短描述]

**主要函数：**
- `function_name()` - 函数描述

**使用场景：**
- 场景1
- 场景2

**示例：**
```python
from skills.category.skill_name import function_name

result = function_name()
```

---

## 🔗 依赖
```
package1>=1.0.0
package2>=2.0.0
```

## 📝 添加新工具

在此目录添加新的Python文件后，请在本README中添加说明。

---
最后更新：YYYY-MM-DD
```

---

## 其他配置文件

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp

# 数据文件
*.csv
*.xlsx
*.xls
data/
output/

# 配置文件（如包含敏感信息）
config.ini
.env

# 日志
*.log

# 测试
.pytest_cache/
.coverage
```

### requirements.txt（初始版本）
```
pandas>=2.0.0
numpy>=1.24.0
openpyxl>=3.1.0
matplotlib>=3.7.0
seaborn>=0.12.0
chardet>=5.0.0
python-dateutil>=2.8.0