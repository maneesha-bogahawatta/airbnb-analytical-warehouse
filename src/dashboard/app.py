"""Airbnb Market Intelligence Dashboard.

Three real, working capabilities -- nothing simulated:
  1. Price estimator -- loads the trained Random Forest from model_price.py
     and runs an actual prediction. No inline arithmetic, no invented
     coefficients.
  2. Market structure -- host concentration and the room-type price premium,
     computed directly from the warehouse.
  3. Ask the Analyst -- the project's real RAG pipeline (MiniLM embeddings +
     top-k retrieval + grounded LLM generation), not keyword matching.

Run with: streamlit run app.py
"""
import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
import json
import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# PROJECT ROOT RESOLUTION
# -----------------------------------------------------------------------------
# Streamlit does NOT automatically add the project root to sys.path the way
# `python -m` does -- it only sees the folder app.py itself sits in. Since
# app.py lives at src/dashboard/app.py (two levels deep), the bare
# `from src.analytics... import ...` below fails with
# "ModuleNotFoundError: No module named 'src'" unless we add the real
# project root (the folder CONTAINING src/) to sys.path ourselves first.
# Same root-finding pattern used in download_data.py / verify_data.py.
def _find_project_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "src").is_dir() and (p / "config").is_dir():
            return p
    raise FileNotFoundError(
        "Could not locate project root (a folder containing both 'src/' and "
        "'config/') above this file. Run streamlit from inside the project, "
        "or move app.py back under the project root."
    )

PROJECT_ROOT = _find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Reuses the project's own RAG module (Section 7.3 of the report) -- the
# dashboard does not reimplement retrieval logic.
from src.analytics.rag_engine import get_retrieved_context_with_sources, load_chunks
from src.utils.config import setup_gemini

# -----------------------------------------------------------------------------
# PAGE CONFIG & LIGHT STYLING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Airbnb Market Intelligence", page_icon="🏠", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.7rem; }
    .data-caveat {
        background-color: #FFF4E5;
        border-left: 4px solid #E8A33D;
        padding: 0.6rem 0.9rem;
        border-radius: 4px;
        font-size: 0.9rem;
        margin: 0.6rem 0;
        color: #4A3B1F !important;
    }
    .data-caveat * { color: #4A3B1F !important; }
</style>
""", unsafe_allow_html=True)

st.title("Airbnb Market Intelligence")
st.caption("Madrid · Lisbon · Barcelona  —  built on Inside Airbnb open data")
st.divider()

# -----------------------------------------------------------------------------
# DATA & MODEL LOADING
# -----------------------------------------------------------------------------
# 🌟 CLOUD DATABASE CONNECTION LOGIC 🌟
# If deployed to Streamlit Cloud, it uses the MotherDuck Secret.
# If running locally, it gracefully falls back to the local .db file.
if "MOTHERDUCK_TOKEN" in st.secrets:
    # We added airbnb_warehouse right after md:
    DB_PATH = f"md:airbnb_warehouse?motherduck_token={st.secrets['MOTHERDUCK_TOKEN']}"
else:
    DB_PATH = str(PROJECT_ROOT / "data" / "airbnb_warehouse.db")

# Force Streamlit to look from the absolute root of the repository
MODEL_PATH = Path.cwd() / "data" / "price_model.joblib"
META_PATH = Path.cwd() / "data" / "price_model_meta.json"
KNOWLEDGE_PATH = str(PROJECT_ROOT / "data" / "knowledge" / "insights.md")

@st.cache_data
def load_listings():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT l.city, l.room_type, l.price, l.review_rating, l.accommodates,
               l.bedrooms, l.neighbourhood_id, h.host_id, h.is_superhost
        FROM dim_listings l
        JOIN dim_hosts h ON l.host_id = h.host_id
        WHERE l.is_current = TRUE
    """).df()
    con.close()
    return df

@st.cache_resource
def load_price_model():
    if not MODEL_PATH.exists():
        return None, None
    bundle = joblib.load(MODEL_PATH)
    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
    return bundle, meta

@st.cache_data
def load_regulatory():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("""
        SELECT l.city, l.regulatory_status, l.license, l.room_type, h.host_id
        FROM dim_listings l
        JOIN dim_hosts h ON l.host_id = h.host_id
        WHERE l.is_current = TRUE
    """).df()
    con.close()
    return df

@st.cache_resource
def load_rag_resources():
    chunks = load_chunks(KNOWLEDGE_PATH)
    genai = setup_gemini()
    model = genai.GenerativeModel("models/gemini-3.5-flash")
    return chunks, model

try:
    df = load_listings()
    reg_df = load_regulatory()
except Exception as e:
    st.error(f"Could not load the warehouse. Confirm data/airbnb_warehouse.db exists and build_db.py has been run. Details: {e}")
    st.stop()

price_bundle, price_meta = load_price_model()

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.header("Market")
city_options = sorted(c.capitalize() for c in df["city"].unique())
selected_city_label = st.sidebar.selectbox("City", city_options)
selected_city = selected_city_label.lower()

city_df = df[df["city"] == selected_city]
priced_df = city_df[(city_df["price"] > 0) & (city_df["price"].notna())]
has_pricing = len(priced_df) > 0

st.sidebar.metric("Listings in view", f"{len(city_df):,}")
if has_pricing:
    st.sidebar.metric("Median nightly price", f"€{priced_df['price'].median():.0f}")
st.sidebar.metric("Median rating", f"{city_df['review_rating'].median():.2f} / 5.0" if city_df["review_rating"].notna().any() else "N/A")

if not has_pricing:
    st.sidebar.markdown(
        '<div class="data-caveat">No price data for this city in the current snapshot '
        '(documented source-data gap — see report §8.2). Pricing-dependent tabs are disabled below.</div>',
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Price Estimator", "Market Structure", "Privacy Premium", "Ask the Analyst", "Regulatory Risk"
])

# ============================================================ TAB 1: PRICE ESTIMATOR
with tab1:
    st.subheader(f"Price Estimator — {selected_city_label}")

    if price_bundle is None:
        st.error("No trained model found. Run `python3 model_price.py` to train and save it before using this tab.")
    elif not has_pricing:
        st.error(f"{selected_city_label} has no price data in this snapshot, so it was excluded from model training. "
                  "Try Madrid or Lisbon, which the model was trained on.")
    elif selected_city not in price_meta.get("cities_used", []):
        st.warning(f"The trained model was not fit on {selected_city_label} data. Predictions for this city are not available.")
    else:
        st.caption("Estimate driven by the project's trained Random Forest model "
                    f"(test R² = {price_meta['r2']:.2f}, mean error ≈ €{price_meta['mae_eur']:.0f}). "
                    "This is the same model evaluated in the report, Section 7.1 — not a separate formula.")

        c1, c2, c3 = st.columns(3)
        with c1:
            room_type = st.selectbox("Room type", options=price_meta["room_types"])
        with c2:
            accommodates = st.slider("Guests", 1, 16, 2)
        with c3:
            bedrooms = st.slider("Bedrooms", 0, 10, 1)

        nbhd_options = [n for n in price_meta["neighbourhood_ids"] if n.startswith(selected_city)]
        neighbourhood = st.selectbox(
            "Neighbourhood (optional — leave as 'Citywide average' to ignore location)",
            options=["Citywide average"] + nbhd_options
        )

        model = price_bundle["model"]
        feature_cols = price_bundle["feature_cols"]

        row = {c: 0 for c in feature_cols}
        if "accommodates" in row: row["accommodates"] = accommodates
        if "bedrooms" in row: row["bedrooms"] = bedrooms
        rt_col = f"room_type_{room_type}"
        if rt_col in row: row[rt_col] = 1
        city_col = f"city_{selected_city}"
        if city_col in row: row[city_col] = 1
        if neighbourhood != "Citywide average":
            nb_col = f"neighbourhood_id_{neighbourhood}"
            if nb_col in row: row[nb_col] = 1

        X = pd.DataFrame([row])[feature_cols]
        pred_log = model.predict(X)[0]
        pred_eur = float(np.expm1(pred_log))
        mae = price_meta["mae_eur"]

        st.markdown("####")
        m1, m2 = st.columns([1, 1])
        with m1:
            st.metric("Estimated nightly rate", f"€{pred_eur:.0f}",
                       help=f"Model mean absolute error on held-out test data is ±€{mae:.0f}.")
        with m2:
            st.metric("Typical range", f"€{max(pred_eur - mae, 0):.0f} – €{pred_eur + mae:.0f}")

        st.caption(
            "This is a model estimate based on structural features only (room type, capacity, "
            "neighbourhood, city) — it does not account for amenities, photos, seasonality, "
            "or host reputation. See report Section 7.1 for full model details and honest "
            "performance framing."
        )

# ============================================================ TAB 2: MARKET STRUCTURE
with tab2:
    st.subheader(f"Host Concentration — {selected_city_label}")

    host_counts = city_df.groupby("host_id").size().reset_index(name="listings_owned")
    total_listings = len(city_df)
    top_1pct_n = max(1, int(len(host_counts) * 0.01))
    top_hosts = host_counts.nlargest(top_1pct_n, "listings_owned")
    market_share = (top_hosts["listings_owned"].sum() / total_listings) * 100 if total_listings else 0

    st.info(f"The top 1% of hosts by listing count control **{market_share:.1f}%** "
            f"of all active listings in {selected_city_label}.")

    host_counts["host_type"] = np.select(
        [host_counts["listings_owned"] >= 10, host_counts["listings_owned"] >= 3],
        ["Commercial (10+ listings)", "Multi-listing (3–9 listings)"],
        default="Single listing (1–2)"
    )
    pie_data = host_counts.groupby("host_type")["listings_owned"].sum().reset_index()
    pie_data = pie_data.rename(columns={"listings_owned": "Listings"})

    fig = px.pie(pie_data, values="Listings", names="host_type", hole=0.45,
                 color_discrete_sequence=["#2E5C8A", "#5B9BD5", "#A9CCE3"])
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, width='stretch')

    st.caption("Host-scale tiers follow the same classification used in the report's "
               "supply-concentration analysis (Section 5.4).")

# ============================================================ TAB 3: PRIVACY PREMIUM
with tab3:
    st.subheader(f"Entire Home vs. Private Room — {selected_city_label}")

    if not has_pricing:
        st.error(f"Pricing comparisons are unavailable for {selected_city_label} due to missing price data in this snapshot.")
    else:
        clean = priced_df[priced_df["price"] < 1000]
        entire_home = clean[clean["room_type"] == "Entire home/apt"]["price"].median()
        private_room = clean[clean["room_type"] == "Private room"]["price"].median()

        if pd.notna(private_room) and private_room > 0 and pd.notna(entire_home):
            premium_pct = ((entire_home - private_room) / private_room) * 100
            st.success(
                f"Guests in {selected_city_label} pay a **{premium_pct:.0f}% premium** "
                f"for an entire home (€{entire_home:.0f} median) over a private room (€{private_room:.0f} median)."
            )
            st.caption("This matches H1 in the report (Section 6.1): the room-type price gap is the "
                       "single strongest pricing relationship found in the project (Cohen's d = 1.41, large effect).")

        plot_df = clean[clean["room_type"].isin(["Entire home/apt", "Private room"])]
        fig2 = px.box(plot_df, x="room_type", y="price", color="room_type",
                      labels={"price": "Nightly price (€)", "room_type": "Room type"},
                      color_discrete_sequence=["#2E5C8A", "#5B9BD5"])
        fig2.update_yaxes(range=[0, 400])
        fig2.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig2, width='stretch')

# ============================================================ TAB 4: ASK THE ANALYST (REAL RAG)
with tab4:
    st.subheader("Ask the Analyst")
    st.caption(
        "Answers are generated only from this project's verified findings (EDA results, "
        "hypothesis tests, model performance, documented data limitations) — retrieved "
        "via semantic search, then synthesised by an LLM. If something isn't in the "
        "project's findings, it will say so rather than guess."
    )

    try:
        chunks, gen_model = load_rag_resources()
        rag_ready = True
    except Exception as e:
        rag_ready = False
        st.error(f"RAG system unavailable: {e}. Confirm GEMINI_API_KEY is set and "
                 "data/knowledge/insights.md exists.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "sources": [], "content": "Ask me anything about the analysis — "
             "for example: “Why is there no pricing data for Barcelona?” or "
             "“What drives price the most?”"}
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and message.get("sources"):
                with st.expander(f"📚 Sources ({len(message['sources'])} section"
                                  f"{'s' if len(message['sources']) != 1 else ''} retrieved)"):
                    for s in message["sources"]:
                        st.markdown(f"**{s['title']}** ·  relevance {s['score']:.2f}")
                        st.caption(s["text"][:300] + ("..." if len(s["text"]) > 300 else ""))
                        st.markdown("---")

    if prompt := st.chat_input("Ask a question about the data or findings..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})

        with st.chat_message("assistant"):
            if not rag_ready:
                response = "The RAG system isn't configured in this session, so I can't retrieve a grounded answer right now."
                sources = []
                st.markdown(response)
            else:
                with st.spinner("Searching project findings..."):
                    context, sources = get_retrieved_context_with_sources(
                        prompt, chunks, top_k=4, threshold=0.3
                    )
                    if context is None:
                        response = ("I couldn't find anything relevant to that in this project's "
                                    "findings. Try asking about pricing drivers, the Barcelona data "
                                    "gap, host concentration, or the hypothesis test results.")
                    else:
                        full_prompt = (
                            "Answer the following question using only the context provided. "
                            "If it's not in the context, say you don't know.\n\n"
                            f"Context: {context}\n\nQuestion: {prompt}"
                        )
                        result = gen_model.generate_content(full_prompt)
                        response = result.text
                st.markdown(response)

                if sources:
                    with st.expander(f"📚 Sources ({len(sources)} section{'s' if len(sources) != 1 else ''} retrieved)"):
                        for s in sources:
                            st.markdown(f"**{s['title']}** ·  relevance {s['score']:.2f}")
                            st.caption(s["text"][:300] + ("..." if len(s["text"]) > 300 else ""))
                            st.markdown("---")

        st.session_state.messages.append({"role": "assistant", "content": response, "sources": sources})

# ============================================================ TAB 5: REGULATORY RISK
with tab5:
    st.subheader(f"Regulatory Exposure — {selected_city_label}")

    city_reg = reg_df[reg_df["city"] == selected_city]
    total = len(city_reg)
    unlicensed = (city_reg["regulatory_status"] == "Unlicensed / Missing").sum()
    unlicensed_pct = (unlicensed / total * 100) if total else 0

    if selected_city == "barcelona":
        st.markdown(
            '<div class="data-caveat">Barcelona has confirmed it will not renew any tourist-use '
            'licences, phasing out all of the roughly 10,000 currently licensed listings by '
            'November 2028 (upheld by Spain’s Constitutional Court, March 2025). The figures '
            'below show how many active listings are already operating outside that licensing '
            'system today, ahead of the phase-out — see report Section 5.5 and 8.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption("Regulatory registration status for active listings in this market.")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.metric("Active listings", f"{total:,}")
    with r2:
        st.metric("Unlicensed / missing licence", f"{unlicensed:,}")
    with r3:
        st.metric("Share unlicensed", f"{unlicensed_pct:.1f}%")

    status_counts = city_reg["regulatory_status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig5 = px.bar(status_counts, x="status", y="count", color="status",
                  color_discrete_map={
                      "License Registered": "#1F7A3D",
                      "Unlicensed / Missing": "#B8492F",
                  },
                  labels={"status": "Registration status", "count": "Listings"})
    fig5.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig5, width='stretch')

    st.markdown("##### Unlicensed listings by room type")
    unlicensed_by_type = (
        city_reg[city_reg["regulatory_status"] == "Unlicensed / Missing"]
        ["room_type"].value_counts().reset_index()
    )
    unlicensed_by_type.columns = ["room_type", "count"]
    if len(unlicensed_by_type):
        fig6 = px.bar(unlicensed_by_type, x="room_type", y="count",
                      color_discrete_sequence=["#B8492F"],
                      labels={"room_type": "Room type", "count": "Unlicensed listings"})
        fig6.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig6, width='stretch')
    else:
        st.caption("No unlicensed listings found in this breakdown.")

    st.caption(
        "“Unlicensed / Missing” combines listings with no licence number on file and those "
        "explicitly marked exempt or blank in the source data. See report §3.2 for the exact "
        "field definition and §5.5 for the full cross-city comparison."
    )