import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
import textwrap

TICKERS = {
    "Nifty 50": "^NSEI",
    "Nifty Midcap 150": "NIFTYMIDCAP150.NS",
    "Nifty Smallcap 250": "NIFTYSMLCAP250.NS",
    "Brent Crude": "BZ=F",
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^NDX",
    "Soxx Index": "^SOX",
}

def get_intraday_data(ticker):

    df = yf.download(
        ticker,
        period="1d",
        interval="1m",
        auto_adjust=False,
        progress=False,
        multi_level_index=False,
    )

    if df.empty:
        return None

    df = df[["Close"]].dropna()

    return df


def get_daily_data(ticker):

    df = yf.download(
        ticker,
        period="1mo",
        interval="1d",
        auto_adjust=False,
        progress=False,
        multi_level_index=False,
    )

    if df.empty:
        return None

    df = df[["Close"]].dropna()

    return df


def get_market_data():

    results = {}

    for name, ticker in TICKERS.items():

        try:

            intraday = get_intraday_data(ticker)

            daily = get_daily_data(ticker)

            if daily is None or daily.empty:
                print(f"WARNING: No daily data for {name}")
                continue

            if intraday is not None and not intraday.empty:
                current = float(intraday["Close"].iloc[-1])
                current_time = intraday.index[-1]
            else:
                current = float(daily["Close"].iloc[-1])
                current_time = daily.index[-1]

            if len(daily) >= 2:
                previous_close = float(daily["Close"].iloc[-2])
            else:
                previous_close = None

            if len(daily) >= 6:
                five_day_close = float(daily["Close"].iloc[-6])
            else:
                five_day_close = None


            if previous_close is not None:
                change_1d = (
                    (current / previous_close) - 1
                ) * 100
            else:
                change_1d = None

            if five_day_close is not None:
                change_5d = (
                    (current / five_day_close) - 1
                ) * 100
            else:
                change_5d = None

            results[name] = {
                "ticker": ticker,
                "current": current,
                "previous_close": previous_close,
                "change_1d": change_1d,
                "change_5d": change_5d,
                "current_time": current_time,
                "daily_history": daily["Close"],
                "intraday_history": (
                    intraday["Close"]
                    if intraday is not None
                    else None
                ),
            }

            print(
                f"{name}: "
                f"{current:.2f} | "
                f"1D: {change_1d:.2f}% | "
                f"5D: {change_5d:.2f}%"
            )

        except Exception as e:
            print(f"ERROR downloading {name}: {e}")

    return results


def format_value(name, value):

    if value is None:
        return "N/A"

    if name == "Brent Crude":
        return f"${value:,.2f}"

    return f"{value:,.2f}"


def display_market_card(name, data):

    current = data["current"]
    change_1d = data["change_1d"]
    change_5d = data["change_5d"]

    if change_1d > 0:
        border_color = "#2E8B57"
        movement = "▲"
    elif change_1d < 0:
        border_color = "#C0392B"
        movement = "▼"
    else:
        border_color = "#999999"
        movement = "—"
        
    previous_close = data["previous_close"]

    if previous_close is not None:
        absolute_change = current - previous_close
    else:
        absolute_change = None
        
    if absolute_change is not None:
        change_text = f"{movement} {absolute_change:+,.2f} ({change_1d:+.2f}%)"
    else:
        change_text = "N/A"

    history = data["daily_history"].tail(5)

    normalized = (
        history / history.iloc[0] * 100
        if len(history) > 1
        else history
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized.values,
            mode="lines",
            line=dict(width=2),
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        height=45,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(
            visible=False,
        ),
        yaxis=dict(
            visible=False,
            fixedrange=True,
        ),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.html(
        f"""
        <div style="
            background-color: transparent;
            padding: 16px 18px 14px 18px;
            border-radius: 10px;
            border: 2px solid {border_color};
            font-family: sans-serif;
        ">

            <div style="
                font-size: 18px;
                font-weight: 800;
                color: #FFFFFF;
                margin-bottom: 4px;
            ">
                {name}
            </div>

            <div style="
                font-size: 28px;
                font-weight: 750;
                color: #FFFFFF;
                margin-top: 2px;
            ">
                {format_value(name, current)}
            </div>

            <div style="
                font-size: 14px;
                font-weight: 700;
                color: {border_color};
                margin-top: 4px;
            ">
                {change_text}

                <span style="
                    font-weight: 500;
                    color: #FFFFFF;
                    margin-left: 10px;
                ">
                    5D {change_5d:+.2f}%
                </span>
            </div>

        </div>
        """
    )

    #st.markdown(card_html, unsafe_allow_html=True)

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

def main():

    st.set_page_config(
        page_title="Market Monitor",
        page_icon="📈", #is this the right emoji? Maybe change later
        layout="wide",
    )

    header, refresh = st.columns([5, 1])

    with header:
        st.markdown(
            """
            <h1 style="margin-bottom: 0px;">
                Market Monitor
            </h1>
            <p style="color: #666; margin-top: 0px;">
                Latest available market data
            </p>
            """,
            unsafe_allow_html=True,
        )

    with refresh:
        refresh_button = st.button(
            "↻ Refresh",
            type="primary"
        )
    
    if refresh_button:
        with st.spinner("Fetching latest market data..."):
            st.session_state["market_data"] = get_market_data()


    if "market_data" not in st.session_state:

        st.info(
            "Click 'Refresh market data' to fetch the latest values."
        )

        return

    market_data = st.session_state["market_data"]

    names = list(TICKERS.keys())

    for i in range(0, len(names), 2):

        row = st.columns(2)

        with row[0]:
            name = names[i]
            display_market_card(
                name,
                market_data[name]
            )

        if i + 1 < len(names):
            with row[1]:
                name = names[i + 1]
                display_market_card(
                    name,
                    market_data[name]
                )

if __name__ == "__main__":

    main()