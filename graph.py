# graph.py
from typing import Optional, TypedDict, Generator
from langgraph.graph import StateGraph, END
from agents.fundamentals import fundamentals_node
from agents.news_sentiment import news_node
from agents.valuation import valuation_node
from agents.critic import critic_node
from agents.synthesis import synthesis_node

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
    agent_config: Optional[dict]  # NEW

def route_after_critic(state: ResearchState) -> str:
    feedback = state.get("critic_feedback", "")
    revision_count = state.get("revision_count", 0)
    needs_revision = (
        "REVISE" in feedback or
        "Resubmission" in feedback or
        "REJECT" in feedback
    )
    if needs_revision and revision_count < 2:
        print(f"[router] Revision requested (count={revision_count}). Looping back.")
        return "valuation"
    else:
        print("[router] Proceeding to synthesis.")
        return "synthesis"

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

def run_research(ticker: str, agent_config: dict = None) -> ResearchState:
    initial_state = {
        "ticker": ticker,
        "company_name": None,
        "fundamentals_data": None,
        "fundamentals_summary": None,
        "news_summary": None,
        "valuation": None,
        "critic_feedback": None,
        "final_memo": None,
        "revision_count": 0,
        "agent_config": agent_config or {}
    }
    return app.invoke(initial_state)

def run_research_stream(ticker: str, agent_config: dict = None) -> Generator:
    """Yields (node_name, state_update) after each node completes."""
    initial_state = {
        "ticker": ticker,
        "company_name": None,
        "fundamentals_data": None,
        "fundamentals_summary": None,
        "news_summary": None,
        "valuation": None,
        "critic_feedback": None,
        "final_memo": None,
        "revision_count": 0,
        "agent_config": agent_config or {}
    }
    for chunk in app.stream(initial_state):
        # chunk = {"node_name": {state_dict}}
        for node_name, state_update in chunk.items():
            yield node_name, state_update