# Side-by-Side Comparison
# Let's compare our MCP implementation to a traditional function-calling approach in function-calling.py

# At this small scale, the traditional approach is simpler. The key differences become apparent when:

# Scale increases: With dozens of tools, the MCP approach provides better organization
# Reuse matters: The MCP server can be used by multiple clients and applications
# Distribution is needed: MCP provides standard mechanisms for remote operation

# When to Use MCP vs. Traditional Approaches
# Consider MCP when:

# You need to share tool implementations across multiple applications
# You're building a distributed system with components on different machines
# You want to leverage existing MCP servers from the ecosystem
# You're building a product where standardization provides user benefits

import json

import openai
from dotenv import load_dotenv
from tools import add

load_dotenv("../.env")#api key


"""
This is a simple example to demonstrate that MCP simply enables a new way to call functions.
"""

# Define tools for the model

tools = [
    {
        "type": "function",
        "function":{
            "name": "add",
            "description": "Add two numbers together",
            "parameters": {
                "type": "object",
                "properties":{
                    "a": {"type":"integer", "description":"First number"},
                    "b": {"type":"integer", "description":"Second number"},
                },
                "required": ["a","b"],
            },
        },
    }
]

# Call LLM
response = openai.chat.completions.create(
    model = "gpt-4o",
    messages = [{"role":"user","content":"Calculate 25 + 17"}],
    tools = tools,
)


# Handle tool calls
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)
    
    # Execute directly
    result = add(**tool_args)
    
    # Send result back to model
    final_response = openai.chat.completions.create(
        model = "gpt-4o",
        messages=[
            {"role":"user","content":"Calcualte 25 + 17"},
            response.choices[0].message,
            {"role":"tool", "tool_call_id":tool_call.id, "content": str(result)},
        ],
    )
    print(final_response.choices[0].message.content)