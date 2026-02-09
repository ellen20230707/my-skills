"""
A股上涨趋势分析配置文件

本模块定义了股票趋势分析的所有参数配置，包括技术指标参数、筛选阈值、
数据路径等。可通过修改此文件调整分析策略而无需修改核心代码。

Author: Claude
Date: 2026-02-09
"""

import os


class Config:
    """分析配置类"""

    # ============ 数据路径配置 ============
    DATA_DIR = "/Users/ellen_li/2026projects/A股近10年日线数据"
    OUTPUT_DIR = os.path.join(
        os.path.dirname(__file__),
        "output"
    )

    # ============ MACD参数 ============
    MACD_FAST = 12          # 快速EMA周期
    MACD_SLOW = 26          # 慢速EMA周期
    MACD_SIGNAL = 9         # 信号线周期
    MACD_SCORE_THRESHOLD = 50  # MACD评分阈值

    # MACD评分权重
    MACD_SCORE_WEIGHTS = {
        'golden_cross': 30,      # DIF > DEA（金叉状态）
        'above_zero': 20,        # DIF > 0 且 DEA > 0（零轴上方）
        'positive_hist': 15,     # MACD柱状图 > 0
        'dif_uptrend': 20,       # DIF连续5天上升
        'hist_increasing': 15,   # MACD柱连续3天递增
    }

    # ============ 成交量参数 ============
    VOLUME_RECENT_DAYS = 3      # 近期成交量天数
    VOLUME_BASELINE_DAYS = 20   # 基准成交量天数
    VOLUME_RATIO_THRESHOLD = 2.0  # 成交量放大倍数阈值

    # 成交量分级标准
    VOLUME_RATIO_LEVELS = {
        'moderate': 1.5,    # 温和放量
        'obvious': 2.0,     # 明显放量
        'strong': 3.0,      # 剧烈放量
    }

    # ============ 均线参数 ============
    MA_PERIOD = 60                  # 移动平均线周期
    MA_PERIOD_FALLBACK = 30         # 数据不足时的备选周期
    MA_DISTANCE_THRESHOLD = 0.5     # 距离60日均线的容差（%）

    # 均线距离状态分级
    MA_DISTANCE_LEVELS = {
        'optimal': (-3, 0.5),    # 临界突破（最佳状态）
        'accumulating': (-100, -10),  # 深度蓄势
        'breakthrough': (0.5, 100),   # 已突破（不符合条件）
    }

    # ============ 信号验证参数 ============
    FUTURE_DAYS = 5             # 验证未来涨幅的天数
    MIN_FUTURE_RETURN = 2.0     # 最小涨幅要求（%）

    # ============ 筛选模式 ============
    FILTER_MODE = "standard"    # strict/standard/loose

    # 筛选模式配置
    FILTER_MODES = {
        'strict': {
            'min_conditions': 4,    # 4个核心特征全部满足
            'description': '严格模式：精准度高，数量少'
        },
        'standard': {
            'min_conditions': 3,    # 至少3个核心特征满足
            'description': '标准模式：平衡精准度和数量（推荐）'
        },
        'loose': {
            'min_conditions': 2,    # 至少2个特征满足且MACD必须满足
            'description': '宽松模式：数量多，需人工复核'
        }
    }

    # ============ 补充指标参数 ============
    RSI_PERIOD = 14             # RSI周期
    RSI_RANGE = (40, 70)        # RSI黄金区间

    KDJ_PARAMS = (9, 3, 3)      # KDJ参数：N, M1, M2
    KDJ_J_THRESHOLD = 80        # KDJ的J值阈值

    BOLL_PERIOD = 20            # 布林带周期
    BOLL_STD = 2                # 布林带标准差倍数
    BOLL_WIDTH_THRESHOLD = 0.1  # 布林带宽度阈值

    # ============ 补充特征评分权重 ============
    ENHANCED_SCORE_WEIGHTS = {
        'rsi': 10,              # RSI在黄金区间
        'kdj': 15,              # KDJ金叉信号
        'boll': 10,             # 布林带收窄
        'pattern': 15,          # 价格形态良好
        'volume_price': 10,     # 量价齐升
    }

    # 评级阈值
    RATING_THRESHOLDS = {
        'A': 30,    # A级推荐
        'B': 20,    # B级关注
        'C': 0,     # C级观察
    }

    # ============ 数据质量筛选参数 ============
    MIN_DATA_ROWS = 60          # 最少数据行数
    MIN_DAILY_AMOUNT = 10_000_000  # 最小日均成交额（元）
    PRICE_RANGE = (2, 300)      # 价格区间（元）

    # ============ 风险控制参数 ============
    MAX_CONSECUTIVE_LIMIT_UP = 3    # 最大连续涨停天数
    MAX_SHORT_TERM_GAIN = 30        # 最大短期涨幅（%）
    VOLUME_SURGE_NO_GAIN = 5        # 巨量滞涨：成交额放大倍数
    VOLUME_SURGE_MIN_GAIN = 3       # 巨量滞涨：最小涨幅要求（%）
    MAX_MA20_DEVIATION = 30         # 距离20日均线最大偏离度（%）

    # ============ 其他参数 ============
    PROGRESS_INTERVAL = 100     # 进度显示间隔（每N只股票）
    LOG_LEVEL = "INFO"          # 日志级别

    # ============ 输出格式配置 ============
    CSV_ENCODING = "utf-8-sig"  # CSV编码（支持中文Excel）
    DATE_FORMAT = "%Y%m%d"      # 日期格式

    @classmethod
    def get_min_conditions(cls):
        """获取当前筛选模式的最少条件数"""
        return cls.FILTER_MODES[cls.FILTER_MODE]['min_conditions']

    @classmethod
    def get_filter_description(cls):
        """获取当前筛选模式的描述"""
        return cls.FILTER_MODES[cls.FILTER_MODE]['description']

    @classmethod
    def validate(cls):
        """验证配置参数的有效性"""
        errors = []

        # 验证数据路径
        if not os.path.exists(cls.DATA_DIR):
            errors.append(f"数据目录不存在: {cls.DATA_DIR}")

        # 验证MACD参数
        if cls.MACD_FAST >= cls.MACD_SLOW:
            errors.append(f"MACD快线周期({cls.MACD_FAST})必须小于慢线周期({cls.MACD_SLOW})")

        # 验证成交量参数
        if cls.VOLUME_RECENT_DAYS >= cls.VOLUME_BASELINE_DAYS:
            errors.append(f"近期成交量天数({cls.VOLUME_RECENT_DAYS})必须小于基准天数({cls.VOLUME_BASELINE_DAYS})")

        # 验证筛选模式
        if cls.FILTER_MODE not in cls.FILTER_MODES:
            errors.append(f"无效的筛选模式: {cls.FILTER_MODE}")

        # 验证价格区间
        if cls.PRICE_RANGE[0] >= cls.PRICE_RANGE[1]:
            errors.append(f"价格区间无效: {cls.PRICE_RANGE}")

        if errors:
            raise ValueError("配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))

        return True


# 创建输出目录
if not os.path.exists(Config.OUTPUT_DIR):
    os.makedirs(Config.OUTPUT_DIR)
