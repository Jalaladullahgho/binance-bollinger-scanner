
import ccxt
import pandas as pd
import ta
import time
import streamlit as st

st.set_page_config(page_title="Bollinger Bands Scanner (Bybit)", layout="wide")
st.title("🔍 Bybit Weekly Bollinger Bands Scanner")
st.markdown("يعرض العملات ذات أضيق فارق فعلي بين Upper و Lower لبولينجر باندز (فريم أسبوعي)")

# إعداد Bybit API عبر ccxt
exchange = ccxt.bybit()

with st.spinner("📡 جاري تحميل الأسواق من Bybit..."):
    try:
        markets = exchange.load_markets()
        symbols = [s for s in markets if s.endswith('/USDT') and ':' not in s]
    except Exception as e:
        st.error(f"فشل تحميل الأسواق: {str(e)}")
        st.stop()

limit = st.slider("عدد العملات التي سيتم فحصها:", 10, len(symbols), 50)
symbols = symbols[:limit]

results = []
progress = st.progress(0)
status_text = st.empty()
error_log = st.expander("📋 سجل الأخطاء", expanded=False)
error_messages = []

for i, symbol in enumerate(symbols):
    try:
        status_text.text(f"جاري تحليل {symbol} ({i+1}/{len(symbols)})")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1w', limit=30)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])

        if df.empty or len(df) < 20:
            raise ValueError("بيانات غير كافية")

        df['bb_upper'] = ta.volatility.BollingerBands(df['close'], window=20).bollinger_hband()
        df['bb_lower'] = ta.volatility.BollingerBands(df['close'], window=20).bollinger_lband()
        df.dropna(inplace=True)

        last_row = df.iloc[-1]
        bb_diff = last_row['bb_upper'] - last_row['bb_lower']

        results.append((symbol, bb_diff))
        time.sleep(0.5)
    except Exception as e:
        error_messages.append(f"{symbol}: {str(e)}")
        continue

    progress.progress((i + 1) / len(symbols))

if error_messages:
    error_log.write("\n".join(error_messages))

results_sorted = sorted(results, key=lambda x: x[1])
top_n = st.slider("كم عملة تريد عرضها؟", 5, 30, 15)

st.subheader("📈 العملات ذات أضيق Bollinger Bands فعلياً (UP - DN)")
df_result = pd.DataFrame(results_sorted[:top_n], columns=["العملة", "الفرق الفعلي"])
st.dataframe(df_result, use_container_width=True)
