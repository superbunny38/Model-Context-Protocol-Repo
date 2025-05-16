# Updated code to communicate with multiple servers

'''
- Instead of having one session, you now have a list of client sessions where each client session establishes a 1-to-1 connection to each server;
- available_tools includes the definitions of all the tools exposed by all servers that the chatbot can connect to.
- tool_to_session maps the tool name to the corresponding client session; in this way, when the LLM decides on a particular tool name, you can map it to the correct client session so you can use that session to send tool_call request to the right MCP server.
- exit_stack is a context manager that will manage the mcp client objects and their sessions and ensures that they are properly closed. In lesson 5, you did not use it because you used the with statement which behind the scenes uses a context manager. Here you could again use the with statement, but you may end up using multiple nested with statements since you have multiple servers to connect to. exit_stack allows you to dynamically add the mcp clients and their sessions as you'll see in the code below.
- connect_to_servers reads the server configuration file and for each single server, it calls the helper method connect_to_server. In this latter method, an MCP client is created and used to launch the server as a sub-process and then a client session is created to connect to the server and get a description of the list of the tools provided by the server.
- cleanup is a helper method that ensures all your connections are properly shut down when you're done with them. In lesson 5, you relied on the with statement to automatically clean up resources. This cleanup method serves a similar purpose, but for all the resources you've added to your exit_stack; it closes (your MCP clients and sessions) in the reverse order they were added - like stacking and unstacking plates. This is particularly important in network programming to avoid resource leaks.

'''


from dotenv import load_dotenv
from anthropic import Anthropic

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio

def read_file_to_variable(filepath):
    """
    Reads the entire content of a text file and stores it in a variable.

    Args:
    filepath: The path to the text file.

    Returns:
    A string containing the entire content of the file,
    or None if an error occurs (e.g., file not found).
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            file_content = file.read()
        return file_content
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

api_file_path = "/Users/chaeeunryu/Desktop/MCP Study/key.txt"
api_key = read_file_to_variable(api_file_path)

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict
    
class MCP_ChatBot:
    def __init__(self):
        # Initialize session and client objects
        self.sessions : List[ClientSession] = [] # new
        self.exit_stack = AsyncExitStack() # new
        self.anthropic = Anthropic(api_key=api_key)
        self.available_tools: List[ToolDefinition] = []# new
        self.tool_to_session: Dict[str, ClientSession] = {}# new
    
    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            # initialize the session
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to server {server_name} with tools: {[tool.name for tool in tools]}")
            
            for tool in tools:# new
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })
            
        except Exception as e:
            print(f"Error connecting to server {server_name}: {e}")
    
    async def connect_to_servers(self):
        """Connect to multiple MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)# turn it into a dictionary
            
            servers = data.get("mcpServers",{})
                
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
            
        except Exception as e:
            print(f"Error reading server configuration: {e}")
            raise
    
    async def process_query(self, query):
        messages = [{'role': 'user', 'content': query}]
        response = self.anthropic.messages.create(max_tokens=2024,
                                          model='claude-3-7-sonnet-latest',
                                          tools=self.available_tools,
                                          messages=messages)
        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                    
                    if len(response.content) == 1:
                        process_query = False
                elif content.type == 'tool_use':
                    assistant_content.append(content)
                    messages.append({"role":"assistant", 'content':assistant_content})
                    tool_id, tool_args, tool_name = content.id, content.input, content.name
                    
                    print(f"Calling tool {tool_name} with arguments: {tool_args}")
                    
                    # Call a tool
                    session = self.tool_to_session[tool_name] # new
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    messages.append({"role":"user",
                                        "content":[
                                            {
                                                "type":"tool_result",
                                                "tool_use_id":tool_id,
                                                "content": result.content
                                            }
                                        ]})
                    response = self.anthropic.messages.create(max_tokens=2024,
                                                              model='claude-3-7-sonnet-latest',
                                                              tools=self.available_tools,
                                                              messages=messages)
                    if len(response.content) == 1 and response.content[0].type == 'text':
                        print(response.content[0].text)
                        process_query = False
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\n MCP Chatbot Started!")
        print("Type your queries or type 'quit' to exit.")
        
        while True:
            try:
                query = input("You: ").strip()
                
                if query.lower() == 'quit':
                    break
            
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"Error: {str(e)}\n")
    
    async def cleanup(self):# new
        """Clearly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()
        print("All connections closed.")
        

async def main():
    """Main function to run the chatbot."""
    chatbot = MCP_ChatBot()
    
    try:
        await chatbot.connect_to_servers()# new!
        await chatbot.chat_loop()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await chatbot.cleanup()# new!

if __name__ == "__main__":
    asyncio.run(main())