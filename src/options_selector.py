"""
Options chain filtering and strike/expiry selection for debit spreads.

Given a confirmed signal (call or put) from signals.py, this module picks
the long and short legs of a debit spread from the available option chain.

TODO: wire this up to real chain data via Alpaca's MCP tools
(get_option_chain / get_option_contracts). Left as a stub with the
intended shape so it's easy to fill in once chain data format is confirmed.
"""

from dataclasses import dataclass
from datetime import date
from typing import Literal

from config.watchlist import (
    LONG_LEG_DELTA_RANGE,
    SHORT_LEG_DELTA_RANGE,
    MIN_DAYS_TO_EXPIRY,
    MAX_DAYS_TO_EXPIRY,
)


@dataclass
class OptionLeg:
    symbol: str  # OCC option symbol
    strike: float
    expiry: date
    delta: float
    side: Literal["buy", "sell"]


@dataclass
class DebitSpread:
    ticker: str
    direction: Literal["call", "put"]
    long_leg: OptionLeg
    short_leg: OptionLeg
    expiry: date
    reasoning: str


def select_debit_spread(
    ticker: str,
    direction: Literal["call", "put"],
    option_chain: list[dict],
) -> DebitSpread | None:
    """
    Pick long/short legs for a debit spread from an option chain.

    Parameters
    ----------
    ticker: str
    direction: "call" or "put"
    option_chain: list of contract dicts as returned by Alpaca's
        get_option_chain / get_option_contracts tools. Expected to
        include at least: symbol, strike_price, expiration_date,
        delta, option_type.

    Returns
    -------
    DebitSpread or None if no suitable contracts were found.
    """
    option_type = "call" if direction == "call" else "put"

    candidates = [
        c
        for c in option_chain
        if c.get("option_type") == option_type
        and _within_expiry_window(c.get("expiration_date"))
    ]

    if not candidates:
        return None

    long_candidates = [
        c for c in candidates if _delta_in_range(c.get("delta"), LONG_LEG_DELTA_RANGE)
    ]
    short_candidates = [
        c
        for c in candidates
        if _delta_in_range(c.get("delta"), SHORT_LEG_DELTA_RANGE)
    ]

    if not long_candidates or not short_candidates:
        return None

    # Same expiration for both legs. Pick the expiry with a match on
    # both sides.
    long_by_expiry = {c["expiration_date"]: c for c in long_candidates}
    short_by_expiry = {c["expiration_date"]: c for c in short_candidates}
    shared_expiries = set(long_by_expiry) & set(short_by_expiry)

    if not shared_expiries:
        return None

    expiry_str = sorted(shared_expiries)[0]
    long_contract = long_by_expiry[expiry_str]
    short_contract = short_by_expiry[expiry_str]

    long_leg = OptionLeg(
        symbol=long_contract["symbol"],
        strike=float(long_contract["strike_price"]),
        expiry=date.fromisoformat(expiry_str),
        delta=float(long_contract["delta"]),
        side="buy",
    )
    short_leg = OptionLeg(
        symbol=short_contract["symbol"],
        strike=float(short_contract["strike_price"]),
        expiry=date.fromisoformat(expiry_str),
        delta=float(short_contract["delta"]),
        side="sell",
    )

    reasoning = (
        f"{ticker} {direction} debit spread: long {long_leg.strike} "
        f"(delta {long_leg.delta:.2f}), short {short_leg.strike} "
        f"(delta {short_leg.delta:.2f}), expiring {expiry_str}."
    )

    return DebitSpread(
        ticker=ticker,
        direction=direction,
        long_leg=long_leg,
        short_leg=short_leg,
        expiry=long_leg.expiry,
        reasoning=reasoning,
    )


def _within_expiry_window(expiration_date: str | None) -> bool:
    if not expiration_date:
        return False
    days_out = (date.fromisoformat(expiration_date) - date.today()).days
    return MIN_DAYS_TO_EXPIRY <= days_out <= MAX_DAYS_TO_EXPIRY


def _delta_in_range(delta: float | None, delta_range: tuple[float, float]) -> bool:
    if delta is None:
        return False
    return delta_range[0] <= abs(delta) <= delta_range[1]
