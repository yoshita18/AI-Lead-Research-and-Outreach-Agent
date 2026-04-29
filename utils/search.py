from ddgs import DDGS


def search_web(company_name: str, company_url: str) -> dict:
    """Run DuckDuckGo searches for company intelligence signals."""
    domain = company_url.replace("https://", "").replace("http://", "").split("/")[0]
    queries = [
        f"{company_name} company news 2024 2025",
        f"{company_name} funding hiring growth",
        f"{company_name} {domain} CEO founder leadership",
    ]

    results = {}
    with DDGS() as ddgs:
        for query in queries:
            try:
                hits = list(ddgs.text(query, max_results=4))
                results[query] = [
                    {"title": h.get("title", ""), "body": h.get("body", ""), "href": h.get("href", "")}
                    for h in hits
                ]
            except Exception as e:
                results[query] = [{"title": "Search failed", "body": str(e), "href": ""}]

    # Flatten into a single readable block
    flat_lines = []
    for query, hits in results.items():
        flat_lines.append(f"SEARCH: {query}")
        for h in hits:
            flat_lines.append(f"  - {h['title']}: {h['body'][:300]}")
    return {
        "raw": results,
        "summary": "\n".join(flat_lines)[:6000],
    }
