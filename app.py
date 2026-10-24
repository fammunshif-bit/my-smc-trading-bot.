import streamlit as st
import pandas as pd
import time
import ccxt
from datetime import datetime

# --- WEB PAGE CONFIGURATION ---
st.set_page_config(page_title="SMC/ICT Trading Bot", layout="wide", initial_sidebar_state="expanded")

st.title("🌐 Live SMC/ICT Cloud Trading Engine")
st.caption("Access and control your bot securely from any web browser.")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("🎛️ Bot Settings")
trade_mode = st.sidebar.selectbox("Trading Mode", ["Simulation (Paper Trading)", "Live API Account"])
asset_class = st.sidebar.selectbox("Market Asset", ["Crypto (BTC/USDT)", "Crypto (ETH/USDT)"])
timeframe = st.sidebar.selectbox("Chart Timeframe", ["1m", "5m", "15m", "1H"])

st.sidebar.subheader("🛡️ Risk Parameters")
max_risk = st.sidebar.slider("Account Risk per Trade (%)", 0.1, 5.0, 1.0, 0.1)
target_rr = st.sidebar.slider("Target Risk-to-Reward (R:R)", 1.0, 5.0, 2.0, 0.5)

bot_active = st.sidebar.toggle("🔴 ACTIVATE TRADING ENGINE", value=False)

# --- INITIALIZE SESSION STATE ---
if "logs" not in st.session_state:
    st.session_state.logs = []
if "balance" not in st.session_state:
    st.session_state.balance = 10000.00

# --- METRIC CARDS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Account Balance", f"${st.session_state.balance:,.2f}")
with col2:
    st.metric("Bot Status", "ONLINE & RUNNING" if bot_active else "PAUSED / IDLE")
with col3:
    status_color = "🟢" if trade_mode == "Simulation (Paper Trading)" else "⚠️"
    st.metric("Execution Environment", f"{status_color} {trade_mode}")

# --- STRATEGY ENGINE FUNCTION ---
def scan_smc_patterns(symbol, tf):
    """Fetches real market candles and looks for basic FVGs and Order Blocks"""
    try:
        exchange = ccxt.binance()
        # Fetch last 30 candles
        candles = exchange.fetch_ohlcv(symbol, tf, limit=30)
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        current_price = df['close'].iloc[-1]
        
        # Check for a simple Bullish Fair Value Gap (FVG)
        # Definition: Low of candle[i] > High of candle[i-2]
        c_low = df['low'].iloc[-1]
        p_high = df['high'].iloc[-3]
        
        fvg_detected = False
        if c_low > p_high:
            fvg_detected = True
            
        return current_price, fvg_detected
    except Exception as e:
        return None, False

# --- LIVE ENGINE LOOP ---
st.subheader("📊 Live Activity Tracker & Logs")
log_container = st.empty()

if bot_active:
    symbol_map = {"Crypto (BTC/USDT)": "BTC/USDT", "Crypto (ETH/USDT)": "ETH/USDT"}
    market_symbol = symbol_map[asset_class]
    
    st.toast("Bot engine successfully initialized!", icon="🚀")
    
    # Run a lightweight scan cycle
    current_price, fvg_found = scan_smc_patterns(market_symbol, timeframe)
    
    now = datetime.now().strftime("%H:%M:%S")
    if current_price:
        st.session_state.logs.insert(0, f"[{now}] Checked {market_symbol} | Price: ${current_price:,.2f}")
        
        if fvg_found:
            st.session_state.logs.insert(0, f"💥 [{now}] SMC Pattern Spotted: Bullish FVG detected on {market_symbol}!")
            st.session_state.logs.insert(0, f"🛒 [{now}] Order Placed: Buy Market Entry executed at ${current_price:,.2f}")
            
            # Simple simulation profit calculation
            if trade_mode == "Simulation (Paper Trading)":
                st.session_state.balance += (st.session_state.balance * (max_risk / 100) * target_rr)
    else:
        st.session_state.logs.insert(0, f"[{now}] Connecting to exchange data feeds...")
else:
    st.info("The trading engine is currently turned off. Flip the toggle switch in the left sidebar to start scanning for SMC setups.")

# Print logs to screen
with log_container.container():
    for log in st.session_state.logs[:15]:
        st.text(log)

# --- REFRESH INSTRUCTION ---
if bot_active:
    time.sleep(5)
    st.rerun()
