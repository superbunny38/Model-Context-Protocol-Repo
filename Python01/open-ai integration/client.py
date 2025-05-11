import asyncio
import json
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

import nest_asyncio
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

# How do we build client that can interact with mcp server 
# get tools from the mcp server
# and use those and integrate them with AI

# Apply nest_ayncio to allow nested event loops (needed for Jupyter/IPytyhon)
nest_asyncio.apply()

# Load environment variables
load_dotenv("../.env")

class MCPOpenAIClient:
    """ Client for interacting with OpenAI models using MCP tools."""
    
    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize the OpenAI MCP Client.
        
        Args:
            model: The OpenAI model to use.
        """
        
        # Initialize session and client objects