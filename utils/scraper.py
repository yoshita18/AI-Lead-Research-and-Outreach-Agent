import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

MAX_PAGES = 4
TIMEOUT = 10


def _fetch(url: str) -> Optional[str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace
    return " ".join(text.split())


def _get_internal_links(base_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links = set()
    priority_paths = {"about", "product", "solutions", "services", "pricing", "team", "company"}
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        parsed = urlparse(href)
        if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
            path_parts = set(parsed.path.strip("/").split("/"))
            if path_parts & priority_paths:
                links.add(href.split("?")[0].split("#")[0])
    return list(links)[:MAX_PAGES - 1]


def scrape_website(url: str) -> dict:
    """Scrape a company website and return structured text content."""
    if not url.startswith("http"):
        url = "https://" + url

    pages_text = []
    home_html = _fetch(url)

    if not home_html:
        return {"success": False, "content": "", "pages_scraped": 0, "error": "Could not fetch website"}

    home_text = _extract_text(home_html)
    pages_text.append(("home", home_text[:3000]))

    internal_links = _get_internal_links(url, home_html)
    for link in internal_links[:MAX_PAGES - 1]:
        time.sleep(0.5)
        html = _fetch(link)
        if html:
            text = _extract_text(html)
            page_name = urlparse(link).path.strip("/").split("/")[0] or "page"
            pages_text.append((page_name, text[:2000]))

    combined = "\n\n".join(f"[{name.upper()} PAGE]\n{text}" for name, text in pages_text)
    return {
        "success": True,
        "content": combined[:8000],
        "pages_scraped": len(pages_text),
        "error": None,
    }
