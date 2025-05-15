import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP

PAPER_DIR = "papers"

# Initialize the MCP server
mcp  = FastMCP("Research Paper Search")#name: Research Paper Search


# Tool #1 for the mcp server
@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on the given topics and store their information.
    
    Args:
        topic: The topic to search for
        max_results: The maximum number of results to return (default: 5)
    
    Returns:
        Lis of paper IDs found in the search
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
    
    print("Results are saved in", file_path)
    
    return paper_ids

# Tool #2 for the mcp server
@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to search for
    
    Returns:
        JSON string with paper information if found, error message if not found
    """
    
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r") as f:
                        papers_info = json.load(f)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
    return f"There's no saved information about {paper_id}."


if __name__ == "__main__":
    mcp.run(transport='stdio')