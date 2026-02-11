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
import numpy as np
from datetime import datetime
from enhanced_feedback_analyzer import EnhancedFeedbackAnalyzer

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
    logger.info("📊 增强版反馈分析工具")
    logger.info("=" * 80)
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # 1. 创建增强版分析器
    try:
        analyzer = EnhancedFeedbackAnalyzer(learning_rate=0.15)
    except FileNotFoundError as e:
        logger.error(f"❌ 初始化分析器失败: {str(e)}")
        logger.info("请确保数据目录存在")
        return False

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

    # 6. 【新增】逐支股票Gap分析
    logger.info("🔍 进行逐支股票Gap分析...")
    gap_analysis = analyzer.analyze_stock_gaps(feedback_df, date_str)

    if 'error' in gap_analysis:
        logger.warning(f"⚠️  Gap分析失败: {gap_analysis.get('message', '未知错误')}")
        logger.info("将使用基础调优策略")
        logger.info("")
        gap_analysis = None
    else:
        logger.info("=" * 80)
        logger.info("📋 Gap分析结果")
        logger.info("=" * 80)
        logger.info(f"正确推荐 (TP): {len(gap_analysis['true_positives'])}")
        logger.info(f"错误推荐 (FP): {len(gap_analysis['false_positives'])}")
        logger.info(f"遗漏推荐 (FN): {len(gap_analysis['false_negatives'])}")
        logger.info("")

        # 展示典型错误案例（前3个）
        if gap_analysis['false_positives']:
            logger.info("❌ 典型错误推荐案例:")
            for i, case in enumerate(gap_analysis['false_positives'][:3], 1):
                logger.info(f"  {i}. {case['stock_code']}")
                logger.info(f"     特征: MACD={case['features']['macd_score']:.0f}, "
                          f"成交量={case['features']['volume_ratio']:.2f}, "
                          f"补充分={case['features']['enhanced_score']:.0f}")
                logger.info(f"     诊断: {case['diagnosis']}")
            if len(gap_analysis['false_positives']) > 3:
                logger.info(f"  ... 共{len(gap_analysis['false_positives'])}个错误推荐")
            logger.info("")

        if gap_analysis['false_negatives']:
            logger.info("⚠️  典型遗漏推荐案例:")
            for i, case in enumerate(gap_analysis['false_negatives'][:3], 1):
                logger.info(f"  {i}. {case['stock_code']} (最佳买入日: {case['best_date']})")
                logger.info(f"     特征: MACD={case['features']['macd_score']:.0f}, "
                          f"成交量={case['features']['volume_ratio']:.2f}, "
                          f"补充分={case['features']['enhanced_score']:.0f}")
                logger.info(f"     原因: {case['reason']}")
            if len(gap_analysis['false_negatives']) > 3:
                logger.info(f"  ... 共{len(gap_analysis['false_negatives'])}个遗漏推荐")
            logger.info("")

        if gap_analysis['true_positives']:
            logger.info("✅ 成功推荐案例特征分布:")
            tp_features = [case['features'] for case in gap_analysis['true_positives']]
            macd_scores = [f['macd_score'] for f in tp_features]
            volumes = [f['volume_ratio'] for f in tp_features]
            logger.info(f"  MACD评分: 均值={np.mean(macd_scores):.1f}, 中位数={np.median(macd_scores):.1f}")
            logger.info(f"  成交量比率: 均值={np.mean(volumes):.2f}, 中位数={np.median(volumes):.2f}")
            logger.info("")

        logger.info("=" * 80)
        logger.info("")

    # 7. 【新增】特征模式分析
    if gap_analysis:
        logger.info("📊 分析特征模式...")
        pattern_analysis = analyzer.analyze_feature_patterns(gap_analysis)

        logger.info("=" * 80)
        logger.info("🎯 特征模式分析结果")
        logger.info("=" * 80)

        # 展示阈值分析
        threshold_analysis = pattern_analysis.get('threshold_analysis', {})
        for param, analysis in threshold_analysis.items():
            logger.info(f"📌 {param}")
            logger.info(f"   当前阈值: {analysis['current']}")
            logger.info(f"   建议阈值: {analysis['suggested']}")
            logger.info(f"   分析结果: {analysis['reason']}")
            logger.info("")

        logger.info("=" * 80)
        logger.info("")

        # 8. 【新增】生成自适应调优建议
        logger.info("🔧 生成自适应调优建议...")
        tuning_recommendations = analyzer.generate_adaptive_tuning(pattern_analysis)

        logger.info("=" * 80)
        logger.info("💡 自适应调优建议")
        logger.info("=" * 80)
        if tuning_recommendations['adjustments']:
            for adj in tuning_recommendations['adjustments']:
                logger.info(f"📌 {adj['parameter']}")
                logger.info(f"   当前值: {adj['current']}")
                logger.info(f"   建议值: {adj['suggested']}")
                logger.info(f"   实际调整: {adj['actual_adjustment']} (学习率: {analyzer.learning_rate})")
                logger.info(f"   调整幅度: {adj['delta']:+.2f}")
                logger.info(f"   原因: {adj['reason']}")
                logger.info(f"   预期影响: {adj['expected_impact']}")
                logger.info(f"   置信度: {adj['confidence']:.0%}")
                logger.info("")
        else:
            logger.info("当前参数表现良好，无需调整")
        logger.info("=" * 80)
        logger.info("")

    else:
        # 如果Gap分析失败，回退到基础调优
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

        logger.info("🔧 生成基础调优建议...")
        tuning_recommendations = analyzer.generate_tuning_recommendations(accuracy, timing)

        logger.info("=" * 80)
        logger.info("💡 基础调优建议")
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

    # 9. 应用调优
    if tuning_recommendations['adjustments']:
        logger.info("✅ 应用调优参数...")

        # 读取现有调优配置（如果存在）
        tuning_config = {}
        if os.path.exists(analyzer.tuning_config_path):
            try:
                with open(analyzer.tuning_config_path, 'r', encoding='utf-8') as f:
                    tuning_config = json.load(f)
                logger.debug(f"读取现有调优配置: {tuning_config}")
            except:
                pass

        # 更新调优参数（只修改有变化的）
        for adj in tuning_recommendations['adjustments']:
            param_name = adj['parameter']
            # 使用实际调整值（如果是自适应调优）或建议值（如果是基础调优）
            param_value = adj.get('actual_adjustment', adj['suggested'])
            tuning_config[param_name] = param_value

        # 保存配置
        with open(analyzer.tuning_config_path, 'w', encoding='utf-8') as f:
            json.dump(tuning_config, f, indent=2, ensure_ascii=False)

        logger.info(f"调优配置已保存至: {os.path.basename(analyzer.tuning_config_path)}")
        logger.info("")
    else:
        logger.info("无需生成调优配置")
        logger.info("")

    # 10. 【新增】追踪改进历史
    if gap_analysis:
        logger.info("📈 记录改进历史...")
        analyzer.track_improvement(accuracy, tuning_recommendations['adjustments'], gap_analysis, date_str)

        # 展示改进总结
        improvement_summary = analyzer.get_improvement_summary()
        if improvement_summary:
            logger.info("=" * 80)
            logger.info("📊 改进总结")
            logger.info("=" * 80)
            logger.info(f"总调优次数: {improvement_summary['total_tunings']}")
            logger.info(f"首次分析: {improvement_summary['first_date']}")
            logger.info(f"最新分析: {improvement_summary['latest_date']}")
            logger.info("")
            logger.info("总体改进:")
            for metric, change in improvement_summary['overall_improvement'].items():
                logger.info(f"  {metric}: {change}")
            logger.info("")
            logger.info(f"最佳F1分数: {improvement_summary['best_f1_score']:.2%} (日期: {improvement_summary['best_f1_date']})")
            logger.info("=" * 80)
            logger.info("")

    # 11. 提示下次运行
    logger.info("=" * 80)
    logger.info("🎉 增强版反馈分析完成！")
    logger.info("=" * 80)
    logger.info("📝 下次运行推荐工具时将自动使用新的参数配置")
    logger.info("📊 调优配置文件: tuning_config.json")
    if gap_analysis:
        logger.info("📈 改进历史文件: tuning_history.json")
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
