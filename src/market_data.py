"""
Market data access via Alpaca's REST API (alpaca-py), used directly for
standalone testing/running of the agent loop (see CLAUDE_CODE_CONTEXT.md
for why this is separate from the MCP/Hermes integration path).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient

# Credentials live outside the repo on purpose. Never committed.
ENV_PATH = Path(r"C:\Users\vivek\Desktop\alpaca.env")


def get_data_client() -> StockHistoricalDataClient:
    """Load Alpaca credentials and construct the market data client."""
    load_dotenv(ENV_PATH)

    api_key = os.environ["ALPACA_API_KEY"]
    secret_key = os.environ["ALPACA_SECRET_KEY"]

    return StockHistoricalDataClient(api_key, secret_key)
