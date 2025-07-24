from langgraph.prebuilt import create_react_agent
from langgraph.graph.state import CompiledStateGraph
from llm.model import llm

react_agent_graph: CompiledStateGraph = create_react_agent(
    model=llm,
    tools=[],
    prompt=None,
)

    