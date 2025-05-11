import os
import json
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(
    name = "Knowledge Base",
    host = "0.0.0.0", # only used for SSE trannsport (localhost)
    port = 8050, # only used for SSE transport (set this to any port)
)

@mcp.tool()
def get_knowledge_base() -> str:
    """
    Retrieve the entire knowledge base as a formatted string.
    
    Returns:
        A formatted string containing all Q&A pairs from the knowledge base.
    """
    