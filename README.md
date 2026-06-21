# Airbnb Market Intelligence — Madrid · Lisbon · Barcelona

An end-to-end **data engineering + analytics** project built on the public
[Inside Airbnb](https://insideairbnb.com/) dataset. It takes raw, messy city
files all the way through a repeatable pipeline, a clean analytical warehouse,
rigorous statistics, a price model, and an interactive dashboard — plus a full
written report.

The project is framed around a real-world narrative spine: the short-term-rental
**regulation debate** (Barcelona's confirmed 2028 STR phase-out), which Inside
Airbnb itself exists to inform.

> **Status:** Complete. Pipeline, warehouse, EDA, statistics, model, AI layer,
> dashboard, and report are all built and reproducible.
> **Philosophy:** depth over breadth — a few sections done well, with honest,
> documented trade-offs, rather than every task skimmed.

---

## TL;DR — what's in here

| Area | What was built |
|------|----------------|
| **Pipeline** | Config-driven ingestion → verification → profiling → cleaning → DuckDB warehouse. Add a city by editing one YAML file, not the code. |
| **Warehouse** | A DuckDB **star schema** (`dim_listings`, `dim_hosts`, `fact_reviews`) as a single source of truth. |
| **Statistics** | Five hypotheses (H1–H5) tested with assumption checks and **effect sizes**, not just p-values. |
| **Modelling** | A price model comparing three families; the strongest is persisted and served to the dashboard. |
| **Applied AI** | An LLM property-type standardiser (structured JSON output) and a **RAG** assistant grounded in the project's own findings. |
| **Front end** | A Streamlit dashboard: live price estimator, market-concentration explorer, and the RAG Q&A. |
| **Report** | A ~23-page report with architecture + schema diagrams, all charts, and a full AI-usage disclosure. |

---

## Headline findings

- **Privacy premium (H1):** entire homes command a large, practically meaningful
  price premium over private rooms — Cohen's *d* ≈ **1.41** (computed on
  log-price, the correct transform for this skewed data).
- **Superhost signal (H2):** Superhosts earn meaningfully higher guest ratings —
  *d* ≈ **0.66** (medium-to-large). The badge is a reliable quality signal.
- **Hyper-local pricing (H4):** neighbourhood significantly drives price
  (ANOVA, *p* < 0.0001). City-wide averages hide the real story.
- **Supply concentration:** a small share of multi-listing, commercial-style
  hosts controls a large share of listings — the dynamic behind the regulation
  debate.
- **Price model:** explains ≈ **58%** of price variation (R² ≈ 0.58, MAE ≈ €48);
  non-linear models beat linear regression. Reported honestly — not overclaimed.

> A note on the cities: **Madrid (~76%)** and **Lisbon (~86%)** have full price
> coverage and carry every price-based analysis. **Barcelona's** snapshot had
> **0%** price coverage — a documented issue in the source. Rather than hide or
> fabricate, we scoped pricing to Madrid + Lisbon and re-purposed Barcelona to
> anchor the **regulatory and host-supply** story, where its data is complete.
> See [`DECISIONS.md`](DECISIONS.md) for the full reasoning.

---

## Architecture

```
                ┌─────────────┐
  Inside Airbnb │  download   │  config-driven: cities.yml decides which city
   (7 files /   │  + verify   │
    city)       └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   profile   │  data-quality report: row counts, null rates,
                │  + clean    │  price-coverage check, validation rules
                └──────┬──────┘
                       ▼
                ┌─────────────┐
                │   DuckDB    │  star schema — single source of truth
                │  warehouse  │  dim_listings · dim_hosts · fact_reviews
                └──────┬──────┘
            ┌──────────┼───────────┬───────────────┐
            ▼          ▼           ▼               ▼
        ┌───────┐  ┌───────┐  ┌─────────┐    ┌───────────┐
        │  EDA  │  │ stats │  │  price  │    │ applied AI │
        │ charts│  │ H1–H5 │  │  model  │    │ LLM + RAG  │
        └───┬───┘  └───┬───┘  └────┬────┘    └─────┬─────┘
            └──────────┴───────────┴───────────────┘
                       ▼
                ┌─────────────┐     ┌──────────────────┐
                │  Streamlit  │     │  written report  │
                │  dashboard  │     │   (PDF / DOCX)   │
                └─────────────┘     └──────────────────┘
```

A rendered version of this diagram (and the star-schema ER diagram) is in the
report under *Engineering Approach*.

---

## Project structure

```
airbnb-barcelona/
├── README.md                  # this file
├── DECISIONS.md               # running decision log — read this to follow the reasoning
├── requirements.txt
├── .streamlit/
│   └── config.toml            # dashboard config (file-watcher tuned for stability)
├── config/
│   └── cities.yml             # config-driven: switch/add cities here, no code changes
├── src/
│   ├── components/
│   │   ├── download_data.py   # fetches all 7 files for each configured city
│   │   ├── verify_data.py     # sanity-checks downloads before any analysis
│   │   ├── profile_data.py    # data-quality report (nulls, cardinality, coverage)
│   │   └── build_db.py        # cleans + loads the DuckDB star schema
│   ├── eda/
│   │   ├── run_eda_distributions.py
│   │   ├── run_eda_demand.py
│   │   ├── run_eda_geospatial.py
│   │   └── generate_eda_plots.py
│   ├── stats/
│   │   └── run_hypothesis_tests.py   # H1–H5 with effect sizes
│   ├── analytics/
│   │   ├── model_price.py     # trains + persists the price model
│   │   └── rag_engine.py      # embeddings → top-k retrieval → grounded generation
│   ├── dashboard/
│   │   └── app.py             # Streamlit front end
│   └── utils/
│       └── config.py          # project-root resolver + API setup
├── data/
│   ├── raw/                   # downloads land here (git-ignored)
│   ├── processed/             # cleaned outputs (git-ignored)
│   ├── airbnb_warehouse.db    # DuckDB warehouse (git-ignored; rebuilt by build_db.py)
│   ├── price_model.joblib     # persisted model (git-ignored)
│   └── price_model_meta.json  # model metrics (R², MAE, feature importances)
├── reports/                   # final report + exported figures/diagrams
└── notebooks/                 # exploratory notebooks
```

> If your local layout differs slightly (e.g. some scripts sit directly under
> `src/`), adjust the run commands below to match — the logic is identical.

---

## Setup

```bash
# 1. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt
```

**API key (for the LLM standardiser + RAG assistant).** These features call the
Gemini API. Set your key as an environment variable before running them:

```bash
export GEMINI_API_KEY="your-key-here"   # Windows (PowerShell): $env:GEMINI_API_KEY="your-key-here"
```

The pipeline, EDA, statistics, and price model run **without** a key — only the
AI layer and the dashboard's "Ask the AI" tab need it.

---

## How to run — end to end

Run in this order. Each step depends on the warehouse built by `build_db.py`.

```bash
# 1. Download all files for every city in config/cities.yml
python src/components/download_data.py

# 2. Verify the downloads (shapes, keys, data-quality quirks)
python src/components/verify_data.py

# 3. Profile the raw data — produces the data-quality report
python src/components/profile_data.py

# 4. Clean + load the DuckDB star schema (prints a price-coverage report at the end)
python src/components/build_db.py

# 5. Exploratory analysis — generates the charts used in the report
python src/eda/generate_eda_plots.py

# 6. Statistical hypothesis tests (H1–H5, with effect sizes)
python src/stats/run_hypothesis_tests.py

# 7. Train + persist the price model (writes price_model.joblib + meta.json)
python src/analytics/model_price.py

# 8. Launch the dashboard (price estimator, market explorer, RAG Q&A)
streamlit run src/dashboard/app.py
```

### If a download returns 404

Inside Airbnb publishes **quarterly point-in-time snapshots**, so links rotate.
Open the [Get the Data](https://insideairbnb.com/get-the-data/) page, copy the
current link for the city, and update `snapshot_date` (and the region slug if
needed) in `config/cities.yml`. Note Inside Airbnb uses local-language region
slugs — e.g. Madrid is `comunidad-de-madrid`, **not** `community-of-madrid`.

---

## Review order — what to look at first

For an evaluator, the fastest path through the work:

1. **The report** (`reports/`) - the primary artifact; reads top to bottom and
   covers every section with business interpretation.
2. **`DECISIONS.md`** - the reasoning behind scope, the city pivot, and the
   Barcelona price-gap call. This is where the engineering judgement lives.
3. **The dashboard** (`streamlit run src/dashboard/app.py`) — the work made
   interactive; the price estimator is wired to the real trained model.
4. **`src/components/build_db.py`** - the heart of the pipeline (cleaning,
   validation, star-schema load, price-coverage report).
5. **`src/stats/run_hypothesis_tests.py`** - H1–H5 with effect sizes.

---

## Tech stack

**Language:** Python · **Warehouse:** DuckDB (star schema) ·
**Analysis:** pandas, scipy / statsmodels · **Viz:** matplotlib / seaborn,
plotly · **ML:** scikit-learn · **Applied AI:** Gemini API (LLM standardiser +
RAG), sentence-transformers for retrieval · **App:** Streamlit ·
**Config:** YAML · **Version control:** Git.

---

## Data honesty & limitations

This project deliberately states what it does **not** claim:

- **Occupancy is estimated, not measured.** Inside Airbnb has no booking
  records, so any occupancy/revenue figure is an inference and is treated as
  such, never as ground truth.
- **Snapshots, not a live feed.** The data is a periodic scrape — good for
  structural patterns, not real-time decisions.
- **The price model is not a crystal ball.** Explaining ≈58% of price is solid
  for this domain; the rest is human factors no dataset captures.
- **Gaps are named, not hidden.** Barcelona's missing prices, any
  deprioritised sections, and every AI tool used are disclosed openly (see the
  report's AI-usage appendix and `DECISIONS.md`).

---

## AI usage

AI tools were used during development and are **fully disclosed** in the report's
*AI Usage Disclosure* appendix — tools and versions, which parts were
AI-assisted, key prompts, how outputs were validated, and where suggestions were
rejected or substantially changed.

---

## License & attribution

Source data © Inside Airbnb, used under a
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)
license. This repository contains analysis and code; raw data is git-ignored and
must be downloaded via the pipeline above.