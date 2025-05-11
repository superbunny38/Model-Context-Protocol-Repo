import asyncio
import nest_asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

nest_asyncio.apply()

async def main():
    server_params = StdioServerParameters(
        command = "python",
        
    )