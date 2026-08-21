"""
Main entry point for a single agent loop pass.

This is the script the cron job (or a manual run) triggers. It:
  1. Pulls bars for the watchlist
  2. Runs signal detection
  3. For any fired signal, selects a debit spread and sizes the order
  4. Journals every decision along the way
  5. (checks open positions for exit conditions. TODO once execution
     is wired to live Alpaca calls)

Market data / order calls are left as TODOs marked clearly below.
This script defines the *shape* of the loop; the actual Alpaca calls
get filled in once wired to Hermes' MCP tools or the alpaca-py client
directly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.watchlist import WATCHLIST
from src.market_data import fetch_bars, fetch_option_chain
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

        # TODO: pull real account equity + leg prices before sizing.
        # plan = size_position(spread, account_equity=..., long_leg_price=...,
        #                       short_leg_price=..., open_position_count=...)
        # if plan:
        #     log_entry("trade_entry", plan)
        #     payload = build_order_payload(plan)
        #     # place order via Alpaca MCP tool / alpaca-py client here


if __name__ == "__main__":
    run_once()
