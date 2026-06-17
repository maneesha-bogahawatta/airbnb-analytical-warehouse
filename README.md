# Barcelona Airbnb Market Analysis

A data engineering + analytics project on the [Inside Airbnb](https://insideairbnb.com/)
Barcelona dataset (snapshot **2025-12-14**), framed around the city's confirmed
2028 short-term-rental phase-out.

> **Status:** Step 1 — data acquisition & verification.

## Project structure

```
airbnb-barcelona/
├── README.md              # this file
├── DECISIONS.md           # running decision log (read this to follow the reasoning)
├── requirements.txt
├── config/
│   └── cities.yml         # config-driven: switch cities here, no code changes
├── src/
│   ├── download_data.py   # fetches all 7 files for the active city
│   └── verify_data.py     # sanity-checks the download before any analysis
├── data/
│   ├── raw/               # downloads land here (git-ignored)
│   └── processed/         # cleaned outputs (git-ignored)
└── notebooks/
```

## Setup

```bash
# 1. (recommended) create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. install step-1 dependencies
pip install -r requirements.txt
```

## Run — Step 1

```bash
# Download all seven Barcelona files into data/raw/barcelona/
python src/download_data.py

# Verify the download (shapes, keys, data-quality quirks)
python src/verify_data.py
```

If a download returns **404**, the quarterly snapshot date has likely changed.
Open the [Get the Data](https://insideairbnb.com/get-the-data/) page, copy the
real link for Barcelona, and update `snapshot_date` in `config/cities.yml`.

## What's next

Once verification passes: build the ingestion + profiling pipeline (data-quality
report), then cleaning/standardisation, then the DuckDB star schema — see
`DECISIONS.md` for scope and rationale.
