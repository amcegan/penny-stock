from langgraph.graph import StateGraph, END
from stock_scanner.state import GraphState
from stock_scanner.nodes.screener import screener_node
from stock_scanner.nodes.volume import volume_node
from stock_scanner.nodes.analyst import analyst_node
from stock_scanner.nodes.news import news_node
from stock_scanner.nodes.reporting import reporting_node
from stock_scanner.config import config

def create_graph():
    """Defines and compiles the LangGraph workflow."""
    
    workflow = StateGraph(GraphState)
    
    # Add Nodes
    workflow.add_node("screener", screener_node)
    workflow.add_node("volume_filter", volume_node)
    workflow.add_node("analyst_filter", analyst_node)
    workflow.add_node("news_analysis", news_node)
    workflow.add_node("reporter", reporting_node)
    
    # Add Edges (Linear Flow)
    workflow.set_entry_point("screener")
    workflow.add_edge("screener", "volume_filter")
    workflow.add_edge("volume_filter", "analyst_filter")
    workflow.add_edge("analyst_filter", "news_analysis")
    workflow.add_edge("news_analysis", "reporter")
    workflow.add_edge("reporter", END)
    
    # Compile
    app = workflow.compile()
    return app

app = create_graph()
