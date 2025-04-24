from typing import Literal, TypedDict
from langgraph.graph import  END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from my_agent.utils.prompts import CHAT_OPTIONS, SYSTEM_PROMPT
from my_agent.utils.state import State
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
# from langchain_mistralai.chat_models import ChatMistralAI
import os
from my_agent.utils.tools import tools

load_dotenv()


llm = ChatOpenAI(
    base_url=os.getenv("SCW_GENERATIVE_APIs_ENDPOINT"),
    api_key=os.getenv("SCW_SECRET_KEY"), 
    model="llama-3.3-70b-instruct",
    # model="mistral-small-3.1-24b-instruct-2503",
    temperature=0.1
)

llm_code = ChatOpenAI(
    base_url=os.getenv("SCW_GENERATIVE_APIs_ENDPOINT"),
    api_key=os.getenv("SCW_SECRET_KEY"), 
    model="qwen2.5-coder-32b-instruct",
    temperature=0.5
)

# llm = ChatAnthropic(
#     api_key=os.getenv("ANTHROPIC_API_KEY"),
#     model="claude-3-5-sonnet-20241022"
# )

# llm = ChatMistralAI(
#     api_key=os.getenv("MISTRAL_API_KEY"),
#     model="mistral-large-latest"
# )

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




def worker_general(state: State) -> Command[Literal[ "__end__"]]:
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

