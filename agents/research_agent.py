"""Stage 2: Web Research Agent — parallel scrape + web search."""
import concurrent.futures
from utils.scraper import scrape_website
from utils.search import search_web


def _extract_company_name(url: str) -> str:
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    name = domain.replace("www.", "").split(".")[0]
    return name.replace("-", " ").replace("_", " ").title()


def run_research(company_url: str) -> dict:
    """Scrape the website and search the web in parallel. Returns raw intelligence."""
    company_name = _extract_company_name(company_url)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        scrape_future = executor.submit(scrape_website, company_url)
        search_future = executor.submit(search_web, company_name, company_url)

        scrape_result = scrape_future.result()
        search_result = search_future.result()

    return {
        "company_name": company_name,
        "company_url": company_url,
        "scraped": scrape_result,
        "searched": search_result,
    }
