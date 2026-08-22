from pathlib import Path

import kagglehub
import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

EXTERNAL_DATA_DIR = PROJECT_ROOT / "data" / "external" / "kaggle-etf"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

DATASET_HANDLE = "jacksoncrow/stock-market-dataset"


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def download_etf(ticker: str) -> Path:
    dataset_path = f"etfs/{ticker}.csv"

    downloaded_path = kagglehub.dataset_download(
        DATASET_HANDLE,
        path=dataset_path,
        output_dir=str(EXTERNAL_DATA_DIR),
    )

    return Path(downloaded_path)


def read_adjusted_close(file_path: Path, ticker: str) -> pd.Series:
    data = pd.read_csv(
        file_path,
        parse_dates=["Date"],
        index_col="Date",
    )

    if "Adj Close" not in data.columns:
        raise ValueError(f"{ticker}: 'Adj Close' column not found.")

    adjusted_close = data["Adj Close"].rename(ticker)
    adjusted_close = adjusted_close[~adjusted_close.index.duplicated()]
    adjusted_close = adjusted_close.sort_index()

    return adjusted_close


def build_price_matrix(config: dict) -> pd.DataFrame:
    price_series = []

    for ticker in config["data"]["tickers"]:
        print(f"Processing {ticker}...")

        file_path = download_etf(ticker)
        adjusted_close = read_adjusted_close(file_path, ticker)
        price_series.append(adjusted_close)

    prices = pd.concat(price_series, axis=1).sort_index()

    start_date = config["data"]["start_date"]
    end_date = config["data"]["end_date"]

    prices = prices.loc[start_date:end_date]

    return prices


def validate_prices(prices: pd.DataFrame) -> None:
    print("\nDate range:")
    print(f"{prices.index.min().date()} to {prices.index.max().date()}")

    print("\nObservations and assets:")
    print(prices.shape)

    print("\nMissing values by asset:")
    print(prices.isna().sum().sort_values(ascending=False))

    print("\nFirst valid date by asset:")
    print(prices.apply(pd.Series.first_valid_index))


def main() -> None:
    config = load_config()

    EXTERNAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    prices = build_price_matrix(config)
    validate_prices(prices)

    output_path = PROCESSED_DATA_DIR / "etf_adjusted_close.csv"
    prices.to_csv(output_path)

    print(f"\nSaved processed price matrix to:\n{output_path}")


if __name__ == "__main__":
    main()