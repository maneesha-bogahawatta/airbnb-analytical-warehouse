# Airbnb Market Intelligence: Key Insights

## 1. Data Engineering & Standardization
* **Standardization Strategy**: The raw dataset contained over 100 highly granular property types (e.g., "Private room in cave", "Treehouse", "Shipping container").
* **Harmonization**: We implemented an LLM-based standardization pipeline to map all raw types into four canonical categories: ['Entire Home', 'Private Room', 'Shared Room', 'Other'].
* **Impact**: This drastically reduced data noise, allowing downstream models to identify broader market trends rather than overfitting on rare or idiosyncratic property types.

## 2. Multi-City Market Driver Analysis
* **Primary Pricing Drivers**: Across the combined Madrid and Lisbon markets, 'accommodates' (capacity) and 'bedrooms' remain the strongest predictors of price.
* **Market-Specific Dynamics**: City location itself is a top-tier price driver, validating the decision to pool markets while using dummy variables to capture city-specific intercepts.
* **Geospatial Granularity**: Specific neighbourhood identifiers consistently emerge as significant factors in feature importance, indicating that pricing power is highly hyper-local.

## 3. Statistical Hypothesis Testing (Final, Verified Results)

All tests were run on log-transformed price to correct for right-skew. Effect sizes
(Cohen's d for two-group comparisons, eta-squared for ANOVA) are reported alongside
p-values, since p-values alone are misleading at this sample size (n in the tens of
thousands) — almost any difference becomes "significant" by p-value, so effect size is
what determines whether a finding is practically meaningful.

* **H1 — Privacy Premium (Entire Home vs. Private Room)**: p < 0.0001, **Cohen's d = 1.41
  (large effect)**. Entire-home listings command a substantial and practically meaningful
  price premium over private rooms. This is the strongest pricing driver identified in
  the project.

* **H2 — Superhost Rating Premium**: p < 0.0001, **Cohen's d = 0.66 (medium-to-large
  effect)**. Superhost status is associated with a meaningfully higher guest rating,
  supporting its use as a real quality signal rather than a purely cosmetic badge.

* **H3 — Review Volume Impact on Price**: p = 1.92e-08, **Cohen's d = 0.06 (negligible
  effect)**. High-review-volume listings (≥10 reviews, n=25,095) and low-review-volume
  listings (<10 reviews, n=15,324) differ in mean log-price by less than 0.02 — a
  practically trivial gap despite the statistically significant p-value. **This is a
  deliberate contrast with H1**: it demonstrates that statistical significance and
  practical significance are not the same thing. At this sample size, p-values shrink
  toward zero for almost any nonzero difference, so effect size — not p-value — is the
  correct basis for a business conclusion. The practical takeaway: hosts do not appear
  to price based on accumulated review volume; price is set by structural factors
  (room type, capacity, location) rather than reputation.

* **H4 — Neighbourhood Price Variance (ANOVA)**: p < 0.0001, **eta-squared = 0.146**.
  Neighbourhood identity explains approximately 14.6% of price variance — a real and
  moderate effect, confirming hyper-local pricing dynamics, but not the dominant driver
  of price (consistent with §2: capacity/bedrooms outrank location in the ML model).

* **H5 — Capacity-Price Relationship by City** *(revised scope, see Data Limitations)*:
  Pearson correlation between `accommodates` and log-price — Madrid: r = 0.575
  (p < 0.0001, n=18,953); Lisbon: r = 0.634 (p < 0.0001, n=21,466). Both cities show a
  moderate-to-strong positive relationship between capacity and price, corroborating
  `accommodates` as a top feature-importance driver in the ML model (§2).

## 4. Data Limitations & Scope Decisions

* **Barcelona Pricing Gap**: The Barcelona snapshot used in this project has 0 of 18,177
  listings with a populated `price` field (verified via direct warehouse query,
  2026-06-21: `madrid 25,000 total / 18,953 priced`, `barcelona 18,177 total / 0 priced`,
  `lisbon 24,950 total / 21,466 priced`). This is a documented data-quality issue in the
  source scrape, not a processing error. **All pricing-dependent analysis (H1, H3, H5,
  the ML price model) is therefore scoped to Madrid and Lisbon.** Barcelona is retained
  in the project for analyses that do not depend on price: licensing/regulatory status,
  host concentration, room-type mix, and review activity — which directly support the
  project's regulatory narrative (Barcelona's confirmed 2028 short-term-rental
  licence phase-out).
* **H5 Scope Revision**: H5 was originally scoped to test weekday-vs-weekend pricing
  using the calendar dataset (~15-20M+ rows across three cities). Given the ingestion
  cost and remaining project time, this was deprioritized in favour of a capacity-price
  analysis using already-validated warehouse data. The calendar-based seasonality
  question is noted as Future Work.
* **Pricing Ceiling**: A price cap was applied to remove extreme outliers, focusing the
  analysis on standard short-term rental market segments rather than luxury outliers.
* **Occupancy & Revenue**: Inside Airbnb contains no actual booking data; any
  occupancy/demand reasoning in this project (e.g., review volume as a demand proxy) is
  an estimate, not a direct measurement.

## 5. Technical Disclosure
* **LLM-Assisted Standardization**: Property-type harmonization was performed using a
  programmatic LLM mapping pipeline (Gemini), with distinct values mapped to canonical
  categories, parsed as structured JSON, and validated against an allowed-category list
  before being joined back to the warehouse.
* **Retrieval-Augmented Generation**: A RAG system over this insights document was built
  using local MiniLM sentence embeddings, cosine-similarity top-k retrieval over
  heading-chunked content, and grounded generation (Gemini) with an explicit
  "answer only from context, else say you don't know" instruction.