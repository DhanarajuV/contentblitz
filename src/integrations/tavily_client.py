import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search(query: str, max_results: int = 5, days: int = None) -> str:
    """Search the web and return formatted results with sources."""
    kwargs = {"max_results": max_results}
    if days:
        kwargs["days"] = days

    response = _client.search(query, **kwargs)
    results = response.get("results", [])

    # Fallback: if days filter returns nothing, retry without it
    if not results and days:
        response = _client.search(query, max_results=max_results)
        results = response.get("results", [])

    if not results:
        return "No results found."

    output = ""
    for i, r in enumerate(results, 1):
        title = r.get("title", "")
        url = r.get("url", "")
        content = r.get("content", "")[:300]
        output += f"[{i}] {title}\n    URL: {url}\n    {content}\n\n"

    return output

if __name__ == "__main__":
    print(search("latest trends in content marketing 2026"))