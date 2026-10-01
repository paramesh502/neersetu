"""
NeerSetu LangGraph pipeline.

Graph:
  intake → fairness → negotiation → consent → ledger → dispatcher → END

Each node is a pure function: NeerSetuState → NeerSetuState.
"""
from langgraph.graph import StateGraph, END
from agents.state import NeerSetuState
from agents.intake_agent import run_intake_agent
from agents.fairness_agent import run_fairness_agent
from agents.negotiation_agent import run_negotiation_agent
from agents.consent_agent import run_consent_agent
from agents.ledger_agent import run_ledger_agent
from agents.dispatcher_agent import run_dispatcher_agent


def should_continue_after_negotiation(state: NeerSetuState) -> str:
    """Route: if negotiation found a yielding farmer, continue; else dispatch anyway."""
    if state.get("error"):
        return "dispatcher"
    return "consent"


def build_pipeline() -> StateGraph:
    graph = StateGraph(NeerSetuState)

    graph.add_node("intake", run_intake_agent)
    graph.add_node("fairness", run_fairness_agent)
    graph.add_node("negotiation", run_negotiation_agent)
    graph.add_node("consent", run_consent_agent)
    graph.add_node("ledger", run_ledger_agent)
    graph.add_node("dispatcher", run_dispatcher_agent)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "fairness")
    graph.add_edge("fairness", "negotiation")
    graph.add_conditional_edges(
        "negotiation",
        should_continue_after_negotiation,
        {"consent": "consent", "dispatcher": "dispatcher"},
    )
    graph.add_edge("consent", "ledger")
    graph.add_edge("ledger", "dispatcher")
    graph.add_edge("dispatcher", END)

    return graph.compile()


# Compiled graph singleton
neersetu_pipeline = build_pipeline()
