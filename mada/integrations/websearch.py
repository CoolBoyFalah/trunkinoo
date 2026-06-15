from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 6) -> list[dict]:
    """Search the web using DuckDuckGo. Returns list of {title, href, body}."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))
    return results
