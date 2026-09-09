# app.py
import streamlit as st
from graph import run_research, ResearchState
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Equity Research Crew",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Equity Research Analyst Crew")
st.caption("Multi-agent system powered by LangGraph + Claude")

# --- Input ---
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input(
        "Enter a stock ticker",
        placeholder="e.g. AAPL, MSFT, TSLA",
        max_chars=10
    ).upper().strip()
with col2:
    st.write("")
    st.write("")
    run_button = st.button("🚀 Run Research", type="primary", use_container_width=True)

if run_button and ticker:
    st.divider()

    # We'll stream results into these placeholders as agents complete
    fund_expander = st.expander("🏦 Fundamentals Agent", expanded=True)
    news_expander = st.expander("📰 News & Sentiment Agent", expanded=True)
    val_expander  = st.expander("📊 Valuation Agent", expanded=True)
    critic_expander = st.expander("🔍 Critic Agent", expanded=True)
    memo_placeholder = st.empty()

    try:
        with st.spinner(f"Running research crew for **{ticker}**..."):
            result = run_research(ticker)

        # --- Display each agent's output ---
        with fund_expander:
            st.markdown(f"**Company:** {result.get('company_name', 'N/A')}")
            st.markdown(result.get('fundamentals_summary', 'No output'))

        with news_expander:
            st.markdown(result.get('news_summary', 'No output'))

        with val_expander:
            revision_count = result.get('revision_count', 0)
            if revision_count > 1:
                st.warning(f"⚠️ Critic requested revision — valuation was revised {revision_count - 1}x")
            st.markdown(result.get('valuation', 'No output'))

        with critic_expander:
            feedback = result.get('critic_feedback', '')
            if 'REVISE' in feedback:
                st.error("🔄 Critic verdict: **REVISE**")
            else:
                st.success("✅ Critic verdict: **APPROVED**")
            st.markdown(feedback)

        # --- Final memo ---
        st.divider()
        st.subheader("📄 Final Investment Memo")
        memo_placeholder.markdown(result.get('final_memo', 'No memo generated'))

    except ValueError as e:
        st.error(f"❌ {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        st.caption("Check your API key and ticker symbol, then try again.")

elif run_button and not ticker:
    st.warning("Please enter a ticker symbol first.")