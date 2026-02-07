# My Skills Library

个人Python技能库 - 工作与生活效率工具集合

## 📋 目录结构

### 数据处理 (`skills/data_processing/`)
处理各类数据文件的工具集
- `data_cleaner.py` - 数据清洗工具
- `csv_handler.py` - CSV文件处理
- `excel_handler.py` - Excel文件处理

### 数据分析 (`skills/data_analysis/`)
数据分析和可视化工具
- `statistical_analysis.py` - 统计分析工具
- `visualization.py` - 数据可视化

### 工作自动化 (`skills/work_automation/`)
提升工作效率的自动化脚本
- `email_sender.py` - 批量邮件发送
- `report_generator.py` - 自动生成报告
- `file_organizer.py` - 文件自动整理

### 生活效率 (`skills/life_productivity/`)
日常生活效率提升工具
- `expense_tracker.py` - 个人记账工具
- `reminder_system.py` - 智能提醒系统

### 通用工具 (`skills/utilities/`)
跨项目通用的工具函数
- `logger.py` - 日志记录工具
- `config_loader.py` - 配置文件加载

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 使用示例
```python
# 导入需要的skill
from skills.data_processing.data_cleaner import clean_data

# 使用
result = clean_data(your_data)
```

## 📝 添加新Skill

1. 确定skill所属分类
2. 复制 `templates/skill_template.py` 创建新文件
3. 编写代码和文档字符串
4. 在对应分类的README中添加说明
5. 在本文件中更新索引

## 📚 文档

- [快速开始指南](docs/getting_started.md)
- [命名规范](docs/naming_conventions.md)
- [贡献指南](docs/contributing.md)

## 🔄 更新日志

### 2024-02-07
- 初始化项目结构
- 创建基础模板

## 📄 许可

个人使用

---
最后更新：2024-02-07