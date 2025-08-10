from mcp.server.fastmcp import FastMCP
from duckduckgo_search import DDGS


mcp = FastMCP("Search MCP Server")



@mcp.tool()
async def duckduckgo_search(query: str) -> list:
    """
    Search the web using DuckDuckGo.
    Returns top 5 results.
    """
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
    return results


if __name__ == "__main__":
    mcp.run(transport="streamable-http")