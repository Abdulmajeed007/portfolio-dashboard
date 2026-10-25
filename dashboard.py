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
        for col in ["weight", "predicted_return", "current_price", "actual_return"]:
            if col in df.columns:
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
    day[["weight", "predicted_return", "current_price", "actual_return"]].style.format(
        {"weight": "{:.1%}", "predicted_return": "{:+.2%}", "current_price": "${:,.2f}", "actual_return": "{:+.2%}"},
        na_rep="pending",
    )
)

st.subheader("Weights over time")
history = df.pivot(index="prediction_date", columns="ticker", values="weight")
if len(history) > 1:
    st.line_chart(history * 100)
else:
    st.info("History will appear here once the pipeline has run on more than one day.")
st.subheader("Live track record")
if "actual_return" in df.columns and df["actual_return"].notna().any():
    tracked = df.dropna(subset=["actual_return"]).copy()
    tracked["correct"] = (tracked["predicted_return"] > 0) == (tracked["actual_return"] > 0)
    tracked["contribution"] = tracked["weight"] * tracked["actual_return"]

    a, b, c = st.columns(3)
    a.metric("Days tracked", tracked["prediction_date"].nunique())
    b.metric("Forecasts checked", len(tracked))
    c.metric("Up/down hit rate", f"{tracked['correct'].mean():.1%}")

    daily = tracked.groupby("prediction_date").agg(
        **{"Our portfolio": ("contribution", "sum"), "Equal split": ("actual_return", "mean")}
    )
    st.line_chart(((1 + daily).cumprod() - 1) * 100)
    st.caption("Cumulative % return, close to close, before trading costs. A coin flip hits 50%.")
else:
    st.info("The track record fills in after the first full trading day has closed.")    