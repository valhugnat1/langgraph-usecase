from typing import Literal, TypedDict
from langgraph.graph import  END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from my_agent.utils.prompts import CHAT_OPTIONS, SYSTEM_PROMPT
from my_agent.utils.state import State
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import os
from my_agent.utils.tools import tools

load_dotenv()


llm = ChatOpenAI(
    base_url=os.getenv("SCW_GENERATIVE_APIs_ENDPOINT"),
    api_key=os.getenv("SCW_SECRET_KEY_PERSO"), 
    model="llama-3.1-70b-instruct",
)

llm = ChatAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-5-sonnet-20241022"
)

llm_agent_no_tool = create_react_agent(llm, tools=[])
llm_agent_tools = create_react_agent(llm, tools=tools)


class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*CHAT_OPTIONS]



def supervisor_node(state: State) -> Command[Literal[*CHAT_OPTIONS]]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    return Command(goto=goto, update={"next": goto})




def worker_general(state: State) -> Command[Literal["__end__"]]:
    result = llm_agent_tools.invoke(state)
    return Command(
        update={"messages": [AIMessage(content=result["messages"][-1].content)]},
        goto=END,
    )



def worker_code(state: State) -> Command[Literal["__end__"]]:
    result = llm_agent_no_tool.invoke(state)
    return Command(
        update={"messages": [AIMessage(content=result["messages"][-1].content)]},
        goto=END,
    )



def worker_HR(state: State) -> Command[Literal["__end__"]]:
    result = llm_agent_no_tool.invoke(state)
    return Command(
        update={"messages": [AIMessage(content=result["messages"][-1].content)]},
        goto=END,
    )



def worker_product(state: State) -> Command[Literal["__end__"]]:
    result = llm_agent_no_tool.invoke(state)
    return Command(
        update={"messages": [AIMessage(content=result["messages"][-1].content)]},
        goto=END,
    )
