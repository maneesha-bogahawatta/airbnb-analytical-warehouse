import streamlit as st
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Multi-Market Analytical Hub", layout="wide")
st.title("📊 Airbnb Multi-Market Dynamic Analytical Dashboard")

# Connect cleanly to the shared warehouse file
def get_warehouse_data():
    conn = duckdb.connect("data/airbnb_warehouse.db", read_only=True)
    df = conn.execute("""
        SELECT city, room_type, review_rating, price 
        FROM dim_listings 
        WHERE review_rating IS NOT NULL;
    """).df()
    conn.close()
    return df

try:
    df = get_warehouse_data()

    # Sidebar Interactive Filter Control Panel
    st.sidebar.header("Filter Control Center")
    selected_city = st.sidebar.selectbox("Select Target Metropolitan Market", options=df['city'].unique() if not df.empty else ["No Data Available"])

    # Subset slicing execution
    filtered_df = df[df['city'] == selected_city]

    # Layout Matrix Metrics Cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Active Monitored Properties", value=f"{len(filtered_df):,}")
    with col2:
        st.metric(label="Mean Historical Review Score", value=f"{filtered_df['review_rating'].mean():.2f} ⭐" if len(filtered_df) > 0 else "N/A")

    # Interactive Visualizations Section
    st.subheader(f"Consumer Rating Layout Distributions: {selected_city.upper()}")
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(data=filtered_df, x="review_rating", hue="room_type", multiple="stack", binwidth=0.1, ax=ax)
        plt.xlabel("Review Rating Score")
        plt.ylabel("Asset Properties Count")
        st.pyplot(fig)
    else:
        st.warning("No dynamic historical data records found for this specific market view.")
except Exception as e:
    st.error(f"Could not connect to database warehouse layer: {e}")