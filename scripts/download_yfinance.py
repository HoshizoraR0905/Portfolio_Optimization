from pathlib import Path

import pandas as pd
import yfinance as yf
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def download_prices(config: dict) -> pd.DataFrame:
    data_config = config["data"]

    downloaded = yf.download(
        tickers=data_config["tickers"],
        start=data_config["start_date"],
        end=data_config["end_date"],
        interval=data_config["interval"],
        auto_adjust=data_config["auto_adjust"],
        progress=True,
        threads=True,
    )

    if downloaded.empty:
        raise RuntimeError("No market data were downloaded.")

    prices = downloaded["Close"].copy()
    prices.index.name = "date"
    prices = prices.sort_index()

    return prices


def validate_prices(prices: pd.DataFrame) -> None:
    print("\nDate range:")
    print(f"{prices.index.min().date()} to {prices.index.max().date()}")

    print("\nObservations and assets:")
    print(prices.shape)

    print("\nMissing values by asset:")
    print(prices.isna().sum().sort_values(ascending=False))


def main() -> None:
    config = load_config()
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    prices = download_prices(config)
    validate_prices(prices)

    output_path = RAW_DATA_DIR / "etf_adjusted_close.csv"
    prices.to_csv(output_path)

    print(f"\nSaved adjusted close prices to:\n{output_path}")


if __name__ == "__main__":
    main()