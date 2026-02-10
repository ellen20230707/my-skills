"""
每日股票推荐工具

功能：
1. 每天22:00自动运行分析
2. 基于stock_macd_volumn的分析结果
3. 筛选并推荐第二天可买入的股票
4. 生成详细的推荐理由

使用方法：
    python daily_recommendation.py

定时任务配置（每天22:00执行）：
    0 22 * * * cd /Users/ellen_li/2026projects/my-skills/skills/stock_daily_recommendation && source ../../venv/bin/activate && python daily_recommendation.py >> logs/recommendation.log 2>&1

Author: Claude
Date: 2026-02-09
"""

import os
import sys
import json
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any

# 添加stock_macd_volumn到路径
parent_dir = os.path.dirname(os.path.dirname(__file__))
macd_dir = os.path.join(parent_dir, 'stock_macd_volumn')
sys.path.insert(0, macd_dir)

from config import Config
from stock_trend_analyzer import analyze_all_stocks


# 配置日志
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'recommendation.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RecommendationConfig:
    """推荐配置"""

    # 输出目录
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'recommendations')

    # 推荐数量
    TOP_N_STOCKS = 20  # 推荐前20只股票

    # 评级过滤
    MIN_RATING = 'B'  # 最低评级要求（A/B/C）

    # 补充特征分数要求
    MIN_ENHANCED_SCORE = 20  # A级≥30, B级≥20

    # 报告格式
    REPORT_FORMAT = 'both'  # 'text', 'html', 'both'


def generate_buy_reason(signal: Dict[str, Any]) -> str:
    """
    生成买入理由

    Args:
        signal: 信号字典

    Returns:
        str: 买入理由描述
    """
    reasons = []

    # 1. MACD分析
    macd_score = signal['macd_score']
    if macd_score >= 80:
        reasons.append(f"📈 MACD强势上涨({macd_score}分)，多项指标优秀")
    elif macd_score >= 65:
        reasons.append(f"📈 MACD上涨趋势明确({macd_score}分)，金叉信号良好")
    else:
        reasons.append(f"📈 MACD显示上涨信号({macd_score}分)")

    # 2. 成交量分析
    volume_ratio = signal['volume_ratio']
    if volume_ratio >= 3.0:
        reasons.append(f"💪 成交量剧烈放大({volume_ratio:.2f}倍)，资金大量介入")
    elif volume_ratio >= 2.5:
        reasons.append(f"💪 成交量明显放大({volume_ratio:.2f}倍)，交投活跃")
    elif volume_ratio >= 2.0:
        reasons.append(f"💪 成交量放大({volume_ratio:.2f}倍)，交易升温")
    else:
        reasons.append(f"💪 成交量温和放大({volume_ratio:.2f}倍)")

    # 3. 位置分析
    ma60_distance = signal['ma60_distance']
    if -3 <= ma60_distance <= 0.5:
        reasons.append(f"🎯 临界突破位置(距60日均线{ma60_distance:.2f}%)，最佳买入点")
    elif ma60_distance < -10:
        reasons.append(f"🎯 深度蓄势(距60日均线{ma60_distance:.2f}%)，上涨空间大")
    else:
        reasons.append(f"🎯 低位启动(距60日均线{ma60_distance:.2f}%)，未追高")

    # 4. 补充特征分析
    enhanced_details = signal.get('enhanced_details', {})

    if 'rsi' in enhanced_details:
        rsi_info = enhanced_details['rsi']
        if rsi_info.get('status') == '黄金区间':
            reasons.append(f"✨ RSI处于黄金区间({rsi_info['value']:.1f})，强弱适中")

    if 'kdj' in enhanced_details:
        kdj_info = enhanced_details['kdj']
        if kdj_info.get('status') == '金叉信号':
            reasons.append(f"✨ KDJ金叉信号，短期上涨概率高")

    if 'boll' in enhanced_details:
        boll_info = enhanced_details['boll']
        if boll_info.get('status') == '收窄待突破':
            reasons.append(f"✨ 布林带收窄，即将突破")

    if 'pattern' in enhanced_details:
        pattern = enhanced_details['pattern']
        if pattern != '无明显形态':
            reasons.append(f"✨ 价格形态：{pattern}")

    if 'volume_price' in enhanced_details:
        vp_status = enhanced_details['volume_price']
        if vp_status == '量价齐升':
            reasons.append(f"✨ 量价配合良好，上涨动能充足")

    # 5. 综合评级
    rating = signal['rating']
    enhanced_score = signal['enhanced_score']
    if rating == 'A级':
        reasons.append(f"⭐ A级推荐(综合{enhanced_score}分)，多项补充指标优秀")
    elif rating == 'B级':
        reasons.append(f"⭐ B级关注(综合{enhanced_score}分)，部分补充指标良好")

    return "\n   ".join(reasons)


def format_text_report(recommendations: List[Dict], summary: Dict) -> str:
    """
    生成文本格式报告

    Args:
        recommendations: 推荐列表
        summary: 汇总信息

    Returns:
        str: 文本报告
    """
    report_lines = []

    # 标题
    today = datetime.now().strftime('%Y年%m月%d日')
    report_lines.append("=" * 80)
    report_lines.append(f"📊 {today} 股票买入推荐报告")
    report_lines.append("=" * 80)
    report_lines.append("")

    # 市场概况
    report_lines.append("📈 市场概况：")
    report_lines.append(f"   • 分析股票数：{summary['total_stocks']} 只")
    report_lines.append(f"   • 发现信号：{summary['total_signals']} 个")
    report_lines.append(f"   • 有信号股票：{summary['stocks_with_signals']} 只")
    report_lines.append(f"   • 筛选模式：{summary['filter_mode']}")
    report_lines.append("")

    # 评级分布
    if 'rating_distribution' in summary:
        report_lines.append("⭐ 评级分布：")
        for rating, count in summary['rating_distribution'].items():
            report_lines.append(f"   • {rating}：{count} 个信号")
        report_lines.append("")

    # 推荐股票列表
    report_lines.append(f"🎯 今日推荐（前{len(recommendations)}只）：")
    report_lines.append("")

    for i, rec in enumerate(recommendations, 1):
        report_lines.append(f"【{i}】{rec['stock_name']} ({rec['stock_code']}) - {rec['rating']}")
        report_lines.append(f"   信号日期：{rec['date']}")
        report_lines.append(f"   当前价格：¥{rec['close']:.2f}")
        report_lines.append(f"   MACD评分：{rec['macd_score']} | 成交量比率：{rec['volume_ratio']:.2f}倍 | 综合评分：{rec['enhanced_score']}")
        report_lines.append("")
        report_lines.append("   📝 买入理由：")
        report_lines.append(f"   {rec['buy_reason']}")
        report_lines.append("")
        report_lines.append("-" * 80)
        report_lines.append("")

    # 风险提示
    report_lines.append("⚠️  风险提示：")
    report_lines.append("   1. 本报告仅供参考，不构成投资建议")
    report_lines.append("   2. 股市有风险，投资需谨慎")
    report_lines.append("   3. 建议结合个人风险承受能力和市场环境综合判断")
    report_lines.append("   4. 建议设置止损位，控制风险")
    report_lines.append("")

    # 策略说明
    report_lines.append("📚 策略说明：")
    report_lines.append("   本推荐基于以下核心特征：")
    report_lines.append("   • MACD上涨趋势（评分≥50分）")
    report_lines.append("   • 成交量放大（≥2.0倍）")
    report_lines.append("   • 低位启动（未突破60日均线）")
    report_lines.append("   • 补充指标确认（RSI、KDJ、布林带、形态、量价）")
    report_lines.append("")

    # 生成时间
    report_lines.append(f"📅 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("🤖 由A股上涨趋势分析工具自动生成")
    report_lines.append("=" * 80)

    return "\n".join(report_lines)


def format_html_report(recommendations: List[Dict], summary: Dict) -> str:
    """
    生成HTML格式报告

    Args:
        recommendations: 推荐列表
        summary: 汇总信息

    Returns:
        str: HTML报告
    """
    today = datetime.now().strftime('%Y年%m月%d日')

    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{today} 股票买入推荐报告</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .summary-item {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .summary-item .label {{
            color: #666;
            font-size: 14px;
        }}
        .summary-item .value {{
            color: #333;
            font-size: 24px;
            font-weight: bold;
            margin-top: 5px;
        }}
        .stock-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .stock-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .stock-title {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }}
        .stock-code {{
            color: #666;
            margin-left: 10px;
        }}
        .rating {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .rating-A {{
            background: #ff6b6b;
            color: white;
        }}
        .rating-B {{
            background: #4ecdc4;
            color: white;
        }}
        .rating-C {{
            background: #95afc0;
            color: white;
        }}
        .stock-meta {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }}
        .meta-item {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
        }}
        .meta-label {{
            color: #666;
            font-size: 12px;
        }}
        .meta-value {{
            color: #333;
            font-weight: bold;
            font-size: 16px;
            margin-top: 5px;
        }}
        .reasons {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
        }}
        .reasons h4 {{
            margin: 0 0 15px 0;
            color: #333;
        }}
        .reason-item {{
            margin: 10px 0;
            padding-left: 20px;
            color: #555;
            line-height: 1.6;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 {today} 股票买入推荐报告</h1>
        <p>基于技术指标分析的量化推荐</p>
    </div>

    <div class="summary">
        <h3>📈 市场概况</h3>
        <div class="summary-grid">
            <div class="summary-item">
                <div class="label">分析股票数</div>
                <div class="value">{summary['total_stocks']}</div>
            </div>
            <div class="summary-item">
                <div class="label">发现信号</div>
                <div class="value">{summary['total_signals']}</div>
            </div>
            <div class="summary-item">
                <div class="label">有信号股票</div>
                <div class="value">{summary['stocks_with_signals']}</div>
            </div>
            <div class="summary-item">
                <div class="label">推荐股票</div>
                <div class="value">{len(recommendations)}</div>
            </div>
        </div>
    </div>

    <h3>🎯 今日推荐</h3>
"""

    # 推荐股票卡片
    for i, rec in enumerate(recommendations, 1):
        rating_class = rec['rating'].replace('级', '')

        html += f"""
    <div class="stock-card">
        <div class="stock-header">
            <div>
                <span class="stock-title">【{i}】{rec['stock_name']}</span>
                <span class="stock-code">{rec['stock_code']}</span>
            </div>
            <span class="rating rating-{rating_class}">{rec['rating']}</span>
        </div>

        <div class="stock-meta">
            <div class="meta-item">
                <div class="meta-label">信号日期</div>
                <div class="meta-value">{rec['date']}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">当前价格</div>
                <div class="meta-value">¥{rec['close']:.2f}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">MACD评分</div>
                <div class="meta-value">{rec['macd_score']}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">成交量比率</div>
                <div class="meta-value">{rec['volume_ratio']:.2f}倍</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">综合评分</div>
                <div class="meta-value">{rec['enhanced_score']}</div>
            </div>
        </div>

        <div class="reasons">
            <h4>📝 买入理由</h4>
            {"".join([f'<div class="reason-item">{reason}</div>' for reason in rec['buy_reason'].split('\\n   ')])}
        </div>
    </div>
"""

    # 风险提示和结尾
    html += f"""
    <div class="warning">
        <h4>⚠️ 风险提示</h4>
        <ul>
            <li>本报告仅供参考，不构成投资建议</li>
            <li>股市有风险，投资需谨慎</li>
            <li>建议结合个人风险承受能力和市场环境综合判断</li>
            <li>建议设置止损位，控制风险</li>
        </ul>
    </div>

    <div class="footer">
        <p>📅 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>🤖 由A股上涨趋势分析工具自动生成</p>
    </div>
</body>
</html>
"""

    return html


def generate_recommendations():
    """
    生成每日推荐
    """
    logger.info("=" * 60)
    logger.info("每日股票推荐工具")
    logger.info("=" * 60)
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 确保输出目录存在
    os.makedirs(RecommendationConfig.OUTPUT_DIR, exist_ok=True)

    # 1. 运行分析（实盘模式，不验证未来涨幅）
    logger.info("正在运行股票趋势分析...")
    analysis_result = analyze_all_stocks(
        data_dir=Config.DATA_DIR,
        output_dir=Config.OUTPUT_DIR,
        config=Config,
        enable_future_validation=False  # 实盘模式
    )

    if not analysis_result or analysis_result['total_signals'] == 0:
        logger.warning("未发现任何信号，无法生成推荐")
        return False

    logger.info(f"分析完成: 发现 {analysis_result['total_signals']} 个信号")

    # 2. 读取分析结果
    from datetime import datetime as dt
    today_str = dt.now().strftime('%Y%m%d')

    # 查找最新的CSV文件
    import glob
    csv_pattern = os.path.join(Config.OUTPUT_DIR, f"trend_signals_{today_str}.csv")
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        # 如果今天的不存在，找最新的
        csv_pattern = os.path.join(Config.OUTPUT_DIR, "trend_signals_*.csv")
        csv_files = sorted(glob.glob(csv_pattern), reverse=True)

    if not csv_files:
        logger.error("未找到分析结果CSV文件")
        return False

    latest_csv = csv_files[0]
    logger.info(f"读取分析结果: {latest_csv}")

    df = pd.read_csv(latest_csv)

    if df.empty:
        logger.warning("分析结果为空")
        return False

    # 3. 筛选和排序
    logger.info("筛选推荐股票...")

    # 评级过滤
    if RecommendationConfig.MIN_RATING == 'A':
        df = df[df['评级'] == 'A级']
    elif RecommendationConfig.MIN_RATING == 'B':
        df = df[df['评级'].isin(['A级', 'B级'])]

    # 补充特征分数过滤
    df = df[df['补充特征分'] >= RecommendationConfig.MIN_ENHANCED_SCORE]

    # 转换日期格式
    df['信号日期'] = pd.to_datetime(df['信号日期'])

    # 只保留信号日期是当天的股票
    today = pd.Timestamp.now().normalize()
    df = df[df['信号日期'].dt.normalize() == today]

    logger.info(f"当天信号数: {len(df)}")

    # 如果有多个信号来自同一只股票，取综合得分最高的
    # 按日期排序（虽然都是当天，但保持一致性）
    df = df.sort_values('信号日期', ascending=False)

    # 综合评分排序
    # 评分公式：MACD评分*0.3 + 成交量比率*10 + 补充特征分*0.4
    df['综合得分'] = (df['MACD评分'] * 0.3 +
                     df['成交量比率'] * 10 +
                     df['补充特征分'] * 0.4)

    df = df.sort_values('综合得分', ascending=False)

    # 取前N只
    top_stocks = df.head(RecommendationConfig.TOP_N_STOCKS)

    logger.info(f"筛选出 {len(top_stocks)} 只推荐股票")

    # 4. 生成推荐列表
    recommendations = []
    for _, row in top_stocks.iterrows():
        signal = {
            'stock_code': row['股票代码'],
            'stock_name': row['股票名称'],
            'date': row['信号日期'].strftime('%Y-%m-%d'),
            'close': row['收盘价'],
            'macd_score': row['MACD评分'],
            'volume_ratio': row['成交量比率'],
            'ma60_distance': row['MA60距离%'],
            'rating': row['评级'],
            'enhanced_score': row['补充特征分'],
            'enhanced_details': {}  # 简化版本，实际应该从分析结果中获取
        }

        # 生成买入理由
        buy_reason = generate_buy_reason(signal)
        signal['buy_reason'] = buy_reason

        recommendations.append(signal)

    # 5. 生成报告
    summary = {
        'total_stocks': analysis_result['total_stocks'],
        'total_signals': analysis_result['total_signals'],
        'stocks_with_signals': analysis_result['stocks_with_signals'],
        'filter_mode': Config.FILTER_MODE,
        'rating_distribution': df['评级'].value_counts().to_dict()
    }

    timestamp = datetime.now().strftime('%Y%m%d')

    # 文本报告
    if RecommendationConfig.REPORT_FORMAT in ['text', 'both']:
        text_report = format_text_report(recommendations, summary)
        text_path = os.path.join(
            RecommendationConfig.OUTPUT_DIR,
            f'recommendation_{timestamp}.txt'
        )
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_report)
        logger.info(f"文本报告已保存: {text_path}")

        # 同时输出到控制台
        print("\n" + text_report)

    # HTML报告
    if RecommendationConfig.REPORT_FORMAT in ['html', 'both']:
        html_report = format_html_report(recommendations, summary)
        html_path = os.path.join(
            RecommendationConfig.OUTPUT_DIR,
            f'recommendation_{timestamp}.html'
        )
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        logger.info(f"HTML报告已保存: {html_path}")

    # JSON数据
    json_path = os.path.join(
        RecommendationConfig.OUTPUT_DIR,
        f'recommendation_{timestamp}.json'
    )
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'date': timestamp,
            'summary': summary,
            'recommendations': recommendations
        }, f, ensure_ascii=False, indent=2)
    logger.info(f"JSON数据已保存: {json_path}")

    logger.info("=" * 60)
    logger.info("✅ 推荐报告生成完成!")
    logger.info("=" * 60)

    return True


def main():
    """主函数"""
    try:
        success = generate_recommendations()
        return 0 if success else 1
    except Exception as e:
        logger.error(f"生成推荐失败: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
