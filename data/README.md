# Data provenance

`quarterly_2017_2024.csv` contains 32 quarterly observations extracted from a saved integration table, retaining its displayed six-decimal precision. This is an analysis snapshot, not a fresh government-data download. Source revisions and rounding may change results slightly.

| Variable | Definition | Official source |
|---|---|---|
| avg_resale_price | Quarterly mean transaction price, SGD; not mix-adjusted | [HDB resale transactions](https://data.gov.sg/datasets/d_8b84c4ee58e3cfc0ece0d773c8ca6abc/view) |
| unemployment_rate | Resident unemployment, end of quarter, percent | [MOM](https://data.gov.sg/datasets/d_b0da22a41f952764376a2b7b5b0f2533/view) |
| avg_tbill_yield | Quarterly mean of monthly 1-year Treasury bill yields, percent | [MAS](https://data.gov.sg/datasets/d_5fe5a4bb4a1ecc4d8a56a095832e2b24/view) |
| gdp_growth | GDP year-on-year growth, chained 2015 dollars, percent | [DOS](https://data.gov.sg/datasets/d_caf9655a8faaf94c9eed5a2eb7a4b3f9/view) |

To rebuild, download the four CSV exports into `data/raw/` as `hdb.csv`, `unemployment.csv`, `interest.csv`, and `gdp.csv`, then run `python src/prepare_data.py`. Expected export formats: HDB has `month` and `resale_price`; macroeconomic files have `DataSeries` plus wide date columns. The script validates complete 2017–2024 coverage before saving a new snapshot and SQLite database. Raw files are ignored by Git. A source refresh may change estimates; rerun the notebook and review the interpretation afterward.

The HDB Resale Price Index is not a final-model input. It remains a useful robustness check because transaction means are sensitive to the mix of flats sold.
