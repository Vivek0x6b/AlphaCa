"""
Account and position access via Alpaca's trading client.

Kept separate from market_data.py on purpose: the trading client is the
one that can also place and cancel real orders, while market_data.py only
ever reads prices. Keeping them apart makes it obvious at a glance which
code just looks at data and which code touches the account.
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass

from src.market_data import load_credentials


def get_trading_client() -> TradingClient:
    """Load Alpaca credentials and construct the trading client."""
    api_key, secret_key = load_credentials()
    return TradingClient(api_key, secret_key, paper=True)


def get_account_equity() -> float:
    """Current total account equity, used to size positions."""
    client = get_trading_client()
    account = client.get_account()
    return float(account.equity)


def get_open_spread_count() -> int:
    """
    Number of tickers with an open option position.

    One debit spread shows up as two positions in the account (the long
    leg and the short leg), so counting raw positions would double-count
    each open spread. Counting distinct underlying tickers instead gives
    the number of open spread trades, which is what MAX_CONCURRENT_POSITIONS
    is meant to limit.
    """
    client = get_trading_client()
    positions = client.get_all_positions()

    option_positions = [p for p in positions if p.asset_class == AssetClass.US_OPTION]
    underlying_tickers = {_underlying_from_occ_symbol(p.symbol) for p in option_positions}

    return len(underlying_tickers)


def _underlying_from_occ_symbol(symbol: str) -> str:
    """The ticker part of an OCC option symbol, e.g. "SPY" from "SPY260911C00717000"."""
    return symbol[:-15]
