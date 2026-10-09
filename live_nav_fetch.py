
from pathlib import Path

import pandas as pd
import requests

# Project paths
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Five key schemes plus HDFC Top 100 Direct
SCHEMES = {
    "125497": "HDFC Top 100 Direct",
    "119551": "SBI Bluechip",
    "120503": "ICICI Bluechip",
    "118632": "Nippon Large Cap",
    "119092": "Axis Bluechip",
    "120841": "Kotak Bluechip",
}


def fetch_nav(scheme_code, expected_name):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    print(f"\nFetching {expected_name} (AMFI code: {scheme_code})")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        result = response.json()

        metadata = result.get("meta") or {}
        nav_records = result.get("data") or []

        if not nav_records:
            print("WARNING: API returned no NAV records.")
            return False

        df = pd.DataFrame(nav_records)

        required_columns = {"date", "nav"}
        if not required_columns.issubset(df.columns):
            print("WARNING: API response is missing date or nav columns.")
            return False

        df["scheme_code"] = str(scheme_code)
        df["scheme_name"] = metadata.get("scheme_name", expected_name)

        # Keep the NAV values and dates as returned by the API.
        output_columns = ["scheme_code", "scheme_name", "date", "nav"]
        df = df[output_columns]

        output_file = RAW_DIR / f"live_nav_{scheme_code}.csv"
        df.to_csv(output_file, index=False)

        print(f"Scheme name: {metadata.get('scheme_name', expected_name)}")
        print(f"NAV records saved: {len(df):,}")
        print(f"Output: {output_file.relative_to(BASE_DIR)}")
        return True

    except (requests.RequestException, ValueError) as error:
        print(f"ERROR fetching {scheme_code}: {error}")
        return False


def main():
    successful = 0

    for code, name in SCHEMES.items():
        if fetch_nav(code, name):
            successful += 1

    print(f"\nCompleted: {successful}/{len(SCHEMES)} schemes fetched successfully.")


if __name__ == "__main__":
    main()