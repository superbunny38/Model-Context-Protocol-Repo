from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio


# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command = "uv", #Executable
    args = "run example_servre.py", # Command line arguments
    env = None, # Environment variables
)

async def run():
    # Launch the server as a subprocess & returns the read and write streams
    # read: the stream that the client will use to read messages from the server
    # write: the stream that client will use to write messages to the server
    
    
    # Context managager
    async with stdio_client(server_params) as (read, write):
        # the Client session is used to initiate the connection
        # and send requests to server
        
        async with ClientSession(read, write) as session:
            # Initialie the connection (1:1 connection with the server)
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            
            #will call the chat_loop here
            # ....
            
            # Call a tool: this will be in the process_query method
            
            result = await session.call_tool("tool-name", arguments={"arg1": "value"})
            
        if __name__ == "__main__":
            asyncio.run(run())