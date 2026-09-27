"""Prepare four official CSV exports and integrate them with SQLite."""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [str(q).replace("Q", "-Q") for q in pd.period_range("2017Q1", "2024Q4", freq="Q")]
COLUMNS = ["year_quarter", "avg_resale_price", "unemployment_rate", "avg_tbill_yield", "gdp_growth"]


def validate_frame(df):
    if list(df.columns) != COLUMNS or df["year_quarter"].tolist() != EXPECTED:
        raise ValueError("Expected one row per quarter from 2017-Q1 to 2024-Q4")
    if df.isna().any().any():
        raise ValueError("Missing values in integrated data")
    return df


def wide_series(path, label):
    frame = pd.read_csv(path)
    rows = frame.loc[frame["DataSeries"].str.strip().eq(label)]
    if len(rows) != 1:
        raise ValueError(f"Expected one {label!r} series in {path}")
    result = rows.melt(id_vars="DataSeries", var_name="period", value_name="value")
    result["value"] = pd.to_numeric(result["value"], errors="coerce")
    return result


def quarterly(path, label, name):
    frame = wide_series(path, label)
    parts = frame["period"].str.extract(r"^(\d{4})\s*([1-4])Q$")
    frame["year_quarter"] = parts[0] + "-Q" + parts[1]
    frame = frame.loc[frame["year_quarter"].isin(EXPECTED), ["year_quarter", "value"]]
    if frame["year_quarter"].duplicated().any():
        raise ValueError("Duplicate quarters")
    return frame.rename(columns={"value": name})


def main():
    raw = ROOT / "data/raw"
    hdb = pd.read_csv(raw / "hdb.csv", usecols=["month", "resale_price"])
    hdb["month"] = pd.to_datetime(hdb["month"], format="%Y-%m")
    hdb["year_quarter"] = hdb["month"].dt.to_period("Q").astype(str).str.replace("Q", "-Q")
    hdb = hdb.loc[hdb["year_quarter"].isin(EXPECTED)].copy()
    hdb["resale_price"] = pd.to_numeric(hdb["resale_price"], errors="raise")
    if hdb["resale_price"].isna().any():
        raise ValueError("Missing transaction prices")
    prices = hdb.groupby("year_quarter", as_index=False)["resale_price"].mean().rename(columns={"resale_price": "avg_resale_price"})
    unemployment = quarterly(raw / "unemployment.csv", "Resident Unemployment Rate", "unemployment_rate")
    gdp = quarterly(raw / "gdp.csv", "GDP In Chained (2015) Dollars", "gdp_growth")
    interest = wide_series(raw / "interest.csv", "Government Securities - 1-Year Treasury Bills Yield")
    interest["date"] = pd.to_datetime(interest["period"], format="%Y%b", errors="coerce")
    interest = interest.loc[interest["date"].dt.year.between(2017, 2024)].copy()
    if len(interest) != 96 or interest["date"].nunique() != 96 or interest["value"].isna().any():
        raise ValueError("Expected 96 unique, nonmissing monthly interest-rate values")
    interest["year_quarter"] = interest["date"].dt.to_period("Q").astype(str).str.replace("Q", "-Q")
    rates = interest.groupby("year_quarter", as_index=False)["value"].mean().rename(columns={"value": "avg_tbill_yield"})
    with sqlite3.connect(ROOT / "data/analysis.sqlite") as conn:
        for name, table in [("hdb", prices), ("unemployment", unemployment), ("interest", rates), ("gdp", gdp)]:
            table.to_sql(name, conn, if_exists="replace", index=False)
        final = pd.read_sql_query("""
            SELECT h.year_quarter, h.avg_resale_price, u.unemployment_rate,
                   i.avg_tbill_yield, g.gdp_growth
            FROM hdb h JOIN unemployment u USING (year_quarter)
            JOIN interest i USING (year_quarter) JOIN gdp g USING (year_quarter)
            ORDER BY h.year_quarter
        """, conn)
        validate_frame(final)
        final.to_sql("quarterly", conn, if_exists="replace", index=False)
    final.to_csv(ROOT / "data/quarterly_2017_2024.csv", index=False)
    print(f"Prepared {len(final)} quarters; CSV and SQLite database saved.")


if __name__ == "__main__":
    main()
