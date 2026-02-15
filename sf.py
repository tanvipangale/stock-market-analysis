import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="STOCK ANALYSIS | Terminal",
    page_icon="📈",
    layout="wide"
)

# Basic styling
st.markdown("""
<style>
.stApp {
    background-color: #1e1e2f;
    color: #e0e0e0;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Market Controls")

ticker_input = st.sidebar.text_input("Ticker Symbol", "AAPL").upper()

today = datetime.now()
date_input = st.sidebar.date_input(
    "Select Date Range",
    value=(today - timedelta(days=365), today),
    max_value=today
)

if isinstance(date_input, tuple) and len(date_input) == 2:
    start_date, end_date = date_input
else:
    st.sidebar.info("Select complete date range")
    st.stop()

show_rsi = st.sidebar.checkbox("Show RSI", value=True)
show_sma = st.sidebar.checkbox("Show 50 Day SMA", value=True)

# Fetch data
@st.cache_data(ttl=300)
def fetch_data(ticker, start, end):
    try:
        asset = yf.Ticker(ticker)
        df = asset.history(start=start, end=end)
        info = asset.info
        if df.empty:
            return None, None
        return df, info
    except:
        return None, None


def main():
    data, info = fetch_data(ticker_input, start_date, end_date)

    if data is None or info is None:
        st.error("Data could not be retrieved")
        return

    # Price calculations
    curr_price = data["Close"].iloc[-1]
    prev_price = data["Close"].iloc[-2]
    price_change = curr_price - prev_price

    st.title(f"📈 {info.get('longName', ticker_input)}")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Latest Price", f"${curr_price:.2f}", f"{price_change:.2f}")
    col2.metric("Highest Price", f"${data['High'].max():.2f}")
    col3.metric("Lowest Price", f"${data['Low'].min():.2f}")
    col4.metric("Average Volume", f"{int(data['Volume'].mean()/1e6)}M")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Chart", "Company Info", "Historical Data"])

    # Chart tab
    with tab1:

        # Price Action Section
        st.subheader("Price Action")

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data["Open"],
            high=data["High"],
            low=data["Low"],
            close=data["Close"],
            name="Price"
        ))

        if show_sma:
            sma = data["Close"].rolling(50).mean()
            fig.add_trace(go.Scatter(
                x=data.index,
                y=sma,
                name="50 Day SMA"
            ))

        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # RSI Section
        if show_rsi:
            st.subheader("RSI (Relative Strength Index)")

            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=data.index,
                y=rsi,
                name="RSI"
            ))

            fig_rsi.update_layout(
                template="plotly_dark",
                yaxis=dict(range=[0, 100])
            )

            st.plotly_chart(fig_rsi, use_container_width=True)

        # Volume Section
        st.subheader("Trading Volume")

        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=data.index,
            y=data["Volume"],
            name="Volume"
        ))

        fig_vol.update_layout(template="plotly_dark")
        st.plotly_chart(fig_vol, use_container_width=True)

    # comapny info tab
    with tab2:
        st.subheader("Key Statistics")
        st.write("Exchange:", info.get("exchange", "N/A"))
        st.write("Market Cap:", info.get("marketCap", "N/A"))
        st.write("Trailing PE:", info.get("trailingPE", "N/A"))
        st.write("Dividend Yield:", info.get("dividendYield", "N/A"))

        st.subheader("Business Summary")
        st.write(info.get("longBusinessSummary", "No description available"))

    # historical data tab
    with tab3:
        st.subheader("Historical Records")

        log_df = data.sort_index(ascending=False).copy()
        log_df.index = log_df.index.strftime("%Y-%m-%d")

        st.dataframe(log_df, use_container_width=True)


if __name__ == "__main__":
    main()
