from __future__ import annotations

from utils.keywords import extract_keywords
from utils.classifier import classify_page

import json
import os
import sys
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Set
from urllib.parse import urljoin, urlparse
import csv

import requests
from bs4 import BeautifulSoup


TOR_PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}

USER_AGENT = "TorOSINTCrawler/1.0 (+research project)"
REQUEST_TIMEOUT = 20
MAX_LINKS_PER_PAGE = 30


@dataclass
class PageResult:
    url: str
    status_code: int | None
    title: str | None
    links: list[str]
    error: str | None = None
    keywords: dict | None = None
    category: str | None = None


def is_onion_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.hostname is not None
            and parsed.hostname.endswith(".onion")
        )
    except Exception:
        return False


def normalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None

    href = href.strip()
    if href.startswith(("mailto:", "javascript:", "#")):
        return None

    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)

    if parsed.scheme not in {"http", "https"}:
        return None

    return absolute


def same_onion_host(url_a: str, url_b: str) -> bool:
    return urlparse(url_a).hostname == urlparse(url_b).hostname


def fetch_page(url: str) -> PageResult:
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(
            url,
            headers=headers,
            proxies=TOR_PROXIES,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return PageResult(
                url=response.url,
                status_code=response.status_code,
                title=None,
                links=[],
                error=f"Contenido no HTML: {content_type}",
            )

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        text_content = soup.get_text(separator=" ")
        keywords = extract_keywords(text_content)
        category = classify_page(keywords)

        links: list[str] = []
        seen_links: Set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            normalized = normalize_url(response.url, a_tag["href"])
            if not normalized:
                continue
            if normalized in seen_links:
                continue
            seen_links.add(normalized)
            links.append(normalized)
            if len(links) >= MAX_LINKS_PER_PAGE:
                break

        return PageResult(
            url=response.url,
            status_code=response.status_code,
            title=title,
            links=links,
            error=None,
            keywords=keywords,
            category=category,
        )

    except requests.RequestException as exc:
        return PageResult(
            url=url,
            status_code=None,
            title=None,
            links=[],
            error=str(exc),
        )


def crawl_onion(start_url: str, max_pages: int = 5, delay_seconds: float = 2.0) -> list[PageResult]:
    if not is_onion_url(start_url):
        raise ValueError("La URL inicial debe ser una dirección .onion válida.")

    visited: Set[str] = set()
    queue = deque([start_url])
    results: list[PageResult] = []

    while queue and len(results) < max_pages:
        current_url = queue.popleft()
        if current_url in visited:
            continue

        visited.add(current_url)
        result = fetch_page(current_url)
        results.append(result)

        if result.error is None:
            for link in result.links:
                if same_onion_host(start_url, link) and link not in visited:
                    queue.append(link)

        time.sleep(delay_seconds)

    return results


def save_results(results: list[PageResult], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)


def save_results_csv(results: list[PageResult], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "url", "status", "title",
            "category", "num_links", "keywords"
        ])

        for r in results:
            writer.writerow([
                r.url,
                r.status_code,
                r.title,
                r.category,
                len(r.links),
                ",".join(r.keywords.keys()) if r.keywords else ""
            ])


def print_summary(results: list[PageResult]) -> None:
    print("\n=== Resumen del crawl ===")
    print(f"Páginas analizadas: {len(results)}")

    for page in results:
        print(f"\nURL: {page.url}")
        print(f"Status: {page.status_code}")
        print(f"Título: {page.title}")
        print(f"Categoría: {page.category}")
        print(f"Keywords: {page.keywords}")
        print(f"Enlaces encontrados: {len(page.links)}")
        if page.error:
            print(f"Error: {page.error}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python crawler.py <url_onion> [max_pages]")
        raise SystemExit(1)

    start_url = sys.argv[1].strip()
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    results = crawl_onion(start_url=start_url, max_pages=max_pages, delay_seconds=2.0)

    save_results(results, "results/crawl_results.json")
    save_results_csv(results, "results/crawl_results.csv")

    print_summary(results)
    print("\nResultados guardados en results/crawl_results.json")
    print("Resultados guardados en results/crawl_results.csv")


if __name__ == "__main__":
    main()