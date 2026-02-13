# GitHub Actions 推送冲突修复说明

## 问题描述

工作流在推送数据更新时失败，错误信息：
```
error: failed to push some refs to 'https://github.com/ellen20230707/my-skills'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally.
```

## 问题原因

1. **并发提交冲突**：当多个工作流同时运行或有手动提交时，远程仓库可能包含本地没有的更改
2. **缺少同步机制**：原工作流直接 `git push`，没有先拉取远程更改

## 修复方案

### 1. 推送前拉取远程更改
```yaml
# 先拉取远程更改（使用rebase避免合并提交）
git pull --rebase origin main
```

### 2. 冲突处理策略
如果拉取时出现冲突（主要是数据文件冲突），使用本地版本：
```yaml
git checkout --ours A股近10年日线数据/*.csv
git add A股近10年日线数据/*.csv
git rebase --continue
```

### 3. 推送重试机制
添加最多3次重试，每次重试前重新同步：
```yaml
for i in {1..3}; do
  if git push origin main; then
    echo "✅ 推送成功"
    break
  else
    echo "⚠️ 推送失败，第 $i 次重试..."
    sleep 2
    git pull --rebase origin main || true
  fi
done
```

## 修复效果

✅ **推送前自动同步**：避免"rejected"错误
✅ **智能冲突处理**：数据文件冲突时优先使用最新数据
✅ **重试机制**：提高成功率，应对瞬时网络问题
✅ **保持提交历史整洁**：使用rebase而非merge

## 测试建议

1. **手动触发测试**：
   - 在GitHub仓库页面点击 "Actions"
   - 选择 "每日股票数据更新" 工作流
   - 点击 "Run workflow"
   - 查看执行日志确认是否成功

2. **模拟冲突场景**：
   - 手动修改远程仓库的某个CSV文件
   - 立即触发工作流
   - 观察工作流是否能正确处理冲突并推送

## 注意事项

- 数据文件冲突时始终使用本地（最新下载）的版本
- 如果连续3次推送失败，工作流会报错，需要人工介入
- 建议避免在工作流运行期间手动推送数据文件

## 相关文件

- 工作流文件：`.github/workflows/daily-data-update.yml`
- 数据更新脚本：`skills/stock_macd_volumn/daily_data_updater.py`
- 数据目录：`A股近10年日线数据/`

## 更新日期

2026-02-12
