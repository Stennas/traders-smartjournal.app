import streamlit as st
import pandas as pd
import os
import datetime
import matplotlib.pyplot as plt
from io import BytesIO

# ------------------ CONFIGURATION ------------------
TRADE_LOG_PATH = "trade_log.csv"
SCREENSHOT_FOLDER = "screenshots"
os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

if not os.path.exists(TRADE_LOG_PATH):
    df = pd.DataFrame(columns=[
        "Date", "Symbol", "Entry Time", "Exit Time",
        "Entry Price", "Exit Price", "Outcome", "Lot Size",
        "Comments", "Session", "Strategy Used", "Emotion Tag", "Screenshot"
    ])
    df.to_csv(TRADE_LOG_PATH, index=False)

trades = pd.read_csv(TRADE_LOG_PATH)

# ------------------ UI STYLING ------------------
st.set_page_config(page_title="SmartJournal", layout="wide")
st.markdown("""
    <style>
        .main > div { padding-top: 1.5rem; }
        .block-container { padding-top: 1rem; }
        .metric-box { border-radius: 10px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); margin: 5px; }
        footer { visibility: hidden; }
        @media (max-width: 768px) {
            .metric-box { text-align: center; }
            .stButton button { width: 100%; }
        }
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
col1, col2 = st.columns([8, 1])
with col1:
    st.title("📈 Trader's SmartJournal")
    st.caption("Log your trades, analyze behavior, and optimize your strategy.")

# ------------------ TRADE ENTRY FORM ------------------
st.markdown("### 📝 Log a New Trade")

with st.form("trade_form"):
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            date = st.date_input("Date", value=datetime.date.today())
            symbol = st.text_input("Symbol (e.g., EURUSD)")
            entry_time = st.time_input("Entry Time")
            exit_time = st.time_input("Exit Time")
            lot_size = st.number_input("Lot Size", min_value=0.01, step=0.01)
        with c2:
            entry_price = st.text_input("Entry Price")
            exit_price = st.text_input("Exit Price")
            outcome = st.selectbox("Outcome", ["Win", "Loss", "Break-even"])

    comments = st.text_area("Comments")
    
    st.markdown("> 💡 *Without tags, you're journaling trades.  \nWith tags, you're studying yourself.*")
    strategy_used = st.text_input("Strategy Used (e.g., Breakout)")
    emotion_tag = st.selectbox("Emotion Tag", [
                "Confident", "Fearful", "Revenge", "FOMO", "Calm", "Disciplined",
                "Frustrated", "Hopeful", "Greedy", "Other"
            ])
    screenshot_link = st.text_input("Screenshot URL (optional)")
    screenshot_file = st.file_uploader("Or Upload Screenshot", type=["png", "jpg", "jpeg"])

    def get_session(t):
        hour = t.hour
        if 0 <= hour < 8:
            return "Asia"
        elif 8 <= hour < 13:
            return "London"
        elif 13 <= hour < 22:
            return "New York"
        return "Off Hours"

    session = get_session(entry_time)

    submitted = st.form_submit_button("📩 Save Trade")
    if submitted:
        screenshot_path = screenshot_link
        if screenshot_file is not None:
            file_name = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{screenshot_file.name}"
            screenshot_path = os.path.join(SCREENSHOT_FOLDER, file_name)
            with open(screenshot_path, "wb") as f:
                f.write(screenshot_file.getbuffer())

        new_trade = {
            "Date": date,
            "Symbol": symbol.upper(),
            "Entry Time": entry_time.strftime("%H:%M"),
            "Exit Time": exit_time.strftime("%H:%M"),
            "Entry Price": entry_price,
            "Exit Price": exit_price,
            "Outcome": outcome,
            "Lot Size": lot_size,
            "Comments": comments,
            "Session": session,
            "Strategy Used": strategy_used,
            "Emotion Tag": emotion_tag,
            "Screenshot": screenshot_path
        }

        trades = pd.concat([trades, pd.DataFrame([new_trade])], ignore_index=True)
        trades.to_csv(TRADE_LOG_PATH, index=False)
        st.success("✅ Trade logged successfully!")

# ------------------ TRADE HISTORY ------------------
st.markdown("---")
st.markdown("### 📒 Trade History")

for _, row in trades[::-1].iterrows():
    with st.expander(f"{row['Date']} - {row['Symbol']} ({row['Outcome']})"):
        st.write(f"**Session:** {row['Session']}")
        st.write(f"**Strategy Used:** {row.get('Strategy Used', '')}")
        st.write(f"**Emotion Tag:** {row.get('Emotion Tag', '')}")
        st.write(f"**Entry Time:** {row['Entry Time']} | **Exit Time:** {row['Exit Time']}")
        st.write(f"**Entry Price:** {row['Entry Price']} | **Exit Price:** {row['Exit Price']}")
        st.write(f"**Lot Size:** {row['Lot Size']}")
        st.write(f"**Comments:** {row['Comments']}")

        if pd.notna(row['Screenshot']) and row['Screenshot'] != "":
            if str(row['Screenshot']).startswith("http"):
                st.markdown(f"[📷 View Screenshot]({row['Screenshot']})")
            elif os.path.exists(row['Screenshot']):
                st.image(row['Screenshot'], use_column_width=True)

# ------------------ ANALYTICS ------------------
st.markdown("---")
st.markdown("### 📊 Analytics Dashboard")

if not trades.empty:
    def get_time_block(time_str):
        hour = int(time_str.split(":")[0])
        block_start = (hour // 2) * 2
        block_end = block_start + 2
        return f"{block_start:02d}:00 - {block_end:02d}:00"

    trades["Time Block"] = trades["Entry Time"].apply(get_time_block)
    trades["Win"] = (trades["Outcome"] == "Win").astype(int)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trades", len(trades))
    with col2:
        st.metric("Win Rate", f"{trades['Win'].mean() * 100:.1f}%")
    with col3:
        st.metric("Most Active Session", trades["Session"].value_counts().idxmax())

    st.markdown("#### ⏱️ Trades by Time Block")
    block_stats = trades.groupby(["Session", "Time Block", "Outcome"]).size().unstack().fillna(0)
    fig_block, ax_block = plt.subplots(figsize=(10, 6))
    block_stats.plot(kind="bar", stacked=True, ax=ax_block)
    ax_block.set_ylabel("Number of Trades")
    st.pyplot(fig_block)

    st.markdown("#### 📊 Win Rate by Session and Time Block")
    grouped = trades.groupby(["Session", "Time Block"])["Win"].mean().reset_index()
    grouped["Win Rate (%)"] = grouped["Win"] * 100
    pivot_bar = grouped.pivot(index="Time Block", columns="Session", values="Win Rate (%)").fillna(0)
    fig_bar, ax_bar = plt.subplots(figsize=(12, 6))
    pivot_bar.plot(kind="bar", ax=ax_bar)
    ax_bar.set_ylabel("Win Rate (%)")
    ax_bar.set_title("Win Rate per Session and Time Block")
    st.pyplot(fig_bar)

    # ------------------ SMART INSIGHTS ON DEMAND ------------------
    if st.button("🧠 Show Smart Insights"):
        top_zones = pivot_bar.stack().sort_values(ascending=False).head(3)
        st.markdown("**🚀 Top 3 Most Profitable Zones:**")
        for (block, session), win_pct in top_zones.items():
            st.markdown(f"- `{session}` during `{block}`: **{win_pct:.1f}% win rate**")

        top_strategies = trades[trades["Outcome"] == "Win"].groupby("Strategy Used").size().sort_values(ascending=False).head(3)
        st.markdown("**🧪 Most Effective Strategies:**")
        for strat, count in top_strategies.items():
            st.markdown(f"- `{strat}`: {count} wins")

        st.success("💡 Tip: Focus on these zones with your best-performing strategies.")
else:
    st.info("No trades recorded yet for analytics.")

# ------------------ EXPORT SECTION ------------------
st.markdown("---")
st.markdown("### 📤 Export Your Data")

col1, col2 = st.columns(2)
with col1:
    st.download_button("📥 Download CSV", data=trades.to_csv(index=False), file_name="trade_log.csv", mime="text/csv")
with col2:
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        trades.to_excel(writer, sheet_name="Trades", index=False)
    st.download_button(
        label="📊 Download Excel",
        data=excel_buffer.getvalue(),
        file_name="trade_log.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ------------------ FOOTER ------------------
st.markdown("---")
st.caption("🛠️ Built with ❤️ by Stennas | © 2025")
