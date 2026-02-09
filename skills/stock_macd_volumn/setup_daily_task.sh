#!/bin/bash
# 设置每日数据更新定时任务
#
# 功能：配置cron定时任务，每天21:00自动更新股票数据
#
# 使用方法：
#   chmod +x setup_daily_task.sh
#   ./setup_daily_task.sh

echo "================================================"
echo "设置每日股票数据更新定时任务"
echo "================================================"

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_PATH="$PROJECT_DIR/venv/bin/activate"
PYTHON_SCRIPT="$SCRIPT_DIR/daily_data_updater.py"
LOG_DIR="$SCRIPT_DIR/logs"

echo "项目目录: $PROJECT_DIR"
echo "虚拟环境: $VENV_PATH"
echo "更新脚本: $PYTHON_SCRIPT"
echo "日志目录: $LOG_DIR"
echo ""

# 检查虚拟环境是否存在
if [ ! -f "$VENV_PATH" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "请先创建虚拟环境: python3 -m venv $PROJECT_DIR/venv"
    exit 1
fi

# 检查Python脚本是否存在
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ 错误: 更新脚本不存在: $PYTHON_SCRIPT"
    exit 1
fi

# 创建日志目录
mkdir -p "$LOG_DIR"

# 构造cron任务命令
CRON_CMD="0 21 * * * cd $SCRIPT_DIR && source $VENV_PATH && python $PYTHON_SCRIPT >> $LOG_DIR/daily_update.log 2>&1"

echo "定时任务配置："
echo "  时间: 每天 21:00"
echo "  命令: $CRON_CMD"
echo ""

# 检查是否已存在相同的cron任务
if crontab -l 2>/dev/null | grep -q "daily_data_updater.py"; then
    echo "⚠️  检测到已存在相同的定时任务"
    echo ""
    echo "当前的定时任务："
    crontab -l | grep "daily_data_updater.py"
    echo ""
    read -p "是否替换现有任务? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi

    # 删除旧任务
    crontab -l | grep -v "daily_data_updater.py" | crontab -
    echo "✓ 已删除旧任务"
fi

# 添加新的cron任务
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ 定时任务设置成功!"
echo ""
echo "验证定时任务："
crontab -l | grep "daily_data_updater.py"
echo ""

echo "================================================"
echo "配置完成"
echo "================================================"
echo ""
echo "说明："
echo "  1. 定时任务将在每天21:00自动运行"
echo "  2. 日志保存在: $LOG_DIR/daily_update.log"
echo "  3. 查看所有定时任务: crontab -l"
echo "  4. 编辑定时任务: crontab -e"
echo "  5. 删除此任务: crontab -e 然后删除包含'daily_data_updater.py'的行"
echo ""
echo "测试运行（不等待到21:00）："
echo "  cd $SCRIPT_DIR"
echo "  source $VENV_PATH"
echo "  python daily_data_updater.py --test"
echo ""
echo "手动运行完整更新："
echo "  cd $SCRIPT_DIR"
echo "  source $VENV_PATH"
echo "  python daily_data_updater.py"
echo ""
