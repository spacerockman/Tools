import streamlit as st
import pandas as pd
import json
from datetime import datetime
from scrapegraphai.graphs import SmartScraperGraph

# Page config
st.set_page_config(page_title="S&P 500 Investment Strategy", layout="wide")

# Constants
BASE_INVESTMENT = 50000  # 基准定投
VOLATILITY_RESERVE = 30000  # 波动追加储备金
BOTTOM_RESERVE = 20000  # 顶格抄底储备金
CIRCUIT_BREAKER_THRESHOLD = 0.20  # 熔断阈值

# Initialize session state
if 'market_data' not in st.session_state:
    st.session_state.market_data = {}

def fetch_sp500_data():
    query = "Extract the current price, previous close, day range, year range, market cap, PE ratio, and dividend yield of the S&P 500 from the Google Finance page"
    url = "https://www.google.com/finance/quote/.INX:INDEXSP"
    
    graph = SmartScraperGraph(query, url, {
        "llm": {
            "model": "gemini-1.5-pro-latest",
            "api_key": "AIzaSyDYl-kXZIsFETsBQbvgqQkmzzJn2sDsswA"
        }
    })
    
    result = graph.run()
    return result

def calculate_investment_amount(current_price, previous_close):
    try:
        if not previous_close or previous_close == 0:
            st.warning("Previous close price is not available. Using current price for calculation.")
            return BASE_INVESTMENT
        
        daily_change = (current_price - previous_close) / previous_close
        
        if daily_change <= -0.07:  # 跌幅>7%
            return BASE_INVESTMENT + VOLATILITY_RESERVE + BOTTOM_RESERVE
        elif -0.07 < daily_change <= -0.01:  # 跌幅1%~7%
            scaled_additional = abs(daily_change) * VOLATILITY_RESERVE
            return BASE_INVESTMENT + scaled_additional
        else:
            return BASE_INVESTMENT
    except Exception as e:
        st.error(f"Error calculating investment amount: {str(e)}")
        return BASE_INVESTMENT

def main():
    st.title("S&P 500 Investment Strategy Dashboard")
    
    # Add refresh button
    if st.button("Refresh Market Data"):
        with st.spinner("Fetching latest S&P 500 data..."):
            try:
                market_data = fetch_sp500_data()
                st.session_state.market_data = market_data.get("content", {})
            except Exception as e:
                st.error(f"Error fetching market data: {str(e)}")
    else:
        # Load market data from file if session state is empty
        if not st.session_state.market_data:
            try:
                with open("sp500_data.json", "r") as f:
                    data = json.load(f)
                    st.session_state.market_data = data.get("content", {})
            except Exception as e:
                st.error(f"Error loading market data: {str(e)}")
    
    # Create columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Market Data")
        current_price = st.session_state.market_data.get('Current Price', 'N/A')
        previous_close = st.session_state.market_data.get('Previous Close', 'N/A')
        try:
            delta = float(current_price.replace(',', '')) - float(previous_close.replace(',', ''))
        except:
            delta = 0
            
        st.metric(
            label="S&P 500 Price",
            value=f"${current_price}",
            delta=f"${delta:.2f}"
        )
        
        st.write("**Market Information**")
        info_df = pd.DataFrame({
            "Metric": ["Previous Close", "Day Range", "Year Range", "Market Cap", "PE Ratio", "Dividend Yield"],
            "Value": [
                st.session_state.market_data.get("Previous Close", "N/A"),
                st.session_state.market_data.get("Day Range", "N/A"),
                st.session_state.market_data.get("Year Range", "N/A"),
                st.session_state.market_data.get("Market Cap", "N/A"),
                st.session_state.market_data.get("PE ratio", "N/A"),
                st.session_state.market_data.get("Dividend Yield", "N/A")
            ]
        })
        st.table(info_df)
    
    with col2:
        st.subheader("Investment Strategy")
        
        # Calculate investment amount
        try:
            current_price = float(st.session_state.market_data.get('Current Price', '0').replace(',', ''))
            previous_close = float(st.session_state.market_data.get('Previous Close', '0').replace(',', ''))
            
            if current_price == 0:
                st.error("Unable to fetch current market price. Please try again later.")
                return
                
            investment_amount = calculate_investment_amount(current_price, previous_close)
            
            # Calculate daily change safely
            daily_change = 0
            if previous_close != 0:
                daily_change = (current_price - previous_close) / previous_close
            
            # Display investment recommendation
            st.metric(
                label="Recommended Investment Amount (JPY)",
                value=f"¥{investment_amount:,.0f}",
                delta=f"{daily_change:.2%}"
            )

            # Investment breakdown
            st.write("**Investment Breakdown**")
            st.progress(BASE_INVESTMENT / investment_amount)
            st.write(f"Base Investment: ¥{BASE_INVESTMENT:,.0f}")
            
            if investment_amount > BASE_INVESTMENT:
                volatility_amount = min(VOLATILITY_RESERVE, investment_amount - BASE_INVESTMENT)
                st.progress(volatility_amount / investment_amount)
                st.write(f"Volatility Reserve Used: ¥{volatility_amount:,.0f}")
                
                if investment_amount > BASE_INVESTMENT + VOLATILITY_RESERVE:
                    bottom_amount = investment_amount - BASE_INVESTMENT - VOLATILITY_RESERVE
                    st.progress(bottom_amount / investment_amount)
                    st.write(f"Bottom Reserve Used: ¥{bottom_amount:,.0f}")
            
            # Circuit breaker warning
            if daily_change <= -CIRCUIT_BREAKER_THRESHOLD:
                st.error("⚠️ Circuit Breaker Activated: Investment suspended for 3 months due to 20% drawdown")
        except Exception as e:
            st.error(f"Error processing market data: {str(e)}")

if __name__ == "__main__":
    main()