"""
增强版反馈分析器
实现逐支股票的Gap分析、特征反推、自适应调优和改进追踪

功能：
1. 股票特征反推 - 从反馈数据加载历史数据，计算技术指标
2. 逐支股票Gap分析 - 诊断每支股票的错误原因
3. 特征模式分析 - 统计成功/失败案例的特征分布
4. 自适应阈值调整 - 应用学习率做小幅调整
5. 改进历史追踪 - 记录每日指标和调优决策

Author: Claude
Date: 2026-02-10
"""

import os
import sys
import glob
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

# 添加 stock_macd_volumn 到路径以导入配置和技术指标计算函数
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stock_macd_volumn'))

from config import Config
from technical_indicators import calculate_all_indicators
from signal_detector import calculate_macd_score

# 导入基础类
from feedback_analyzer import FeedbackAnalyzer

logger = logging.getLogger(__name__)


class EnhancedFeedbackAnalyzer(FeedbackAnalyzer):
    """
    增强版反馈分析器
    在基础反馈分析的基础上，增加了逐支股票的Gap分析和自适应调优
    """

    def __init__(self, data_dir=None, learning_rate=0.15,
                 feedback_dir='turning_feedback',
                 recommendation_dir='recommendations'):
        """
        初始化增强版反馈分析器

        Args:
            data_dir: A股近10年日线数据目录，默认使用仓库根目录下的"A股近10年日线数据"
            learning_rate: 学习率，默认0.15（保守调整）
            feedback_dir: 反馈文件目录
            recommendation_dir: 推荐报告目录
        """
        super().__init__(feedback_dir, recommendation_dir)

        # 数据目录 - 相对于仓库根目录
        if data_dir is None:
            # 计算仓库根目录（从当前文件位置向上2层）
            current_dir = os.path.dirname(os.path.abspath(__file__))  # stock_daily_recommendation/
            skills_dir = os.path.dirname(current_dir)  # skills/
            repo_root = os.path.dirname(skills_dir)  # repo root
            self.data_dir = os.path.join(repo_root, "A股近10年日线数据")
        else:
            self.data_dir = data_dir

        if not os.path.exists(self.data_dir):
            raise FileNotFoundError(f"数据目录不存在: {self.data_dir}")

        # 学习率
        self.learning_rate = learning_rate

        # 历史追踪文件
        self.history_path = os.path.join(
            os.path.dirname(__file__),
            'tuning_history.json'
        )

        logger.info(f"增强版反馈分析器已初始化")
        logger.info(f"  数据目录: {self.data_dir}")
        logger.info(f"  学习率: {self.learning_rate}")

    # ========== 模块1：股票特征反推 ==========

    def load_stock_data(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        加载股票历史数据并计算所有技术指标

        Args:
            stock_code: 股票代码，如 '600000' 或 'sh.600000'

        Returns:
            包含所有技术指标的DataFrame，如果文件不存在则返回None
        """
        # 提取纯数字代码
        code = stock_code.split('.')[-1] if '.' in stock_code else stock_code

        # 查找股票文件（支持 sh.XXXXXX*.csv 和 sz.XXXXXX*.csv）
        pattern = os.path.join(self.data_dir, f"*.{code}*.csv")
        files = glob.glob(pattern)

        if not files:
            logger.warning(f"未找到股票数据: {stock_code} (pattern: {pattern})")
            return None

        # 读取第一个匹配的文件
        file_path = files[0]
        logger.debug(f"加载股票数据: {os.path.basename(file_path)}")

        try:
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])

            # 计算所有技术指标（复用现有函数）
            df = calculate_all_indicators(df, Config)

            return df
        except Exception as e:
            logger.error(f"加载股票数据失败 {stock_code}: {str(e)}")
            return None

    def calculate_features_for_date(self, stock_code: str, target_date: str) -> Optional[Dict]:
        """
        计算指定日期的技术指标特征

        Args:
            stock_code: 股票代码
            target_date: 目标日期，格式 'YYYYMMDD'

        Returns:
            特征字典，包含 macd_score, volume_ratio, ma60_distance 等
        """
        df = self.load_stock_data(stock_code)
        if df is None or len(df) == 0:
            return None

        try:
            # 转换日期格式
            target_date_obj = pd.to_datetime(target_date, format='%Y%m%d')

            # 查找最接近的交易日（考虑停牌、节假日）
            df['date_diff'] = abs((df['date'] - target_date_obj).dt.days)
            closest_idx = df['date_diff'].idxmin()
            row = df.loc[closest_idx]

            # 检查日期差异（如果超过7天则警告）
            if row['date_diff'] > 7:
                logger.warning(f"股票 {stock_code} 在 {target_date} 附近无交易数据，最近交易日为 {row['date'].strftime('%Y-%m-%d')}")

            # 计算MACD评分（需要历史数据）
            macd_score = calculate_macd_score(df, closest_idx, Config) if closest_idx >= 26 else 0

            # 提取特征
            features = {
                'date': row['date'].strftime('%Y-%m-%d'),
                'actual_date': target_date,
                'date_diff_days': int(row['date_diff']),
                'close': float(row['close']) if pd.notna(row['close']) else 0,
                'macd_score': macd_score,
                'volume_ratio': float(row.get('volume_ratio', 0)) if pd.notna(row.get('volume_ratio')) else 0,
                'ma60_distance': float(row.get('ma60_distance', 100)) if pd.notna(row.get('ma60_distance')) else 100,
                'rsi': float(row.get('rsi', 50)) if pd.notna(row.get('rsi')) else 50,
                'enhanced_score': float(row.get('enhanced_score', 0)) if pd.notna(row.get('enhanced_score')) else 0,
            }

            # 计算评级
            enhanced_score = features['enhanced_score']
            if enhanced_score >= 30:
                features['rating'] = 'A'
            elif enhanced_score >= 20:
                features['rating'] = 'B'
            else:
                features['rating'] = 'C'

            return features

        except Exception as e:
            logger.error(f"计算特征失败 {stock_code} @ {target_date}: {str(e)}")
            return None

    # ========== 模块2：Gap分析 ==========

    def _diagnose_false_positive(self, features: Dict) -> str:
        """
        诊断错误推荐（False Positive）的原因

        Args:
            features: 股票技术指标特征

        Returns:
            诊断结果字符串
        """
        issues = []

        # MACD评分刚过阈值
        macd_score = features.get('macd_score', 0)
        if 50 <= macd_score <= 60:
            issues.append(f'MACD评分{macd_score:.0f}刚过阈值(50-60)，可能是临界噪音')

        # 成交量比率刚过阈值
        volume_ratio = features.get('volume_ratio', 0)
        if 2.0 <= volume_ratio <= 2.5:
            issues.append(f'成交量比率{volume_ratio:.2f}刚过阈值(2.0-2.5)，放量不够明显')

        # 补充特征分偏低
        enhanced_score = features.get('enhanced_score', 0)
        if enhanced_score < 25:
            issues.append(f'补充特征分{enhanced_score:.0f}偏低，质量不高')

        # MA60距离较大
        ma60_distance = features.get('ma60_distance', 100)
        if ma60_distance > 0.3:
            issues.append(f'MA60距离{ma60_distance:.1f}%较大，可能涨幅过大')

        return '; '.join(issues) if issues else '指标看似合格但实际表现不佳'

    def _diagnose_false_negative(self, features: Dict) -> str:
        """
        诊断遗漏推荐（False Negative）的原因

        Args:
            features: 股票技术指标特征

        Returns:
            诊断结果字符串
        """
        blocked = []

        # MACD评分不足
        macd_score = features.get('macd_score', 0)
        if macd_score < 50:
            blocked.append(f'MACD评分{macd_score:.0f}<50')

        # 成交量比率不足
        volume_ratio = features.get('volume_ratio', 0)
        if volume_ratio < 2.0:
            blocked.append(f'成交量比率{volume_ratio:.2f}<2.0')

        # MA60距离超标
        ma60_distance = features.get('ma60_distance', 100)
        if ma60_distance > 0.5:
            blocked.append(f'MA60距离{ma60_distance:.1f}%>0.5%')

        # 补充特征分不足
        enhanced_score = features.get('enhanced_score', 0)
        if enhanced_score < 25:
            blocked.append(f'补充特征分{enhanced_score:.0f}<25')

        return '被阻塞：' + '; '.join(blocked) if blocked else '未知原因'

    def _diagnose_success(self, features: Dict, is_tp: bool) -> str:
        """
        诊断成功案例（True Positive 或 True Negative）的特征

        Args:
            features: 股票技术指标特征
            is_tp: True表示TP（正确推荐），False表示TN（正确不推荐）

        Returns:
            诊断结果字符串
        """
        if is_tp:
            # 正确推荐的特征
            strengths = []
            macd_score = features.get('macd_score', 0)
            volume_ratio = features.get('volume_ratio', 0)
            enhanced_score = features.get('enhanced_score', 0)

            if macd_score >= 70:
                strengths.append(f'MACD评分{macd_score:.0f}优秀')
            if volume_ratio >= 2.5:
                strengths.append(f'成交量比率{volume_ratio:.2f}放量明显')
            if enhanced_score >= 30:
                strengths.append(f'补充特征分{enhanced_score:.0f}A级')

            return '; '.join(strengths) if strengths else '各项指标均衡良好'
        else:
            # 正确不推荐的原因
            return '指标未达到推荐标准，正确过滤'

    def analyze_stock_gaps(self, feedback_df: pd.DataFrame, date_str: str) -> Dict:
        """
        逐支股票分析推荐与反馈之间的Gap

        Args:
            feedback_df: 反馈数据DataFrame
            date_str: 反馈日期字符串 (YYYYMMDD)

        Returns:
            Gap分析结果字典，包含TP/FP/FN/TN的详细案例
        """
        logger.info("开始逐支股票Gap分析...")

        # 读取当日推荐CSV（用于判断TP/FP）
        recommendation_csv = self._find_recommendation_csv(date_str)
        recommended_stocks = set()

        if recommendation_csv and os.path.exists(recommendation_csv):
            try:
                rec_df = pd.read_csv(recommendation_csv)
                recommended_stocks = set(rec_df['股票代码'].values)
                logger.info(f"找到推荐CSV: {len(recommended_stocks)}支股票")
            except Exception as e:
                logger.warning(f"读取推荐CSV失败: {str(e)}")
        else:
            logger.warning("未找到推荐CSV文件，无法进行完整Gap分析")
            return {
                'error': 'no_recommendation_csv',
                'message': '未找到推荐CSV文件，请先生成推荐报告'
            }

        # 分类股票
        gap_analysis = {
            'false_positives': [],   # 错误推荐
            'false_negatives': [],   # 遗漏推荐
            'true_positives': [],    # 正确推荐
            'true_negatives': []     # 正确不推荐（暂不分析）
        }

        # 分析每支反馈股票
        for _, row in feedback_df.iterrows():
            stock_code = row['stock']
            best_date = row['Best recommendation buy day']

            # 跳过"不应推荐"的股票（用于分析TN，但数据量太大，暂不全量分析）
            if best_date == 'not recommended':
                # 如果被推荐了，则是FP
                if stock_code in recommended_stocks:
                    features = self.calculate_features_for_date(stock_code, date_str)
                    if features:
                        gap_analysis['false_positives'].append({
                            'stock_code': stock_code,
                            'features': features,
                            'diagnosis': self._diagnose_false_positive(features)
                        })
                # 否则是TN（正确不推荐，暂不记录）
                continue

            # 计算该股票在最佳买入日的特征
            features = self.calculate_features_for_date(stock_code, best_date)

            if features is None:
                logger.warning(f"无法计算特征: {stock_code} @ {best_date}")
                continue

            # 判断是否被推荐
            was_recommended = stock_code in recommended_stocks

            if was_recommended:
                # True Positive - 正确推荐
                gap_analysis['true_positives'].append({
                    'stock_code': stock_code,
                    'best_date': best_date,
                    'features': features,
                    'diagnosis': self._diagnose_success(features, is_tp=True)
                })
            else:
                # False Negative - 遗漏推荐
                gap_analysis['false_negatives'].append({
                    'stock_code': stock_code,
                    'best_date': best_date,
                    'features': features,
                    'reason': self._diagnose_false_negative(features)
                })

        # 统计结果
        logger.info(f"Gap分析完成:")
        logger.info(f"  正确推荐 (TP): {len(gap_analysis['true_positives'])}")
        logger.info(f"  错误推荐 (FP): {len(gap_analysis['false_positives'])}")
        logger.info(f"  遗漏推荐 (FN): {len(gap_analysis['false_negatives'])}")

        return gap_analysis

    def _find_recommendation_csv(self, date_str: str) -> Optional[str]:
        """查找推荐CSV文件"""
        csv_pattern = os.path.join(
            os.path.dirname(__file__),
            self.recommendation_dir,
            f'recommendation_{date_str}.csv'
        )
        return csv_pattern if os.path.exists(csv_pattern) else None

    # ========== 模块3：特征模式分析 ==========

    def analyze_feature_patterns(self, gap_analysis: Dict) -> Dict:
        """
        分析成功/失败案例的特征分布模式

        Args:
            gap_analysis: Gap分析结果

        Returns:
            特征模式分析结果，包含统计信息和阈值建议
        """
        logger.info("开始特征模式分析...")

        if 'error' in gap_analysis:
            return {'error': gap_analysis['error']}

        # 提取各类别的特征
        tp_features = [case['features'] for case in gap_analysis['true_positives']]
        fp_features = [case['features'] for case in gap_analysis['false_positives']]
        fn_features = [case['features'] for case in gap_analysis['false_negatives']]

        # 统计函数
        def calc_stats(features_list: List[Dict], key: str) -> Dict:
            """计算特征统计值"""
            values = [f.get(key, 0) for f in features_list if f.get(key) is not None]
            if not values:
                return {'count': 0}
            return {
                'count': len(values),
                'mean': np.mean(values),
                'median': np.median(values),
                'min': np.min(values),
                'max': np.max(values),
                'p25': np.percentile(values, 25),
                'p75': np.percentile(values, 75),
                'p90': np.percentile(values, 90)
            }

        # 统计各类别的特征分布
        feature_keys = ['macd_score', 'volume_ratio', 'ma60_distance', 'enhanced_score']

        pattern_analysis = {
            'true_positive_stats': {key: calc_stats(tp_features, key) for key in feature_keys},
            'false_positive_stats': {key: calc_stats(fp_features, key) for key in feature_keys},
            'false_negative_stats': {key: calc_stats(fn_features, key) for key in feature_keys},
            'threshold_analysis': {}
        }

        # 阈值分析
        threshold_analysis = {}

        # 1. MACD_SCORE_THRESHOLD (当前50)
        current_macd_threshold = 50
        fp_macd_scores = [f.get('macd_score', 0) for f in fp_features]
        fn_macd_scores = [f.get('macd_score', 0) for f in fn_features]

        fp_near_threshold = sum(1 for score in fp_macd_scores if current_macd_threshold <= score <= current_macd_threshold + 10)
        fn_near_threshold = sum(1 for score in fn_macd_scores if current_macd_threshold - 10 <= score < current_macd_threshold)

        # 根据FP和FN的分布决定调整方向
        if fp_near_threshold > 5 and fp_near_threshold > fn_near_threshold:
            # FP集中在阈值附近 → 提高阈值
            suggested_macd = current_macd_threshold + min(10, fp_near_threshold // 2)
            reason = f'{fp_near_threshold}个FP在{current_macd_threshold}-{current_macd_threshold+10}之间，提高阈值可减少错误推荐'
        elif fn_near_threshold > 5 and fn_near_threshold > fp_near_threshold:
            # FN集中在阈值以下 → 降低阈值
            suggested_macd = current_macd_threshold - min(10, fn_near_threshold // 2)
            reason = f'{fn_near_threshold}个FN在{current_macd_threshold-10}-{current_macd_threshold}之间，降低阈值可提高召回率'
        else:
            suggested_macd = current_macd_threshold
            reason = 'MACD阈值表现良好'

        threshold_analysis['MACD_SCORE_THRESHOLD'] = {
            'current': current_macd_threshold,
            'suggested': suggested_macd,
            'fp_near_threshold': fp_near_threshold,
            'fn_near_threshold': fn_near_threshold,
            'reason': reason
        }

        # 2. VOLUME_RATIO_THRESHOLD (当前2.0)
        current_volume_threshold = 2.0
        fp_volumes = [f.get('volume_ratio', 0) for f in fp_features]
        fn_volumes = [f.get('volume_ratio', 0) for f in fn_features]

        fp_near_threshold = sum(1 for v in fp_volumes if current_volume_threshold <= v <= current_volume_threshold + 0.5)
        fn_near_threshold = sum(1 for v in fn_volumes if current_volume_threshold - 0.5 <= v < current_volume_threshold)

        if fp_near_threshold > 5 and fp_near_threshold > fn_near_threshold:
            suggested_volume = round(current_volume_threshold + 0.3, 1)
            reason = f'{fp_near_threshold}个FP的成交量在{current_volume_threshold}-{current_volume_threshold+0.5}之间，提高阈值'
        elif fn_near_threshold > 5 and fn_near_threshold > fp_near_threshold:
            suggested_volume = round(current_volume_threshold - 0.3, 1)
            reason = f'{fn_near_threshold}个FN的成交量在{current_volume_threshold-0.5}-{current_volume_threshold}之间，降低阈值'
        else:
            suggested_volume = current_volume_threshold
            reason = '成交量阈值表现良好'

        threshold_analysis['VOLUME_RATIO_THRESHOLD'] = {
            'current': current_volume_threshold,
            'suggested': suggested_volume,
            'fp_near_threshold': fp_near_threshold,
            'fn_near_threshold': fn_near_threshold,
            'reason': reason
        }

        # 3. MIN_ENHANCED_SCORE (当前25，如果有tuning_config则使用调优值)
        current_enhanced_threshold = 25
        if os.path.exists(self.tuning_config_path):
            try:
                with open(self.tuning_config_path, 'r') as f:
                    tuning_config = json.load(f)
                    current_enhanced_threshold = tuning_config.get('MIN_ENHANCED_SCORE', 25)
            except:
                pass

        fp_enhanced = [f.get('enhanced_score', 0) for f in fp_features]
        fn_enhanced = [f.get('enhanced_score', 0) for f in fn_features]

        fp_low_score = sum(1 for s in fp_enhanced if s < current_enhanced_threshold + 5)
        fn_high_score = sum(1 for s in fn_enhanced if s >= current_enhanced_threshold - 5)

        if fp_low_score > 5 and fp_low_score > fn_high_score:
            suggested_enhanced = current_enhanced_threshold + 5
            reason = f'{fp_low_score}个FP的补充特征分偏低，提高阈值'
        elif fn_high_score > 5 and fn_high_score > fp_low_score:
            suggested_enhanced = max(15, current_enhanced_threshold - 5)
            reason = f'{fn_high_score}个FN的补充特征分达标，降低阈值'
        else:
            suggested_enhanced = current_enhanced_threshold
            reason = '补充特征分阈值表现良好'

        threshold_analysis['MIN_ENHANCED_SCORE'] = {
            'current': current_enhanced_threshold,
            'suggested': suggested_enhanced,
            'fp_below_threshold': fp_low_score,
            'fn_above_threshold': fn_high_score,
            'reason': reason
        }

        pattern_analysis['threshold_analysis'] = threshold_analysis

        logger.info("特征模式分析完成")
        return pattern_analysis

    # ========== 模块4：自适应调优 ==========

    def generate_adaptive_tuning(self, pattern_analysis: Dict) -> Dict:
        """
        基于特征模式生成自适应调优建议

        Args:
            pattern_analysis: 特征模式分析结果

        Returns:
            调优建议字典
        """
        logger.info(f"生成自适应调优建议（学习率: {self.learning_rate}）...")

        if 'error' in pattern_analysis:
            return {'adjustments': [], 'error': pattern_analysis['error']}

        adjustments = []

        for param, analysis in pattern_analysis.get('threshold_analysis', {}).items():
            current = analysis['current']
            suggested = analysis['suggested']

            if suggested == current:
                logger.info(f"  {param}: 无需调整 (当前值: {current})")
                continue

            # 应用学习率做小幅调整
            delta = suggested - current
            actual_value = current + delta * self.learning_rate

            # 四舍五入
            if param == 'MACD_SCORE_THRESHOLD':
                actual_value = int(round(actual_value))
            elif param in ['VOLUME_RATIO_THRESHOLD', 'MA_DISTANCE_THRESHOLD']:
                actual_value = round(actual_value, 1)
            elif param == 'MIN_ENHANCED_SCORE':
                actual_value = int(round(actual_value))
            else:
                actual_value = round(actual_value, 2)

            # 计算预期影响
            if suggested > current:
                expected_impact = 'precision ↑, recall ↓'
            else:
                expected_impact = 'precision ↓, recall ↑'

            # 计算置信度
            fp_count = analysis.get('fp_near_threshold', 0) + analysis.get('fp_below_threshold', 0)
            fn_count = analysis.get('fn_near_threshold', 0) + analysis.get('fn_above_threshold', 0)
            total_evidence = fp_count + fn_count
            confidence = min(0.95, 0.5 + total_evidence * 0.05)

            adjustments.append({
                'parameter': param,
                'current': current,
                'suggested': suggested,
                'actual_adjustment': actual_value,
                'delta': actual_value - current,
                'reason': analysis['reason'],
                'expected_impact': expected_impact,
                'confidence': confidence
            })

            logger.info(f"  {param}: {current} → {actual_value} (建议: {suggested})")

        return {'adjustments': adjustments}

    # ========== 模块5：改进追踪 ==========

    def track_improvement(self, accuracy: Dict, adjustments: List,
                         gap_analysis: Dict, date_str: str):
        """
        追踪改进历史，记录到tuning_history.json

        Args:
            accuracy: 准确性统计
            adjustments: 调优建议列表
            gap_analysis: Gap分析结果
            date_str: 日期字符串
        """
        logger.info("记录改进历史...")

        # 读取历史记录
        history_data = {'history': [], 'summary': {}}
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            except Exception as e:
                logger.warning(f"读取历史记录失败: {str(e)}")

        # 构建当前记录
        current_record = {
            'date': date_str,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'metrics': {
                'precision': accuracy.get('precision', 0),
                'recall': accuracy.get('recall', 0),
                'f1_score': accuracy.get('f1_score', 0),
                'accuracy': accuracy.get('accuracy', 0),
                'true_positives': accuracy.get('true_positives', 0),
                'false_positives': accuracy.get('false_positives', 0),
                'false_negatives': accuracy.get('false_negatives', 0),
                'true_negatives': accuracy.get('true_negatives', 0)
            },
            'adjustments': [
                f"{adj['parameter']}: {adj['current']}→{adj['actual_adjustment']}"
                for adj in adjustments
            ],
            'adjustment_details': adjustments,
            'error_patterns': {
                'false_positives': len(gap_analysis.get('false_positives', [])),
                'false_negatives': len(gap_analysis.get('false_negatives', [])),
                'true_positives': len(gap_analysis.get('true_positives', []))
            }
        }

        # 计算改进情况（与上一次对比）
        if history_data['history']:
            prev_record = history_data['history'][-1]
            prev_metrics = prev_record['metrics']

            current_record['improvement'] = {
                'precision_change': current_record['metrics']['precision'] - prev_metrics['precision'],
                'recall_change': current_record['metrics']['recall'] - prev_metrics['recall'],
                'f1_change': current_record['metrics']['f1_score'] - prev_metrics['f1_score'],
                'fp_reduction': prev_record['error_patterns']['false_positives'] - current_record['error_patterns']['false_positives'],
                'fn_reduction': prev_record['error_patterns']['false_negatives'] - current_record['error_patterns']['false_negatives']
            }

        # 添加到历史
        history_data['history'].append(current_record)

        # 更新总结
        if len(history_data['history']) >= 2:
            first_metrics = history_data['history'][0]['metrics']
            latest_metrics = current_record['metrics']

            history_data['summary'] = {
                'total_tunings': len(history_data['history']),
                'first_date': history_data['history'][0]['date'],
                'latest_date': date_str,
                'overall_improvement': {
                    'precision': f"{(latest_metrics['precision'] - first_metrics['precision']):.2%}",
                    'recall': f"{(latest_metrics['recall'] - first_metrics['recall']):.2%}",
                    'f1_score': f"{(latest_metrics['f1_score'] - first_metrics['f1_score']):.2%}"
                },
                'best_f1_score': max(r['metrics']['f1_score'] for r in history_data['history']),
                'best_f1_date': max(history_data['history'], key=lambda r: r['metrics']['f1_score'])['date']
            }

        # 保存
        try:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            logger.info(f"改进历史已保存到: {os.path.basename(self.history_path)}")
        except Exception as e:
            logger.error(f"保存改进历史失败: {str(e)}")

    def get_improvement_summary(self) -> Optional[Dict]:
        """
        获取改进总结

        Returns:
            改进总结字典，如果文件不存在则返回None
        """
        if not os.path.exists(self.history_path):
            return None

        try:
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            return history_data.get('summary')
        except Exception as e:
            logger.error(f"读取改进总结失败: {str(e)}")
            return None
