import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

st.set_page_config(page_title="Portfolio Optimisation", layout="wide")


@st.cache_resource
def get_client():
    def read(name):
        return os.environ[name] if name in os.environ else st.secrets[name]
    return create_client(read("SUPABASE_URL"), read("SUPABASE_PUBLISHABLE_KEY"))


@st.cache_data(ttl=600)
def load_data():
    response = (
        get_client()
        .table("predictions")
        .select("*")
        .order("prediction_date", desc=True)
        .execute()
    )
    df = pd.DataFrame(response.data)
    if not df.empty:
        for col in ["weight", "predicted_return", "current_price"]:
            df[col] = pd.to_numeric(df[col])
        df["prediction_date"] = pd.to_datetime(df["prediction_date"]).dt.date
    return df


st.title("Prophet + Markowitz Portfolio Optimisation")
st.caption("For illustration only. Not financial advice.")

df = load_data()
if df.empty:
    st.warning("No data yet. Run pipeline.py first, then refresh this page.")
    st.stop()

dates = sorted(df["prediction_date"].unique(), reverse=True)
chosen = st.selectbox("Prediction date", dates)
day = df[df["prediction_date"] == chosen].set_index("ticker")

left, right = st.columns(2)
with left:
    st.subheader("Suggested weights")
    st.bar_chart(day["weight"] * 100)
with right:
    st.subheader("Prophet's predicted next-day return (%)")
    st.caption("Raw prophet forecast. The optimizer capped each at ±3% to avoid extreme allocations.")
    st.bar_chart(day["predicted_return"] * 100)

st.subheader("Details")
st.dataframe(
    day[["weight", "predicted_return", "current_price"]].style.format(
        {"weight": "{:.1%}", "predicted_return": "{:+.2%}", "current_price": "${:,.2f}"}
    )
)

st.subheader("Weights over time")
history = df.pivot(index="prediction_date", columns="ticker", values="weight")
if len(history) > 1:
    st.line_chart(history * 100)
else:
    st.info("History will appear here once the pipeline has run on more than one day.")