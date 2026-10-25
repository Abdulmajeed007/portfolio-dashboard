# Prophet + Markowitz Portfolio Dashboard

A live dashboard for an automated portfolio-optimisation pipeline. Every weekday it forecasts next-day returns for 11 US stocks with Facebook Prophet, then uses Markowitz optimisation to suggest portfolio weights. It also records what actually happened, so the forecasts can be judged on real out-of-sample data.

**Live app:** https://myportfolio-dashboard.streamlit.app/

*For illustration only. Not financial advice.*

## What the dashboard shows
- **Suggested weights:** how the optimiser splits the money across the stocks for a chosen date
- **Prophet's predicted next-day return:** the raw forecasts (the optimiser caps each at ±3% before using it)
- **Details table:** weight, predicted return, actual return (once the day has closed) and starting price
- **Weights over time:** how stable the allocation is from day to day
- **Live track record:** how often Prophet got the direction right, and the cumulative return of the portfolio vs an equal split

## How it works
```
yfinance prices -> Prophet forecasts -> Markowitz optimiser (SciPy) -> Supabase
                                                                          |
GitHub Actions (weekdays, 09:00 UTC)        Streamlit dashboard <---------+
        |
   tracker fills in actual returns after each close
```
- The pipeline runs on a schedule in a separate private repository.
- Forecasts are turned into expected returns, capped at ±3%, then fed into a mean-variance optimiser (weights between 2% and 25% per stock).
- Results go to a Supabase table. This dashboard reads them with a **read-only publishable key**, protected by row-level security, so it cannot change any data.

Stocks: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, NFLX, ADBE, INTC, CSCO

## Backtest findings (90 trading days, 11 stocks)

| Strategy | Total return | Sharpe | Max drawdown |
|---|---|---|---|
| Equal split | 2.30% | 0.42 | -6.67% |
| Prophet + Markowitz (risk aversion 3) | 10.54% | 1.28 | -9.54% |
| Prophet + Markowitz (risk aversion 1000) | 5.92% | 1.03 | -5.26% |
| Markowitz, no forecasts | 6.20% | 1.08 | -5.20% |

- Prophet's up/down accuracy was about **51.7%**, close to a coin flip.
- With forecasts capped, the risk-aversion-1000 portfolio performed about the same as Markowitz with no forecasts at all. Most of the benefit over the equal split came from risk management, not forecasting.
- Uncapped forecasts (for example +37% in one day for INTC) distorted the weights, which is why they are capped.

**Limitations:** 90 days is a short window in a rising market, Sharpe ratios are annualised from a short sample, the stock list was not selected independently of recent performance, and there are no trading costs. The live track record is the more reliable test as it accumulates.

## Run it locally
```
pip install -r requirements.txt
streamlit run dashboard.py
```
Create a `.env` file with:
```
SUPABASE_URL=your-project-url
SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```
The app expects a Supabase table called `predictions` with columns `prediction_date`, `ticker`, `weight`, `predicted_return`, `current_price` and `actual_return`.

## Tech stack
Python, Prophet, SciPy, pandas, yfinance, Supabase (Postgres), GitHub Actions, Streamlit
