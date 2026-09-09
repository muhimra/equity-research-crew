# graph.py
from agents.synthesis import synthesis_node
from agents.critic import critic_node
from agents.valuation import valuation_node
from agents.news_sentiment import news_node
from agents.fundamentals import fundamentals_node
from typing import Optional, TypedDict
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