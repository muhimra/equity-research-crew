# graph.py
from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END

# --- State Schema ---
class ResearchState(TypedDict):
    ticker: str
    company_name: Optional[str]
    fundamentals_data: Optional[dict]
    fundamentals_summary: Optional[str]
    news_summary: Optional[str]
    valuation: Optional[str]
    critic_feedback: Optional[str]
    final_memo: Optional[str]
    revision_count: int

# --- Dummy Nodes ---
def fundamentals_node(state: ResearchState) -> dict:
    print(f"[fundamentals] Running for ticker: {state['ticker']}")
    return {
        "company_name": "Dummy Corp",
        "fundamentals_data": {"trailingPE": 25, "marketCap": 1e12},
        "fundamentals_summary": "Dummy fundamentals summary."
    }

def news_node(state: ResearchState) -> dict:
    print("[news] Running news agent")
    return {"news_summary": "Dummy news summary."}

def valuation_node(state: ResearchState) -> dict:
    print(f"[valuation] Running valuation (revision #{state['revision_count']})")
    return {"valuation": "Dummy valuation output."}

def critic_node(state: ResearchState) -> dict:
    print("[critic] Running critic")
    verdict = "APPROVE"  # Change to "REVISE: assumptions too optimistic" to test loop
    return {
        "critic_feedback": verdict,
        "revision_count": state["revision_count"] + 1
    }

def synthesis_node(state: ResearchState) -> dict:
    print("[synthesis] Writing final memo")
    return {"final_memo": "# Dummy Final Memo\n\nAll agents completed."}

# --- Conditional Routing ---
def route_after_critic(state: ResearchState) -> str:
    feedback = state.get("critic_feedback", "")
    revision_count = state.get("revision_count", 0)
    if "REVISE" in feedback and revision_count < 2:
        print(f"[router] Critic said REVISE (count={revision_count}). Looping back.")
        return "valuation"
    else:
        print("[router] Proceeding to synthesis.")
        return "synthesis"

# --- Graph Assembly ---
def build_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("fundamentals", fundamentals_node)
    graph.add_node("news", news_node)
    graph.add_node("valuation", valuation_node)
    graph.add_node("critic", critic_node)
    graph.add_node("synthesis", synthesis_node)

    graph.set_entry_point("fundamentals")
    graph.add_edge("fundamentals", "news")
    graph.add_edge("news", "valuation")
    graph.add_edge("valuation", "critic")
    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {"valuation": "valuation", "synthesis": "synthesis"}
    )
    graph.add_edge("synthesis", END)
    return graph.compile()

app = build_graph()

# --- Entry Point ---
def run_research(ticker: str) -> ResearchState:
    initial_state = {
        "ticker": ticker,
        "company_name": None,
        "fundamentals_data": None,
        "fundamentals_summary": None,
        "news_summary": None,
        "valuation": None,
        "critic_feedback": None,
        "final_memo": None,
        "revision_count": 0
    }
    return app.invoke(initial_state)