"""
Watchlist and signal parameters for AlphaCa.

Adjust these values to tune the strategy. Keep the reasoning behind each
choice in comments here so the thesis stays traceable.
"""

# Liquid, optionable large-caps and ETFs.
WATCHLIST = [
    "SPY",
    "QQQ",
    "AAPL",
    "NVDA",
    "MSFT",
    "AMD",
    "TSLA",
]

# --- Signal parameters ---

# Breakout lookback window (days). A close above the N-day high (for calls)
# or below the N-day low (for puts) is the breakout condition.
BREAKOUT_LOOKBACK_DAYS = 20

# Trend filter. Only take calls when price is above this moving average,
# only take puts when price is below it. Keeps trades aligned with trend.
TREND_MA_DAYS = 50

# Relative volume threshold. Breakout day volume must be at least this
# multiple of the trailing average volume to confirm real participation.
RELATIVE_VOLUME_LOOKBACK_DAYS = 20
RELATIVE_VOLUME_MULTIPLIER = 1.5

# --- Options selection parameters ---

# Target delta ranges for the debit spread legs.
LONG_LEG_DELTA_RANGE = (0.40, 0.50)
SHORT_LEG_DELTA_RANGE = (0.15, 0.20)

# Expiration window (calendar days out).
MIN_DAYS_TO_EXPIRY = 14
MAX_DAYS_TO_EXPIRY = 28

# --- Risk parameters ---

# Fraction of account equity risked per trade.
POSITION_SIZE_PCT = 0.02

# Maximum number of concurrent open positions.
MAX_CONCURRENT_POSITIONS = 3
