
from pathlib import Path
import pandas as pd

# Project paths
ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
REPORTS_DIR = ROOT / "reports"


def normalize_codes(series):
    """Normalize AMFI codes to strings for reliable comparison."""
    codes = series.dropna().astype(str).str.strip()
    codes = codes.str.replace(r"\.0$", "", regex=True)
    return set(codes[codes != ""])


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load and inspect all 10 provided CSV datasets
    csv_files = sorted(RAW_DIR.glob("[0-9][0-9]_*.csv"))

    if len(csv_files) != 10:
        print(f"WARNING: Expected 10 CSV files, found {len(csv_files)}.")

    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {RAW_DIR}")

    datasets = {}
    report = [
        "BLUESTOCK FINTECH - DAY 1 DATA QUALITY SUMMARY",
        "=" * 55,
        f"CSV files found: {len(csv_files)}",
        "",
    ]

    for file_path in csv_files:
        df = pd.read_csv(file_path, low_memory=False)
        datasets[file_path.name] = df

        print("\n" + "=" * 70)
        print(f"FILE: {file_path.name}")
        print(f"SHAPE: {df.shape}")
        print("\nDATA TYPES:")
        print(df.dtypes)
        print("\nFIRST FIVE ROWS:")
        print(df.head())

        missing = int(df.isna().sum().sum())
        duplicates = int(df.duplicated().sum())
        empty_rows = int(df.isna().all(axis=1).sum())

        report.extend([
            f"File: {file_path.name}",
            f"Rows: {df.shape[0]}",
            f"Columns: {df.shape[1]}",
            f"Missing cells: {missing}",
            f"Duplicate rows: {duplicates}",
            f"Completely empty rows: {empty_rows}",
            "",
        ])

        if df.empty:
            report.append("ANOMALY: Dataset is empty.")
        if missing:
            report.append(f"ANOMALY: {missing} missing cell(s).")
        if duplicates:
            report.append(f"ANOMALY: {duplicates} duplicate row(s).")
        if empty_rows:
            report.append(f"ANOMALY: {empty_rows} completely empty row(s).")

        report.append("")

    # 2. Explore the fund master
    fund_master = datasets["01_fund_master.csv"]

    print("\n" + "=" * 70)
    print("FUND MASTER EXPLORATION")

    exploration_columns = {
        "Fund houses": "fund_house",
        "Categories": "category",
        "Sub-categories": "sub_category",
        "Risk grades": "risk_category",
    }

    for label, column in exploration_columns.items():
        values = sorted(
            fund_master[column].dropna().astype(str).str.strip().unique()
        )
        print(f"\n{label} ({len(values)} unique values):")
        for value in values:
            print(f" - {value}")

        report.append(f"{label}: {len(values)} unique values")
        report.extend(f"  - {value}" for value in values)
        report.append("")

    # 3. Check AMFI scheme codes against NAV history
    nav_history = datasets["02_nav_history.csv"]

    master_codes = normalize_codes(fund_master["amfi_code"])
    nav_codes = normalize_codes(nav_history["amfi_code"])

    missing_codes = sorted(master_codes - nav_codes)
    extra_nav_codes = sorted(nav_codes - master_codes)

    print("\n" + "=" * 70)
    print("AMFI SCHEME-CODE VALIDATION")
    print(f"Unique codes in fund master: {len(master_codes)}")
    print(f"Unique codes in NAV history: {len(nav_codes)}")
    print(f"Fund-master codes absent from NAV history: {len(missing_codes)}")

    if missing_codes:
        print("Missing codes:", missing_codes)
    else:
        print("PASS: Every fund-master AMFI code exists in NAV history.")

    report.extend([
        "AMFI SCHEME-CODE VALIDATION",
        f"Unique fund-master codes: {len(master_codes)}",
        f"Unique NAV-history codes: {len(nav_codes)}",
        f"Fund-master codes absent from NAV history: {len(missing_codes)}",
        f"Extra NAV-history codes: {len(extra_nav_codes)}",
        f"Validation result: {'PASS' if not missing_codes else 'REVIEW REQUIRED'}",
    ])

    if missing_codes:
        report.append("Missing AMFI codes: " + ", ".join(missing_codes))

    if extra_nav_codes:
        report.append("Extra NAV codes: " + ", ".join(extra_nav_codes))

    # 4. Save the data quality summary
    report_path = REPORTS_DIR / "day1_data_quality_summary.txt"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"\nData quality summary saved to: {report_path}")


if __name__ == "__main__":
    main()