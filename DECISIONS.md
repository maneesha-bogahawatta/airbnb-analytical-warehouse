# Decision Log

> A running record of every significant choice and its rationale. The assignment
> states this is where interviewers focus most. Keep entries short: what you
> considered, what you chose, what trade-off you accepted.

---

### D1 — City selection
**Date:** 2026-06-17
**Decision:** Analyse **Barcelona** (Inside Airbnb snapshot **2025-12-14**) as the primary deep-dive city.
**Options considered:** New York City, Lisbon (+Porto), Barcelona.
**Why Barcelona:**
- It is a *functioning, data-rich market living under a confirmed phase-out* — the
  city has voted not to renew its ~10,000 tourist-apartment licences, all expiring
  by November 2028 (upheld by Spain's Constitutional Court, March 2025). This gives
  the whole report a real narrative spine tied to Inside Airbnb's housing mission.
- Mid-size and tractable for a one-week, single-laptop analysis (vs. the very large
  London/NYC calendar files).
- Clean neighbourhood structure (districts) for spatial analysis and ANOVA.
**Trade-off accepted:** Less globally iconic than NYC, and the Spanish/Catalan
neighbourhood names need careful, consistent handling.
**Scope decision:** Start with one city end-to-end. Only add a second city *after*
the full pipeline + report sections for Barcelona are complete and ≥2 days remain.
(Superseded in practice — see D6, D9.)

---

### D2 — Project scaffold & tech stack
**Date:** 2026-06-17
**Decision:** Config-driven Python pipeline: `config/cities.yml` defines every city
(country/region/slug/snapshot date/file list), so adding a city is a config edit, not
a code change. DuckDB for the warehouse (lightweight, SQL, no server), pandas/Polars
for profiling, scipy/statsmodels for statistics.
**Options considered:** Hardcoded per-city scripts vs. config-driven pipeline;
Postgres vs. DuckDB.
**Why:** A config-driven design directly answers the assignment's "process any city
with minimal changes" requirement, and was cheap to set up on day one. DuckDB needs
no server setup and handles the calendar-scale files comfortably on a laptop.
**Trade-off accepted:** Slightly more upfront scaffolding time vs. just hardcoding
Barcelona paths everywhere.

---

### D3 — Dataset familiarization split: factual vs. judgment
**Date:** 2026-06-17
**Decision:** Auto-generate the factual schema documentation (`profile_data.py` →
`schema_<city>.md`: column types, null rates, ranges, key relationships) rather than
hand-typing it. Keep a separate, manually-written `dataset_familiarization.md` for
business interpretation, assumptions on ambiguous fields, and documented limitations.
**Why:** A script is faster and more accurate for facts and is fully reproducible;
the judgment calls (what `availability_365` actually means, how to treat
`minimum_nights >= 31`, etc.) require a human and are what the rubric grades.
**Trade-off accepted:** Two documents to maintain instead of one combined file.

---

### D4 — Barcelona price field: 100% null (first discovery)
**Date:** 2026-06-18
**Decision:** Confirmed via `profile_data.py` output that `price` is null in 100% of
rows across all three Barcelona files (detailed listings, summary listings, and all
~6.6M calendar rows) for the 2025-12-14 snapshot. This is a documented scrape
limitation, not a parsing bug — verified independently via raw-file inspection.
**Options considered:** (a) source an archived Barcelona snapshot with price intact,
(b) switch primary city to Madrid (which has working prices), (c) proceed without
price and scope pricing analysis elsewhere.
**Decision at this stage:** Pursue (a) first — least disruptive to the existing
narrative. Built `find_priced_snapshot.py` to screen archived snapshot dates for
populated price before committing to a fix.
**Explicitly rejected:** Live-scraping current Airbnb prices to backfill the gap.
Rejected because it violates the assignment's "Inside Airbnb data only" requirement,
breaches Airbnb's terms of service, and would mix today's live prices into a
December-2025 snapshot — methodologically invalid regardless of convenience.

---

### D5 — Star schema design (`build_db.py`)
**Date:** 2026-06-18
**Decision:** DuckDB warehouse with `dim_listings`, `dim_hosts`, `dim_neighbourhoods`,
`fact_reviews`, all keyed by an explicit `city` column so every table supports
multi-city queries via `GROUP BY city` with no per-city code branches.
**Why:** A proper dimensional model (vs. one flat per-city table) keeps EDA and
statistics scripts city-agnostic — adding a city later requires zero changes to
downstream analysis code, only a config + rebuild.
**Trade-off accepted:** More upfront DDL design work than a flat CSV-per-city
approach.

---

### D6 — Madrid added as a second city
**Date:** 2026-06-19
**Decision:** Add Madrid to the warehouse to ensure at least one fully-priced city
was available while the Barcelona price issue was being resolved.
**Issue found:** Initial manual Madrid download was capped at exactly 25,000 rows
(round-number red flag) and used an incorrect region slug
(`community-of-madrid`). Re-downloaded through the official pipeline using the
correct Spanish slug (`comunidad-de-madrid`). Cross-verified the final row count
(still 25,000) independently via pandas (which parses multi-line quoted fields
correctly) and the summary `listings.csv` — both agreed at 25,000, confirming this
is genuinely Madrid's snapshot size, not a truncation artifact.
**Why this matters:** Demonstrates the discipline of verifying a suspicious number
rather than assuming the worst or assuming it's fine — both checked independently
before trusting the figure.
**Trade-off accepted:** Time spent on data verification instead of analysis, but
necessary — an unverified capped file would have invalidated every downstream price
result.

---

### D7 — Lisbon added as a third city
**Date:** 2026-06-20
**Decision:** Add Lisbon (snapshot 2026-03-26) as a third city, confirmed via
`curl` to have a valid Inside Airbnb path before committing, and verified to have
86% price coverage (24,950 listings, only 13.96% null) — the best price coverage of
any city in the project.
**Options considered:** (a) accept Barcelona's price gap and run a two-city
(Barcelona regulatory-only / Madrid pricing) analysis, (b) add a third priced city
to keep a genuine multi-city pricing comparison.
**Why Lisbon:** Real region slug confirmed independently before download (avoided
repeating the Madrid slug mistake). Strong price coverage. Distinct but related
regulatory backdrop (Portuguese STR policy) that complements Barcelona's narrative
without duplicating it.
**Trade-off accepted:** More data-engineering time invested versus simply accepting
the two-city scope — judged worthwhile because it preserves a genuine multi-city
pricing comparison rather than relying on a single priced city.
**Explicitly avoided:** A suggested "mask the gap" framing that treated adding a
city as hiding Barcelona's missing data rather than addressing it. Rejected this
framing — the addition is documented and scoped transparently in D9, not used to
obscure the limitation.

---

### D8 — `build_db.py` schema fix (`is_current` / SCD2 columns)
**Date:** 2026-06-19
**Decision:** Added `valid_from`, `valid_to`, `is_current` columns to the
`dim_listings` DDL and populated them on load (`is_current = TRUE`).
**Issue found:** Three EDA scripts (`run_eda_distributions.py`, `run_eda_demand.py`,
`run_eda_geospatial.py`) filtered on `WHERE is_current = TRUE`, a column that did not
exist in the original table definition — causing silent query failures.
**Why:** Rather than removing the filter from each script, fixed the schema to
actually support the SCD Type 2 pattern those scripts (and `scd2_listings_update.py`)
were designed around, since that pattern is also a deliberate §3.6 engineering
demonstration.
**Trade-off accepted:** A warehouse rebuild was required after the fix.

---

### D9 — Final pricing scope: Madrid + Lisbon; Barcelona retained for regulatory analysis
**Date:** 2026-06-21
**Decision:** Confirmed via direct warehouse query that Barcelona price remains
0/18,177 populated in the final build (`madrid 25,000/18,953 priced`,
`barcelona 18,177/0 priced`, `lisbon 24,950/21,466 priced`). All pricing-dependent
analysis (H1, H3, H5 hypothesis tests, the ML price model, geographic price
gradients) is scoped to **Madrid and Lisbon only**. Barcelona is retained for
analyses independent of price: licensing/regulatory status, host concentration,
room-type mix, and review activity — directly supporting the project's regulatory
narrative (the 2028 licence phase-out from D1).
**Options considered:** (1) keep sourcing archived Barcelona snapshots indefinitely,
(2) add Lisbon and scope pricing to Madrid+Lisbon (adopted, see D7), (3) drop
Barcelona entirely and make Madrid the primary city.
**Why this option:** Preserves the regulatory narrative that gives the project its
spine (D1) while keeping pricing analysis honest and fully supported by real data
in two cities, rather than forcing a three-way price comparison the data cannot
support.
**Trade-off accepted:** No three-city price comparison is possible. Mitigated by
Barcelona carrying real, distinct analytical weight on the non-price dimensions.

---

### D10 — H5 hypothesis revised: calendar-based seasonality deprioritized
**Date:** 2026-06-21
**Decision:** Original H5 (weekday vs. weekend pricing) required ingesting
`calendar.csv.gz` across three cities (~15-20M+ rows). Deprioritized given remaining
project time and replaced with a capacity-price correlation analysis
(`accommodates` vs. log-price by city) using data already validated in the
warehouse.
**Why:** The capacity-price relationship is a real, defensible hypothesis answerable
with zero new ingestion risk, and it corroborates the ML model's top feature
(`accommodates`) from a different angle (§5 vs. §6 of the report).
**Trade-off accepted:** The original seasonality question goes unanswered. Noted
explicitly as Future Work rather than silently dropped.

---

### D11 — Statistical reporting standard: effect size over p-value
**Date:** 2026-06-21
**Decision:** Every hypothesis test reports an effect size (Cohen's d for two-group
comparisons, eta-squared for ANOVA) alongside the p-value, and the effect size — not
the p-value — drives the business interpretation.
**Why:** With sample sizes in the tens of thousands, p-values shrink toward zero for
almost any nonzero difference, making "p < 0.05" alone a poor signal of practical
importance. H3 is the clearest example: p = 1.9e-08 but Cohen's d = 0.06
(negligible) — a statistically "significant" result with no real-world meaning,
deliberately contrasted against H1's large effect (d = 1.41) in the report.
**Trade-off accepted:** More complex statistical code (custom Cohen's d / eta-squared
calculations) versus just reporting p-values, but necessary for statistically honest
conclusions.