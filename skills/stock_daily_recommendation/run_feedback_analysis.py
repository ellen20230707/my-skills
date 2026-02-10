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
import json
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


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("📊 反馈分析工具")
    logger.info("=" * 80)
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # 1. 创建分析器
    analyzer = FeedbackAnalyzer()

    # 2. 查找反馈文件
    feedback_file = analyzer.get_latest_feedback_file()
    if not feedback_file:
        logger.error("❌ 未找到反馈文件")
        logger.info("请确保反馈文件位于 turning_feedback/ 目录")
        logger.info("文件名格式: tuning_feedback_YYYYMMDD.csv")
        return False

    logger.info(f"✅ 找到反馈文件: {os.path.basename(feedback_file)}")

    # 3. 读取反馈
    logger.info("📖 读取反馈数据...")
    feedback_df = analyzer.read_feedback(feedback_file)
    if feedback_df is None:
        logger.error("❌ 读取反馈文件失败")
        return False

    logger.info(f"   总反馈数: {len(feedback_df)}")
    should_recommend = feedback_df[feedback_df['Best recommendation buy day'] != 'not recommended']
    should_not_recommend = feedback_df[feedback_df['Best recommendation buy day'] == 'not recommended']
    logger.info(f"   推荐买入: {len(should_recommend)}")
    logger.info(f"   不应推荐: {len(should_not_recommend)}")
    logger.info("")

    # 4. 从反馈文件名提取日期
    feedback_filename = os.path.basename(feedback_file)
    date_str = feedback_filename.replace('tuning_feedback_', '').replace('.csv', '')
    logger.info(f"反馈日期: {date_str}")

    # 5. 分析准确性
    logger.info("🎯 分析推荐准确性...")
    accuracy = analyzer.analyze_accuracy(feedback_df, date_str)

    if accuracy is None:
        logger.warning("⚠️  未找到推荐CSV文件")
        logger.info("这是正常情况 - 首次运行或还未生成推荐报告")
        logger.info("反馈分析将在下次生成推荐报告后自动运行")
        logger.info("")
        logger.info("提示：推荐工具会在每天22:00自动生成CSV格式报告")
        logger.info("=" * 80)
        return True  # 正常退出，不报错

    logger.info("=" * 80)
    logger.info("📊 准确性统计")
    logger.info("=" * 80)
    logger.info(f"真阳性 (正确推荐):    {accuracy['true_positives']}")
    logger.info(f"假阳性 (错误推荐):    {accuracy['false_positives']}")
    logger.info(f"假阴性 (遗漏推荐):    {accuracy['false_negatives']}")
    logger.info(f"真阴性 (正确不推荐):  {accuracy['true_negatives']}")
    logger.info("")
    logger.info(f"精确率 (Precision): {accuracy['precision']:.2%}")
    logger.info(f"召回率 (Recall):    {accuracy['recall']:.2%}")
    logger.info(f"F1分数:             {accuracy['f1_score']:.2%}")
    logger.info(f"准确率 (Accuracy):  {accuracy['accuracy']:.2%}")
    logger.info("=" * 80)
    logger.info("")

    # 6. 分析时机
    logger.info("⏰ 分析推荐时机...")
    timing = analyzer.analyze_timing(feedback_df)

    logger.info("=" * 80)
    logger.info("📅 推荐时机分析")
    logger.info("=" * 80)
    if 'message' in timing:
        logger.info(timing['message'])
    else:
        logger.info(f"有效反馈数: {timing['total_valid']}")
        logger.info(f"平均距离天数: {timing['avg_days_ago']:.1f} 天")
        logger.info(f"当前回溯天数: {timing['current_lookback']} 天")
        logger.info(f"覆盖率: {timing['coverage_rate']:.2%}")
        logger.info(f"建议回溯天数: {timing['suggested_lookback']} 天")
    logger.info("=" * 80)
    logger.info("")

    # 7. 生成调优建议
    logger.info("🔧 生成调优建议...")
    tuning_recommendations = analyzer.generate_tuning_recommendations(accuracy, timing)

    logger.info("=" * 80)
    logger.info("💡 调优建议")
    logger.info("=" * 80)
    if tuning_recommendations['adjustments']:
        for adj in tuning_recommendations['adjustments']:
            logger.info(f"📌 {adj['parameter']}")
            logger.info(f"   当前值: {adj['current']}")
            logger.info(f"   建议值: {adj['suggested']}")
            logger.info(f"   原因: {adj['reason']}")
            logger.info("")
    else:
        logger.info("当前参数表现良好，无需调整")
    logger.info("=" * 80)
    logger.info("")

    # 8. 应用调优
    if tuning_recommendations['adjustments']:
        logger.info("✅ 应用调优参数...")
        # 生成调优配置
        tuning_config = {}
        for adj in tuning_recommendations['adjustments']:
            tuning_config[adj['parameter']] = adj['suggested']

        # 保存配置
        with open(analyzer.tuning_config_path, 'w') as f:
            json.dump(tuning_config, f, indent=2, ensure_ascii=False)

        logger.info(f"调优配置已保存至: {os.path.basename(analyzer.tuning_config_path)}")
        logger.info("")
    else:
        logger.info("无需生成调优配置")
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
