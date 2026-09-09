# app.py
import streamlit as st
from graph import run_research_stream, ResearchState
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Equity Research Crew",
    page_icon="📈",
    layout="wide"
)

# --- Sidebar config ---
with st.sidebar:
    st.header("⚙️ Agent Configuration")
    st.caption("Select model per agent")

    MODEL_OPTIONS = ["claude-sonnet-4-5", "claude-haiku-4-5"]

    fund_model    = st.selectbox("Fundamentals Agent", MODEL_OPTIONS, index=0)
    news_model    = st.selectbox("News Agent",         MODEL_OPTIONS, index=0)
    val_model     = st.selectbox("Valuation Agent",    MODEL_OPTIONS, index=0)
    critic_model  = st.selectbox("Critic Agent",       MODEL_OPTIONS, index=0)
    synth_model   = st.selectbox("Synthesis Agent",    MODEL_OPTIONS, index=0)

    st.divider()
    st.caption("Valuation approach")
    val_approach = st.radio(
        "Method",
        ["dcf", "comps"],
        format_func=lambda x: "DCF (Discounted Cash Flow)" if x == "dcf" else "P/E Comps"
    )

agent_config = {
    "fundamentals_model":  fund_model,
    "news_model":          news_model,
    "valuation_model":     val_model,
    "critic_model":        critic_model,
    "synthesis_model":     synth_model,
    "valuation_approach":  val_approach
}

# --- Header ---
st.title("📈 Equity Research Analyst Crew")
st.caption("Multi-agent system · LangGraph orchestration · Claude")

# --- Input ---
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input(
        "Stock ticker",
        placeholder="e.g. AAPL, MSFT, TSLA",
        max_chars=10
    ).upper().strip()
with col2:
    st.write("")
    st.write("")
    run_button = st.button("🚀 Run Research", type="primary", use_container_width=True)

# --- Pipeline diagram ---
def render_pipeline(statuses: dict):
    """Renders the 5-node pipeline with colour-coded status."""
    nodes = ["fundamentals", "news", "valuation", "critic", "synthesis"]
    labels = {
        "fundamentals": "🏦 Fundamentals",
        "news":         "📰 News",
        "valuation":    "📊 Valuation",
        "critic":       "🔍 Critic",
        "synthesis":    "📝 Synthesis"
    }
    status_style = {
        "waiting":  ("⚪", "#888888", "Waiting"),
        "running":  ("🔄", "#FFA500", "Running..."),
        "done":     ("✅", "#00AA00", "Done"),
        "revising": ("🔁", "#FF6600", "Revising"),
        "approved": ("✅", "#00AA00", "Approved"),
        "revised":  ("⚠️", "#FF6600", "Revised"),
        "error":    ("❌", "#FF0000", "Error"),
    }

    cols = st.columns(len(nodes))
    for i, node in enumerate(nodes):
        status = statuses.get(node, "waiting")
        icon, color, label = status_style.get(status, status_style["waiting"])
        with cols[i]:
            st.markdown(
                f"""<div style='text-align:center; padding:10px; border-radius:8px;
                border: 2px solid {color}; background-color:{color}15;'>
                <div style='font-size:1.5em'>{icon}</div>
                <div style='font-weight:bold; font-size:0.85em'>{labels[node]}</div>
                <div style='color:{color}; font-size:0.75em'>{label}</div>
                </div>""",
                unsafe_allow_html=True
            )
        if i < len(nodes) - 1:
            pass  # arrows handled by column spacing

if run_button and ticker:
    st.divider()

    # Pipeline status tracker
    statuses = {n: "waiting" for n in ["fundamentals", "news", "valuation", "critic", "synthesis"]}
    pipeline_placeholder = st.empty()

    with pipeline_placeholder.container():
        render_pipeline(statuses)

    st.divider()

    # Per-agent output placeholders
    agent_outputs = {}
    for node in ["fundamentals", "news", "valuation", "critic"]:
        agent_outputs[node] = st.expander(
            f"{'🏦' if node=='fundamentals' else '📰' if node=='news' else '📊' if node=='valuation' else '🔍'} {node.title()} Agent",
            expanded=False
        ).empty()

    memo_placeholder = st.empty()
    full_state = {}
    revision_count = 0

    try:
        for node_name, state_update in run_research_stream(ticker, agent_config):
            full_state.update(state_update)

            # Mark current node as running then done
            statuses[node_name] = "done"

            # Special handling per node
            if node_name == "fundamentals":
                with pipeline_placeholder.container():
                    render_pipeline(statuses)
                agent_outputs["fundamentals"].markdown(
                    f"**Company:** {state_update.get('company_name', 'N/A')}\n\n"
                    + state_update.get('fundamentals_summary', '')
                )

            elif node_name == "news":
                with pipeline_placeholder.container():
                    render_pipeline(statuses)
                agent_outputs["news"].markdown(
                    state_update.get('news_summary', '')
                )

            elif node_name == "valuation":
                revision_count = full_state.get("revision_count", 0)
                if revision_count > 0:
                    statuses["valuation"] = "revising"
                with pipeline_placeholder.container():
                    render_pipeline(statuses)
                statuses["valuation"] = "done"
                agent_outputs["valuation"].markdown(
                    f"*Revision #{revision_count}*\n\n"
                    + state_update.get('valuation', '')
                )

            elif node_name == "critic":
                feedback = state_update.get('critic_feedback', '')
                if "REVISE" in feedback or "Resubmission" in feedback:
                    statuses["critic"] = "revised"
                    # Extract the REVISE reason
                    revise_line = [l for l in feedback.split('\n') if 'REVISE' in l]
                    reason = revise_line[-1] if revise_line else "Revision requested"
                    agent_outputs["critic"].error(f"🔄 **REVISE requested**\n\n{reason}\n\n---\n\n{feedback}")
                    # Reset valuation status to show it will rerun
                    statuses["valuation"] = "waiting"
                else:
                    statuses["critic"] = "approved"
                    agent_outputs["critic"].success(f"✅ **APPROVED**\n\n{feedback}")

                with pipeline_placeholder.container():
                    render_pipeline(statuses)

            elif node_name == "synthesis":
                statuses["synthesis"] = "done"
                with pipeline_placeholder.container():
                    render_pipeline(statuses)

                final_memo = state_update.get('final_memo', '')
                st.divider()
                st.subheader("📄 Final Investment Memo")
                memo_placeholder.markdown(final_memo)

                # Download button
                st.download_button(
                    label="⬇️ Download Memo (.md)",
                    data=final_memo,
                    file_name=f"{ticker}_research_memo.md",
                    mime="text/markdown"
                )

    except ValueError as e:
        st.error(f"❌ {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        st.caption("Check your API key and ticker, then try again.")

elif run_button and not ticker:
    st.warning("Please enter a ticker symbol first.")