import asyncio
import os
from pathlib import Path

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator
from rich import print

app = MCPApp(name="science_report_orchestrator")

async def example_usage():
    async with app.run() as research_app:
        logger = research_app.logger
        context = research_app.context
        
        # Add current directory to filesystem server
        context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

        # Research Agents
        search_agent = Agent(
            name="searcher",
            instruction="""You are an expert web researcher. Your role is to:
            1. Search for relevant, authoritative sources on the given topic
            2. Visit the most promising URLs to gather detailed information
            3. Return a structured summary of your findings with source URLs
            
            Focus on high-quality sources like academic papers, respected tech publications,
            and official documentation.
            
            Save each individual source in the output/sources/ folder. We only need up to 10 sources max.
            """,
            server_names=["brave", "fetch", "filesystem"],
        )

        # Fact Checker Agent
        fact_checker = Agent(
            name="fact_checker",
            instruction="""You are a meticulous fact checker. Your role is to:
            1. Verify claims by cross-referencing sources
            2. Check dates, statistics, and technical details for accuracy
            3. Identify any contradictions or inconsistencies
            """,
            server_names=["brave", "fetch", "filesystem"],
        )

        # Report Writer Agent
        report_writer = Agent(
            name="writer",
            instruction="""You are a technical report writer specializing in research 
            documents. Your role is to:
            1. Create well-structured, professional reports
            2. Include proper citations and references
            3. Balance technical depth with clarity
            
            Save your report to the filesystem with appropriate formatting.
            """,
            server_names=["filesystem", "fetch"],
        )

        # Read the research task
        task_path = Path("task.md")
        with open(task_path, 'r') as f:
            task = f.read()

        # Create orchestrator with all agents
        orchestrator = Orchestrator(
            llm_factory=AnthropicAugmentedLLM,
            available_agents=[
                search_agent,
                fact_checker,
                report_writer,
            ],
            plan_type="full",
            plan_output_path=Path("output/execution_plan.md"),
            max_iterations=5
        )

        # Execute the research task
        result = await orchestrator.generate_str(
            message=task,
            request_params=RequestParams(
                model="claude-3-5-haiku-20241022",
                maxTokens=8192
            )
        )
        logger.info(f"Research task completed: {result}")

if __name__ == "__main__":
    import time
    start = time.time()
    asyncio.run(example_usage())
    end = time.time()
    print(f"Total research time: {end - start:.2f}s")