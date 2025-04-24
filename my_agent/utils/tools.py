import json
from langchain_core.messages import ToolMessage
from my_agent.utils.calendar_tools import  get_calendar_tool, create_calendar_tool


tools = [get_calendar_tool, create_calendar_tool]
