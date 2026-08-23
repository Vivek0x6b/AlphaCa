"""
Account and position access via Alpaca's trading client.

Kept separate from market_data.py on purpose: the trading client is the
one that can also place and cancel real orders, while market_data.py only
ever reads prices. Keeping them apart makes it obvious at a glance which
code just looks at data and which code touches the account.
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass, OrderClass, OrderSide, TimeInForce
from alpaca.trading.models import Order
from alpaca.trading.requests import LimitOrderRequest, OptionLegRequest

from src.execution import OrderPlan
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


def place_debit_spread_order(plan: OrderPlan) -> Order:
    """
    Submit a sized debit spread as a real multi-leg limit order.

    The limit price is the same net debit per contract used for sizing
    (long leg ask minus short leg bid), so the order can't fill worse
    than what the 2%-of-equity risk budget was based on. If the market
    moves before the order posts, it may simply not fill right away
    rather than filling at a worse price.
    """
    limit_price = round(plan.est_cost_per_contract / 100, 2)

    order_request = LimitOrderRequest(
        qty=plan.contracts,
        order_class=OrderClass.MLEG,
        time_in_force=TimeInForce.DAY,
        limit_price=limit_price,
        legs=[
            OptionLegRequest(
                symbol=plan.spread.long_leg.symbol,
                ratio_qty=1,
                side=OrderSide.BUY,
            ),
            OptionLegRequest(
                symbol=plan.spread.short_leg.symbol,
                ratio_qty=1,
                side=OrderSide.SELL,
            ),
        ],
    )

    client = get_trading_client()
    return client.submit_order(order_request)
