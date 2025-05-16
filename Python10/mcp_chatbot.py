# adding in prompts and resources

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import json
import asyncio
import nest_asyncio

nest_asyncio.apply()  # Necessary for different operating systems to work in Python


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

class MCP_Chatbot:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=api_key)
        
        # Tools list required for Anthropic API
        self.available_tools = []
        # Prompts list for quick display
        self.available_prompts = []
        # Sessions dict maps tool/prompt names or resource URIs to MCP Client sessions
        self.sessions = {}
    
    async def connect_to_server(self, server_name, server_config):
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            try:
                # List available tools
                response = await session.list_tools()
                for tool in response.tools:
                    self.sessions[tool.name] = session
                    self.available_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema
                    })
                
                #List available prompts
                prompts_response = await session.list_prompts()
                if prompts_response and prompts_response.prompts:
                    for prompt in prompts_response.prompts:
                        self.sessions[prompt.name] = session
                        self.available_prompts.append({
                            "name": prompt.name,
                            "description": prompt.description,
                            "input_schema": prompt.arguments
                        })
                
                #List available resources
                resources_response = await session.list_resources()
                if resources_response and resources_response.resources:
                    for resource in resources_response.resources:
                        resource_url = str(resource.uri)
                        self.sessions[resource_url] = session
            
            except Exception as e:
                print(f"Error listing tools/prompts/resources: {e}")
        except Exception as e:
            print(f"Error connecting to server {server_name}: {e}")
    
    async def connect_to_servers(self):
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        
        except Exception as e:
            print(f"Error reading server configuration: {e}")
            raise
    
    async def process_query(self, query):
        messages = [{'role': 'user', 'content': query}]
        
        while True:
            response = self.anthropic.messages.create(
                max_tokens=2024,
                model='claude-3-7-sonnet-latest',
                tools=self.available_tools,
                messages=messages
            )
            
            assistant_content = []
            has_tool_use = False
            
            for content in response.content:
                if content.type == 'text':
                    print(content.text)
                    assistant_content.append(content)
                elif content.type == 'tool_use':
                    has_tool_use = True
                    assistant_content.append(content)
                    messages.append({'role': 'assistant', 'content': assistant_content})
                    
                    # Get session and call tool
                    session = self.sessions.get(content.name)
                    if not session:
                        print(f"Tool '{content.name}' not found in sessions.")
                        break
                        
                    result = await session.call_tool(content.name, arguments=content.input)
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
                        }]
                    })
            
            # Exit loop if no tool use was found
            if not has_tool_use:
                break
    
    async def get_resource(self, resource_url):
        session = self.sessions.get(resource_url)
        
        # Fallback for papers URIs - try any papers resource session.
        if not session and resource_url.startswith("papers://"):
            for url, sess in self.sessions.items():
                if url.startswith("papers://"):
                    session = sess
                    break
        
        if not session:
            print(f"Resource '{resource_url}' not found in sessions.")
            return 
    
        try:
            result = await session.get_resource(url = resource_url)
            if result and result.contents:
                print(f"Resource '{resource_url}' retrieved successfully.")
                print("Content:")
                print(result.contents[0].text)
            else:
                print("No content available")
                
        except Exception as e:
            print(f"Error retrieving resource {resource_url}: {e}")
    
    async def list_prompts(self):
        """List all available promptss."""
        if not self.available_prompts:
            print("No prompts available.")
            return
        
        print("Available Prompts:")
        for prompt in self.available_prompts:
            print(f"- {prompt['name']}: {prompt['description']}")
            if prompt['arguments']:
                print(f"    Arguments:")
                for arg in prompt['arguments']: