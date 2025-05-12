from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from tools import search_tool, wiki_tool

load_dotenv("../.env")#Load dot env file

# Define a simple Python class which will specify the type of the content that we want our LLM to generate
class ResearchResponse(BaseModel):#Pydantic model
    # Specify all of the fields that you want as output from your LLM call (can be as complex as you want)
    topic: str
    summary: str
    sources: list[str]
    tools_used: list[str]
    
#Set up an LLM
llm = ChatAnthropic(model = "claude-3-5-sonnet-20241022")# Claude model
# response = llm.invoke("Hi is building mcp (model context protocol) server \
#     and let it interact with other llms \
#         and other mcp servers\
#             and make it access internal data storage hard?")
# print(response)


# Set up parser (You could use json file instead to set up parser)
# This parser would allow us to take the output of the llm and parse it into the ResearchResponse model
# And we could use it like a normal python object inside of our code
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

# Prompt Templates
# Uses the parser and takes the pydantic model and turns it into the string that we can then give to the prompt
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a research assistant that will help generate a research paper.
            Answer the user query and use necessary tools.
            Wrap the output in this format and provide no other text\n{format_instructions}
            """,
        ),
        #following info can be found in langchain doc
        ("placeholder", "{chat_history}"),#agent executor fills this in automatically
        ("human", "{query} {name}"),#query: coming from the user
        ("placeholder", "{agent_scratchpad}"),#agent executor fills this in automatically
    ]
).partial(format_instructions = parser.get_format_instructions())# We are partially going to filll in this prompt by passing in the 'format_instructions'



tools = [search_tool, wiki_tool]

# Create agent
agent = create_tool_calling_agent(
    llm = llm,
    prompt = prompt,
    tools = tools#tools: things that the LLM/agent can use that we can either write ourself or we can bring in from things like the Langchain Community Hub
)

# Execute agent
agent_executor = AgentExecutor(agent = agent, tools = tools, verbose = True)#verbose = True: we can see the thought process of the agent

# query = input("What is the capital of France?")
# name = input("Name?")
# raw_response = agent_executor.invoke({"query":query, "name":name})

query = input("What can I help you research?:")
name = input("Who are you?:")
raw_response = agent_executor.invoke({"query":query,"name":name})
print(raw_response)
print("\n\n")

try:
    structured_response = parser.parse(raw_response.get("output")[0]["text"])
    print(structured_response)
    print("\n\n")

    print("Topic:",structured_response.topic)
    print("\n\n")
except Exception as e:
    print("Error parsing response ",e,"Raw Response - ",raw_response)

# try:
#     structured_response = parser.parse(raw_response.get("output")[0]["text"])
#     print(structured_response)
# except Exception as e:
#     print("Error parsing response",e,"Raw Response - ", raw_response)