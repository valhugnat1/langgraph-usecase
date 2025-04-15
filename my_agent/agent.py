from my_agent.utils.nodes import supervisor_node, worker_general, worker_code, worker_HR, worker_product
from my_agent.utils.state import State
from langgraph.graph import StateGraph, START


builder = StateGraph(State)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("general ai", worker_general)
builder.add_node("code ai", worker_code)

graph = builder.compile()
graph.name = "Agent"