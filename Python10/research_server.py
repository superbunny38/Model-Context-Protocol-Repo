# Updated version of server.py

import os
import json
import arxiv   
from typing import List
from mcp.server.fastmcp import FastMCP

PAPER_DIR = "/Users/chaeeunryu/Desktop/MCP Study/MCP-Python/Python10/papers"

# Initialize the MCP server
mcp = FastMCP("Research Paper Search")  # name: Research Paper Search


# Tool #1 for the mcp server
@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arxiv based on the given topics and store their information.
    
    Args:
        topic: The topic to search for
        max_results: The maximum number of results to return (default: 5)
    
    Returns:
        List of paper IDs found in the search
    """
    
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    
    papers = client.results(search)
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")
    
    try:
        with open(file_path, "r") as f:
            papers_info = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}
    
    
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    with open(file_path, "w") as f:
        json.dump(papers_info, f, indent=2)
    
    print("Results saved to:", file_path)
    return paper_ids


# Tool #2 for the mcp server
@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Extract information about a specific paper using its ID.
    
    Args:
        paper_id: The ID of the paper to extract information from.
    
    Returns:
        A string containing the title, authors, summary, and publication date of the paper.
    """
    
    for item in os.listdir(PAPER_DIR):
        path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(path):
            file_path = os.path.join(path, "papers_info.json")
            try:
                with open(file_path, "r") as f:
                    papers_info = json.load(f)
                    if paper_id in papers_info:
                        return json.dumps(papers_info[paper_id], indent=2)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading file {file_path}: {e}")
                continue
    return f"There's no information about {paper_id}."


@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the paper directory.
    
    This resource provides a simple list of all available topic folders.
    """
    
    folders = []
    
    # Get all topic directories.
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                
                if os.path.exists(papers_file):
                    folders.append(topic_dir)
    
    content = "# Available Topics\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\n Use @{folder} to access papers in that topic. \n"
    else:
        content += "No topics found.\n"
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detailed information about papers on a specific topic.
    
    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")
    
    if not os.path.exists(papers_file):
        return f"No papers found for topic: {topic}. "
    
    try:
        with open(papers_file, "r") as f:
            papers_data = json.load(f)
            
        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"
        
        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n"
            content += f"- **Summary**: {paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"
        return content
            
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\n The paper data file is corrupted"
        
@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    
    """
    Generate a prompt for Claude to find and discuss academic papers on a specific topic.
    """
    
    prompt_str = """Search for {num_papers} academic papers on '{topic}' \
        using the search_papers tool.
        Follow these instructions:
        1. First, search for papers using the search_papers(topic = '{topic}', max_results = {num_papers}).
        2. For each paper found, extract and organize the following information:
            - Paper title
            - Authors
            - Publication date
            - Brief summary of the key findings
            - Main contributions or innovations
            - Methodologies used
            - Relevance to the topic '{topic}'
        3. Provide a comprehensive summary that includes:
            - Overview of the current state of research in '{topic}'
            - Common themes and trends across the papers
            - Key research gaps or areas for future investigation
            - Most impactful or influential papers in this area
        4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.
    
        Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}.
    """
    return prompt_str

if __name__ == "__main__":
    # Run the server
    mcp.run(transport='stdio')