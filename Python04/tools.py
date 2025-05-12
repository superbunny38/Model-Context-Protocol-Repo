# Tool 1) Looking up wikipedia
# Tool 2) Going to DuckDuckGo and searching something
# Tool 3) Custom tool that we write ourself, which can be any python function

from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime

search = DuckDuckGoSearchRun()
search_tool = Tool(
    name = "search"
)