"""
Main entry point for a single agent loop pass.

This is the script the cron job (or a manual run) triggers. It:
  1. Pulls bars for the watchlist
  2. Runs signal detection
  3. For any fired signal, selects a debit spread, sizes it, and places
     the order
  4. Journals every decision along the way
  5. (checks open positions for exit conditions. Still a TODO, see
     CLAUDE_CODE_CONTEXT.md)

This version calls Alpaca directly via alpaca-py. Wiring the same logic
into Hermes' MCP tools, for the live autonomous loop, is a separate later
step.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.watchlist import WATCHLIST
from src.market_data import fetch_bars, fetch_option_chain, fetch_option_quotes
from src.broker import get_account_equity, get_open_spread_count, place_debit_spread_order
from src.signals import scan_watchlist
from src.options_selector import select_debit_spread
from src.execution import size_position, build_order_payload
from src.journal import log_entry


def run_once():
    print(f"Scanning {len(WATCHLIST)} tickers: {', '.join(WATCHLIST)}")

    bars_by_ticker = fetch_bars(WATCHLIST)

    if not bars_by_ticker:
        print("No bar data returned from Alpaca. Skipping this run.")
        return

    results = scan_watchlist(bars_by_ticker)

    for result in results:
        log_entry("signal_check", result)
        print(f"[{result.ticker}] fired={result.fired}: {result.reasoning}")

        if not result.fired:
            continue

        option_chain = fetch_option_chain(result.ticker, result.direction)

        spread = select_debit_spread(result.ticker, result.direction, option_chain)
        if spread is None:
            print(f"[{result.ticker}] signal fired but no suitable spread found.")
            continue

        log_entry("spread_selected", spread)
        print(f"[{result.ticker}] {spread.reasoning}")

        quotes = fetch_option_quotes([spread.long_leg.symbol, spread.short_leg.symbol])
        # Buying the long leg: use the ask (the price we'd actually pay).
        # Selling the short leg: use the bid (the price we'd actually receive).
        long_leg_price = quotes[spread.long_leg.symbol][1]
        short_leg_price = quotes[spread.short_leg.symbol][0]

        plan = size_position(
            spread,
            account_equity=get_account_equity(),
            long_leg_price=long_leg_price,
            short_leg_price=short_leg_price,
            open_position_count=get_open_spread_count(),
        )
        if plan is None:
            print(f"[{result.ticker}] spread found but sizing rejected it "
                  f"(position limit reached or risk budget too small).")
            continue

        log_entry("trade_entry", plan)
        print(f"[{result.ticker}] {plan.reasoning}")

        payload = build_order_payload(plan)
        log_entry("order_payload_built", payload)

        order = place_debit_spread_order(plan)
        log_entry("order_submitted", {"order_id": str(order.id), "status": str(order.status)})
        print(f"[{result.ticker}] order submitted, id={order.id}, status={order.status}")


if __name__ == "__main__":
    run_once()
