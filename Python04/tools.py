# Tool 1) Looking up wikipedia
# Tool 2) Going to DuckDuckGo and searching something
# Tool 3) Custom tool that we write ourself, which can be any python function

from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool
from datetime import datetime

search = DuckDuckGoSearchRun()
search_tool = Tool(
    name = "search",#cannot have any spaces for the name (Use _ or CamelCase)
    func = search.run,
    description= "search the web for information",#Need description so that the agent knows when it should be using this tool
)

api_wrapper = WikipediaAPIWrapper(top_k_results=3, doc_content_chars_max=100)
wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)


# Custom Tool
def save_to_txt(data: str, filename: str = "research_output.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_text = f"--- Research Output ---\nTimestamp: {timestamp}\n\n{data}\n\n"
    
    with open(filename, "a", encoding = "utf-8") as f:
        f.write(formatted_text)
    
    return f"Data successfully saved to {filename}"

save_tool = Tool(name = "save_text_to_file",
                 func = save_to_txt,
                 description = "Saves structured research data to a text file.",
                 )