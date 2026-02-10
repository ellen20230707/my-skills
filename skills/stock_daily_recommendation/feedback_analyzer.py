"""
反馈分析和自动调优工具

功能：
1. 读取用户提供的反馈CSV文件
2. 分析推荐准确率和最佳推荐时机
3. 识别有效特征和权重
4. 自动调整推荐参数以提高准确性

使用方法：
    python feedback_analyzer.py

反馈文件格式：
    turning_feedback/tuning_feedback_YYYYMMDD.csv
    列1: stock (股票代码)
    列2: Best recommendation buy day (最佳推荐买入日期或"not recommended")

Author: Claude
Date: 2026-02-10
"""

import os
import sys
import glob
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json

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


class FeedbackAnalyzer:
    """反馈分析器"""

    def __init__(self, feedback_dir='turning_feedback', recommendation_dir='recommendations'):
        self.feedback_dir = os.path.join(os.path.dirname(__file__), feedback_dir)
        self.recommendation_dir = os.path.join(os.path.dirname(__file__), recommendation_dir)
        self.tuning_config_path = os.path.join(os.path.dirname(__file__), 'tuning_config.json')

        # 确保目录存在
        os.makedirs(self.feedback_dir, exist_ok=True)

    def get_latest_feedback_file(self) -> Optional[str]:
        """获取最新的反馈文件"""
        pattern = os.path.join(self.feedback_dir, 'tuning_feedback_*.csv')
        feedback_files = glob.glob(pattern)

        if not feedback_files:
            return None

        # 返回最新的文件
        return max(feedback_files, key=os.path.getmtime)

    def read_feedback(self, feedback_file: str) -> pd.DataFrame:
        """读取反馈文件"""
        try:
            df = pd.read_csv(feedback_file, sep='\t')  # 使用tab分隔
            logger.info(f"成功读取反馈文件: {feedback_file}")
            logger.info(f"反馈条目数: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"读取反馈文件失败: {str(e)}")
            return None

    def get_recommendation_file(self, date_str: str) -> Optional[str]:
        """根据日期获取推荐文件"""
        # 尝试CSV格式（新增）
        csv_path = os.path.join(self.recommendation_dir, f'recommendation_{date_str}.csv')
        if os.path.exists(csv_path):
            return csv_path

        # 尝试JSON格式（备选）
        json_path = os.path.join(self.recommendation_dir, f'recommendation_{date_str}.json')
        if os.path.exists(json_path):
            return json_path

        return None

    def analyze_accuracy(self, feedback_df: pd.DataFrame, date_str: str) -> Dict:
        """分析推荐准确率"""
        recommendation_file = self.get_recommendation_file(date_str)

        if not recommendation_file:
            logger.warning(f"未找到{date_str}的推荐文件")
            return None

        # 读取推荐文件
        if recommendation_file.endswith('.csv'):
            rec_df = pd.read_csv(recommendation_file, encoding='utf-8-sig')
            recommended_stocks = set(rec_df['股票代码'].values)
        else:  # JSON
            with open(recommendation_file, 'r', encoding='utf-8') as f:
                rec_data = json.load(f)
            recommended_stocks = set([r['stock_code'] for r in rec_data['recommendations']])

        # 分析准确性
        feedback_df['was_recommended'] = feedback_df['stock'].apply(
            lambda x: x in recommended_stocks
        )

        # 统计
        total_feedback = len(feedback_df)
        should_recommend = feedback_df[feedback_df['Best recommendation buy day'] != 'not recommended']
        should_not_recommend = feedback_df[feedback_df['Best recommendation buy day'] == 'not recommended']

        # 正确推荐的（应该推荐且推荐了）
        true_positives = len(should_recommend[should_recommend['was_recommended']])

        # 错误推荐的（不应该推荐但推荐了）
        false_positives = len(should_not_recommend[should_not_recommend['was_recommended']])

        # 漏掉的（应该推荐但没推荐）
        false_negatives = len(should_recommend[~should_recommend['was_recommended']])

        # 正确不推荐的（不应该推荐且没推荐）
        true_negatives = len(should_not_recommend[~should_not_recommend['was_recommended']])

        # 计算指标
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_positives + true_negatives) / total_feedback

        results = {
            'date': date_str,
            'total_feedback': total_feedback,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'true_negatives': true_negatives,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'accuracy': accuracy,
            'recommended_stocks': list(recommended_stocks),
            'should_recommend_stocks': should_recommend['stock'].tolist(),
            'false_positive_stocks': should_not_recommend[should_not_recommend['was_recommended']]['stock'].tolist(),
            'false_negative_stocks': should_recommend[~should_recommend['was_recommended']]['stock'].tolist()
        }

        return results

    def analyze_timing(self, feedback_df: pd.DataFrame) -> Dict:
        """分析最佳推荐时机"""
        # 过滤出有有效推荐日期的股票
        valid_dates = feedback_df[feedback_df['Best recommendation buy day'] != 'not recommended'].copy()

        if len(valid_dates) == 0:
            return {'message': '无有效推荐日期数据'}

        # 转换日期格式
        valid_dates['best_date'] = pd.to_datetime(valid_dates['Best recommendation buy day'], format='%Y%m%d')

        # 计算距离今天的天数
        today = pd.Timestamp.now()
        valid_dates['days_ago'] = (today - valid_dates['best_date']).dt.days

        # 统计
        timing_stats = {
            'total_valid': len(valid_dates),
            'avg_days_ago': valid_dates['days_ago'].mean(),
            'median_days_ago': valid_dates['days_ago'].median(),
            'min_days_ago': valid_dates['days_ago'].min(),
            'max_days_ago': valid_dates['days_ago'].max(),
            'distribution': valid_dates['days_ago'].value_counts().to_dict()
        }

        # 判断当前SIGNAL_LOOKBACK_DAYS是否合适
        current_lookback = 7  # 默认值
        if os.path.exists(self.tuning_config_path):
            with open(self.tuning_config_path, 'r') as f:
                config = json.load(f)
                current_lookback = config.get('SIGNAL_LOOKBACK_DAYS', 7)

        # 计算有多少百分比的最佳日期在当前lookback范围内
        within_lookback = len(valid_dates[valid_dates['days_ago'] <= current_lookback])
        coverage_rate = within_lookback / len(valid_dates)

        timing_stats['current_lookback'] = current_lookback
        timing_stats['coverage_rate'] = coverage_rate
        timing_stats['stocks_within_lookback'] = within_lookback

        # 建议的lookback天数（覆盖80%的最佳日期）
        sorted_days = valid_dates['days_ago'].sort_values()
        suggested_lookback = int(sorted_days.quantile(0.8))
        timing_stats['suggested_lookback'] = max(suggested_lookback, 3)  # 至少3天

        return timing_stats

    def generate_tuning_recommendations(self, accuracy_results: Dict, timing_stats: Dict) -> Dict:
        """生成调优建议"""
        recommendations = {
            'adjustments': [],
            'reasoning': []
        }

        if not accuracy_results:
            return recommendations

        # 1. 基于准确率调整
        precision = accuracy_results['precision']
        recall = accuracy_results['recall']

        if precision < 0.5:
            recommendations['adjustments'].append({
                'parameter': 'MIN_ENHANCED_SCORE',
                'current': 20,
                'suggested': 25,
                'reason': f'精准度较低({precision:.2%})，提高补充特征分数要求以减少错误推荐'
            })
            recommendations['reasoning'].append(f"精准度仅{precision:.2%}，建议提高筛选标准")

        if recall < 0.5:
            recommendations['adjustments'].append({
                'parameter': 'MIN_ENHANCED_SCORE',
                'current': 20,
                'suggested': 15,
                'reason': f'召回率较低({recall:.2%})，降低补充特征分数要求以捕获更多机会'
            })
            recommendations['reasoning'].append(f"召回率仅{recall:.2%}，建议放宽筛选标准")

        # 2. 基于时机分析调整
        if timing_stats and 'suggested_lookback' in timing_stats:
            current = timing_stats['current_lookback']
            suggested = timing_stats['suggested_lookback']
            coverage = timing_stats['coverage_rate']

            if suggested != current:
                recommendations['adjustments'].append({
                    'parameter': 'SIGNAL_LOOKBACK_DAYS',
                    'current': current,
                    'suggested': suggested,
                    'reason': f'当前覆盖率{coverage:.2%}，调整回溯天数可提高到约80%'
                })
                recommendations['reasoning'].append(
                    f"最佳推荐时机分析显示，回溯{suggested}天可覆盖80%的机会"
                )

        # 3. 基于错误分析调整
        if accuracy_results['false_positives'] > accuracy_results['true_positives']:
            recommendations['adjustments'].append({
                'parameter': 'MIN_RATING',
                'current': 'B',
                'suggested': 'A',
                'reason': '错误推荐过多，建议只推荐A级股票'
            })
            recommendations['reasoning'].append("错误推荐超过正确推荐，建议提高评级要求")

        return recommendations

    def apply_tuning(self, recommendations: Dict) -> bool:
        """应用调优建议"""
        if not recommendations['adjustments']:
            logger.info("无需调整参数")
            return False

        # 读取当前配置
        current_config = {}
        if os.path.exists(self.tuning_config_path):
            with open(self.tuning_config_path, 'r') as f:
                current_config = json.load(f)

        # 应用调整
        for adjustment in recommendations['adjustments']:
            param = adjustment['parameter']
            suggested_value = adjustment['suggested']
            current_config[param] = suggested_value
            logger.info(f"调整 {param}: {adjustment['current']} → {suggested_value}")
            logger.info(f"  原因: {adjustment['reason']}")

        # 保存配置
        current_config['last_updated'] = datetime.now().isoformat()
        current_config['update_count'] = current_config.get('update_count', 0) + 1

        with open(self.tuning_config_path, 'w') as f:
            json.dump(current_config, f, indent=2, ensure_ascii=False)

        logger.info(f"调优配置已保存: {self.tuning_config_path}")
        return True

    def generate_report(self, accuracy_results: Dict, timing_stats: Dict, tuning_recommendations: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 60)
        report.append("反馈分析报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        if accuracy_results:
            report.append("## 推荐准确率分析")
            report.append("")
            report.append(f"分析日期: {accuracy_results['date']}")
            report.append(f"反馈总数: {accuracy_results['total_feedback']}")
            report.append("")
            report.append("### 混淆矩阵")
            report.append(f"  正确推荐 (TP): {accuracy_results['true_positives']}")
            report.append(f"  错误推荐 (FP): {accuracy_results['false_positives']}")
            report.append(f"  漏推荐 (FN): {accuracy_results['false_negatives']}")
            report.append(f"  正确不推荐 (TN): {accuracy_results['true_negatives']}")
            report.append("")
            report.append("### 性能指标")
            report.append(f"  精准度 (Precision): {accuracy_results['precision']:.2%}")
            report.append(f"  召回率 (Recall): {accuracy_results['recall']:.2%}")
            report.append(f"  F1分数: {accuracy_results['f1_score']:.2%}")
            report.append(f"  准确率 (Accuracy): {accuracy_results['accuracy']:.2%}")
            report.append("")

            if accuracy_results['false_positive_stocks']:
                report.append(f"### 错误推荐的股票 ({len(accuracy_results['false_positive_stocks'])}只)")
                for stock in accuracy_results['false_positive_stocks'][:10]:
                    report.append(f"  - {stock}")
                if len(accuracy_results['false_positive_stocks']) > 10:
                    report.append(f"  ... 还有 {len(accuracy_results['false_positive_stocks'])-10} 只")
                report.append("")

            if accuracy_results['false_negative_stocks']:
                report.append(f"### 漏掉的推荐 ({len(accuracy_results['false_negative_stocks'])}只)")
                for stock in accuracy_results['false_negative_stocks'][:10]:
                    report.append(f"  - {stock}")
                if len(accuracy_results['false_negative_stocks']) > 10:
                    report.append(f"  ... 还有 {len(accuracy_results['false_negative_stocks'])-10} 只")
                report.append("")

        if timing_stats and 'total_valid' in timing_stats:
            report.append("## 推荐时机分析")
            report.append("")
            report.append(f"有效推荐数: {timing_stats['total_valid']}")
            report.append(f"平均最佳时机: {timing_stats['avg_days_ago']:.1f}天前")
            report.append(f"中位数最佳时机: {timing_stats['median_days_ago']:.0f}天前")
            report.append(f"最早: {timing_stats['min_days_ago']}天前")
            report.append(f"最晚: {timing_stats['max_days_ago']}天前")
            report.append("")
            report.append(f"当前回溯天数: {timing_stats['current_lookback']}")
            report.append(f"覆盖率: {timing_stats['coverage_rate']:.2%}")
            report.append(f"建议回溯天数: {timing_stats['suggested_lookback']}")
            report.append("")

        if tuning_recommendations['adjustments']:
            report.append("## 调优建议")
            report.append("")
            for adj in tuning_recommendations['adjustments']:
                report.append(f"### {adj['parameter']}")
                report.append(f"  当前值: {adj['current']}")
                report.append(f"  建议值: {adj['suggested']}")
                report.append(f"  原因: {adj['reason']}")
                report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def run_analysis(self, apply_tuning: bool = True) -> Dict:
        """运行完整的分析流程"""
        logger.info("=" * 60)
        logger.info("开始反馈分析")
        logger.info("=" * 60)

        # 1. 获取最新反馈文件
        feedback_file = self.get_latest_feedback_file()
        if not feedback_file:
            logger.warning("未找到反馈文件")
            return {'success': False, 'message': '未找到反馈文件'}

        logger.info(f"使用反馈文件: {feedback_file}")

        # 2. 读取反馈
        feedback_df = self.read_feedback(feedback_file)
        if feedback_df is None:
            return {'success': False, 'message': '读取反馈文件失败'}

        # 3. 提取日期
        filename = os.path.basename(feedback_file)
        date_str = filename.replace('tuning_feedback_', '').replace('.csv', '')

        # 4. 分析准确率
        logger.info("分析推荐准确率...")
        accuracy_results = self.analyze_accuracy(feedback_df, date_str)

        # 5. 分析时机
        logger.info("分析推荐时机...")
        timing_stats = self.analyze_timing(feedback_df)

        # 6. 生成调优建议
        logger.info("生成调优建议...")
        tuning_recommendations = self.generate_tuning_recommendations(accuracy_results, timing_stats)

        # 7. 生成报告
        report = self.generate_report(accuracy_results, timing_stats, tuning_recommendations)
        print("\n" + report)

        # 保存报告
        report_path = os.path.join(log_dir, f'feedback_analysis_{date_str}.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"分析报告已保存: {report_path}")

        # 8. 应用调优（如果启用）
        if apply_tuning and tuning_recommendations['adjustments']:
            logger.info("应用调优...")
            self.apply_tuning(tuning_recommendations)

        logger.info("=" * 60)
        logger.info("反馈分析完成")
        logger.info("=" * 60)

        return {
            'success': True,
            'accuracy_results': accuracy_results,
            'timing_stats': timing_stats,
            'tuning_recommendations': tuning_recommendations,
            'report_path': report_path
        }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='反馈分析和自动调优工具')
    parser.add_argument('--no-apply', action='store_true', help='不自动应用调优建议')

    args = parser.parse_args()

    analyzer = FeedbackAnalyzer()
    result = analyzer.run_analysis(apply_tuning=not args.no_apply)

    return 0 if result['success'] else 1


if __name__ == "__main__":
    exit(main())
