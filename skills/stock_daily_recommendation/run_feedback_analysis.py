"""
反馈分析运行脚本

功能：
1. 读取用户提供的反馈CSV文件
2. 分析推荐准确性
3. 生成调优建议
4. 自动应用参数调整

使用方法：
    python run_feedback_analysis.py

要求：
- 反馈文件需在 18:00 前提交到 turning_feedback/ 目录
- 文件名格式: tuning_feedback_YYYYMMDD.csv
- 格式: stock\tBest recommendation buy day

Author: Claude
Date: 2026-02-10
"""

import os
import sys
import glob
import logging
from datetime import datetime
from feedback_analyzer import FeedbackAnalyzer

# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'feedback_analysis.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def find_latest_feedback():
    """查找最新的反馈文件"""
    feedback_dir = os.path.join(os.path.dirname(__file__), 'turning_feedback')
    pattern = os.path.join(feedback_dir, 'tuning_feedback_*.csv')
    files = glob.glob(pattern)

    if not files:
        return None

    # 按修改时间排序，返回最新的
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def find_latest_recommendation():
    """查找最新的推荐CSV文件"""
    rec_dir = os.path.join(os.path.dirname(__file__), 'recommendations')
    pattern = os.path.join(rec_dir, 'recommendation_*.csv')
    files = glob.glob(pattern)

    if not files:
        return None

    # 按修改时间排序，返回最新的
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("📊 反馈分析工具")
    logger.info("=" * 80)
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # 1. 查找反馈文件
    feedback_file = find_latest_feedback()
    if not feedback_file:
        logger.error("❌ 未找到反馈文件")
        logger.info("请确保反馈文件位于 turning_feedback/ 目录")
        logger.info("文件名格式: tuning_feedback_YYYYMMDD.csv")
        return False

    logger.info(f"✅ 找到反馈文件: {os.path.basename(feedback_file)}")

    # 2. 查找推荐文件
    rec_file = find_latest_recommendation()
    if not rec_file:
        logger.error("❌ 未找到推荐CSV文件")
        logger.info("请确保已生成推荐报告（recommendation_YYYYMMDD.csv）")
        return False

    logger.info(f"✅ 找到推荐文件: {os.path.basename(rec_file)}")
    logger.info("")

    # 3. 创建分析器
    analyzer = FeedbackAnalyzer(
        feedback_file=feedback_file,
        recommendation_file=rec_file
    )

    # 4. 读取反馈
    logger.info("📖 读取反馈数据...")
    feedback_data = analyzer.read_feedback()
    logger.info(f"   总反馈数: {feedback_data['total']}")
    logger.info(f"   推荐买入: {feedback_data['should_recommend']}")
    logger.info(f"   不应推荐: {feedback_data['should_not_recommend']}")
    logger.info("")

    # 5. 分析准确性
    logger.info("🎯 分析推荐准确性...")
    accuracy = analyzer.analyze_accuracy()

    logger.info("=" * 80)
    logger.info("📊 准确性统计")
    logger.info("=" * 80)
    logger.info(f"真阳性 (正确推荐):    {accuracy['confusion_matrix']['true_positive']}")
    logger.info(f"假阳性 (错误推荐):    {accuracy['confusion_matrix']['false_positive']}")
    logger.info(f"假阴性 (遗漏推荐):    {accuracy['confusion_matrix']['false_negative']}")
    logger.info(f"真阴性 (正确不推荐):  {accuracy['confusion_matrix']['true_negative']}")
    logger.info("")
    logger.info(f"精确率 (Precision): {accuracy['precision']:.2%}")
    logger.info(f"召回率 (Recall):    {accuracy['recall']:.2%}")
    logger.info(f"F1分数:             {accuracy['f1_score']:.2%}")
    logger.info("=" * 80)
    logger.info("")

    # 6. 分析时机
    logger.info("⏰ 分析推荐时机...")
    timing = analyzer.analyze_timing()

    logger.info("=" * 80)
    logger.info("📅 推荐时机分析")
    logger.info("=" * 80)
    logger.info(f"平均提前天数: {timing['avg_days_early']:.1f} 天")
    logger.info(f"最佳回溯天数: {timing['optimal_lookback_days']} 天")
    logger.info("")
    logger.info("天数分布:")
    for days, count in sorted(timing['days_distribution'].items()):
        logger.info(f"  提前 {days} 天: {count} 次")
    logger.info("=" * 80)
    logger.info("")

    # 7. 生成调优建议
    logger.info("🔧 生成调优建议...")
    recommendations = analyzer.generate_tuning_recommendations()

    logger.info("=" * 80)
    logger.info("💡 调优建议")
    logger.info("=" * 80)
    for rec in recommendations:
        logger.info(f"📌 {rec['parameter']}")
        logger.info(f"   当前值: {rec['current_value']}")
        logger.info(f"   建议值: {rec['recommended_value']}")
        logger.info(f"   原因: {rec['reason']}")
        logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # 8. 应用调优
    logger.info("✅ 应用调优参数...")
    tuning_path = analyzer.apply_tuning()
    logger.info(f"调优配置已保存至: {os.path.basename(tuning_path)}")
    logger.info("")

    # 9. 提示下次运行
    logger.info("=" * 80)
    logger.info("🎉 反馈分析完成！")
    logger.info("=" * 80)
    logger.info("📝 下次运行推荐工具时将自动使用新的参数配置")
    logger.info("📊 调优配置文件: tuning_config.json")
    logger.info("🔄 如需恢复默认配置，删除 tuning_config.json 即可")
    logger.info("=" * 80)

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ 执行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
