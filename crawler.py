from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import time
from collections import deque
from dataclasses import dataclass, asdict
from typing import Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from utils.keywords import extract_keywords
from utils.classifier import classify_page
from utils.risk import calculate_risk_score
from utils.user_agents import USER_AGENTS
from utils.content_analysis import detect_language


TOR_PROXIES = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}

REQUEST_TIMEOUT = 20
MAX_LINKS_PER_PAGE = 30
LOG_FILE = "logs/crawler.log"


@dataclass
class PageResult:
    url: str
    depth: int
    status_code: int | None
    title: str | None
    category: str | None
    confidence: float | None
    risk_score: int | None
    risk_label: str | None
    keywords: dict | None
    keywords_count: int
    links: list[str]
    internal_links_count: int
    external_onion_links_count: int
    clearnet_links_count: int
    response_time_ms: int | None
    user_agent: str | None
    meta_description: str | None
    forms_count: int
    password_fields_count: int
    email_fields_count: int
    language: str | None
    error: str | None = None
    error_type: str | None = None


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


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


def choose_user_agent() -> str:
    return random.choice(USER_AGENTS)


def get_proxies_for_url(url: str) -> dict | None:
    if is_onion_url(url):
        return TOR_PROXIES
    return None


def normalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None

    href = href.strip()
    if href.startswith(("mailto:", "javascript:", "#", "tel:")):
        return None

    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)

    if parsed.scheme not in {"http", "https"}:
        return None

    return absolute


def same_host(url_a: str, url_b: str) -> bool:
    return urlparse(url_a).hostname == urlparse(url_b).hostname


def split_links(base_url: str, links: list[str]) -> tuple[list[str], list[str], list[str]]:
    internal = []
    external_onion = []
    clearnet = []

    for link in links:
        if same_host(base_url, link):
            internal.append(link)
        elif is_onion_url(link):
            external_onion.append(link)
        else:
            clearnet.append(link)

    return internal, external_onion, clearnet


def extract_visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = " ".join(text.split())
    return text


def detect_error_type(exc: Exception) -> str:
    message = str(exc).lower()

    if "timed out" in message:
        return "timeout"
    if "connection refused" in message:
        return "connection_refused"
    if "too many redirects" in message:
        return "redirect_loop"
    if "failed to establish a new connection" in message:
        return "connection_failed"

    return "request_error"


def fetch_page(url: str, depth: int) -> PageResult:
    selected_user_agent = choose_user_agent()
    headers = {"User-Agent": selected_user_agent}
    start = time.perf_counter()

    try:
        response = requests.get(
            url,
            headers=headers,
            proxies=get_proxies_for_url(url),
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            logging.warning("Non-HTML content | url=%s | content_type=%s", response.url, content_type)
            return PageResult(
                url=response.url,
                depth=depth,
                status_code=response.status_code,
                title=None,
                category="unknown",
                confidence=0.0,
                risk_score=0,
                risk_label="Low",
                keywords={},
                keywords_count=0,
                links=[],
                internal_links_count=0,
                external_onion_links_count=0,
                clearnet_links_count=0,
                response_time_ms=elapsed_ms,
                user_agent=selected_user_agent,
                meta_description=None,
                forms_count=0,
                password_fields_count=0,
                email_fields_count=0,
                language="unknown",
                error=f"Contenido no HTML: {content_type}",
                error_type="non_html",
            )

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else None

        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_tag.get("content", "").strip() if meta_tag and meta_tag.get("content") else None

        text_content = extract_visible_text(soup)
        keywords = extract_keywords(text_content)
        keywords_count = sum(keywords.values())
        language = detect_language(text_content)

        forms = soup.find_all("form")
        forms_count = len(forms)
        password_fields_count = len(soup.find_all("input", attrs={"type": "password"}))
        email_fields_count = len(soup.find_all("input", attrs={"type": "email"}))
        has_form = forms_count > 0

        raw_links: list[str] = []
        seen_links: Set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            normalized = normalize_url(response.url, a_tag["href"])
            if not normalized:
                continue
            if normalized in seen_links:
                continue
            seen_links.add(normalized)
            raw_links.append(normalized)
            if len(raw_links) >= MAX_LINKS_PER_PAGE:
                break

        internal_links, external_onion_links, clearnet_links = split_links(response.url, raw_links)

        category, confidence = classify_page(
            keywords=keywords,
            has_form=has_form,
            internal_links=len(internal_links),
            external_onion_links=len(external_onion_links),
            clearnet_links=len(clearnet_links),
        )

        risk_score, risk_label = calculate_risk_score(
            keywords=keywords,
            category=category,
            has_form=has_form,
            external_onion_links=len(external_onion_links),
            clearnet_links=len(clearnet_links),
            total_links=len(raw_links),
        )

        logging.info(
            "Fetched | url=%s | depth=%s | status=%s | category=%s | risk=%s",
            response.url,
            depth,
            response.status_code,
            category,
            risk_label,
        )

        return PageResult(
            url=response.url,
            depth=depth,
            status_code=response.status_code,
            title=title,
            category=category,
            confidence=confidence,
            risk_score=risk_score,
            risk_label=risk_label,
            keywords=keywords,
            keywords_count=keywords_count,
            links=raw_links,
            internal_links_count=len(internal_links),
            external_onion_links_count=len(external_onion_links),
            clearnet_links_count=len(clearnet_links),
            response_time_ms=elapsed_ms,
            user_agent=selected_user_agent,
            meta_description=meta_description,
            forms_count=forms_count,
            password_fields_count=password_fields_count,
            email_fields_count=email_fields_count,
            language=language,
            error=None,
            error_type=None,
        )

    except requests.TooManyRedirects as exc:
        error_type = "redirect_loop"
        error_message = str(exc)
    except requests.Timeout as exc:
        error_type = "timeout"
        error_message = str(exc)
    except requests.ConnectionError as exc:
        error_type = detect_error_type(exc)
        error_message = str(exc)
    except requests.RequestException as exc:
        error_type = detect_error_type(exc)
        error_message = str(exc)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    logging.error("Fetch failed | url=%s | depth=%s | error_type=%s", url, depth, error_type)

    return PageResult(
        url=url,
        depth=depth,
        status_code=None,
        title=None,
        category="unknown",
        confidence=0.0,
        risk_score=0,
        risk_label="Low",
        keywords={},
        keywords_count=0,
        links=[],
        internal_links_count=0,
        external_onion_links_count=0,
        clearnet_links_count=0,
        response_time_ms=elapsed_ms,
        user_agent=selected_user_agent,
        meta_description=None,
        forms_count=0,
        password_fields_count=0,
        email_fields_count=0,
        language="unknown",
        error=error_message,
        error_type=error_type,
    )


def load_seed_urls(seed_input: str) -> list[str]:
    if os.path.isfile(seed_input):
        seeds = []
        with open(seed_input, "r", encoding="utf-8") as f:
            for line in f:
                candidate = line.strip()
                if not candidate:
                    continue
                if candidate.startswith(("http://", "https://")):
                    seeds.append(candidate)
        return list(dict.fromkeys(seeds))

    return [seed_input]


def crawl(
    start_urls: list[str],
    max_pages: int = 5,
    max_depth: int = 1,
    delay_seconds: float = 2.0,
) -> list[PageResult]:
    visited: Set[str] = set()
    queue = deque((url, 0) for url in start_urls)
    results: list[PageResult] = []

    while queue and len(results) < max_pages:
        current_url, depth = queue.popleft()

        if current_url in visited:
            continue
        if depth > max_depth:
            continue

        visited.add(current_url)
        result = fetch_page(current_url, depth)
        results.append(result)

        if result.error is None and depth < max_depth:
            for link in result.links:
                if same_host(current_url, link) and link not in visited:
                    queue.append((link, depth + 1))

        time.sleep(delay_seconds)

    return results


def save_results_json(results: list[PageResult], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)


def save_results_csv(results: list[PageResult], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "url",
            "depth",
            "status_code",
            "title",
            "category",
            "confidence",
            "risk_score",
            "risk_label",
            "keywords_count",
            "internal_links_count",
            "external_onion_links_count",
            "clearnet_links_count",
            "response_time_ms",
            "user_agent",
            "meta_description",
            "forms_count",
            "password_fields_count",
            "email_fields_count",
            "language",
            "error_type",
            "keywords",
        ])

        for r in results:
            writer.writerow([
                r.url,
                r.depth,
                r.status_code,
                r.title,
                r.category,
                r.confidence,
                r.risk_score,
                r.risk_label,
                r.keywords_count,
                r.internal_links_count,
                r.external_onion_links_count,
                r.clearnet_links_count,
                r.response_time_ms,
                r.user_agent,
                r.meta_description,
                r.forms_count,
                r.password_fields_count,
                r.email_fields_count,
                r.language,
                r.error_type,
                ",".join(r.keywords.keys()) if r.keywords else "",
            ])


def save_discovered_seeds(results: list[PageResult], output_path: str) -> None:
    discovered = set()

    for result in results:
        for link in result.links:
            if is_onion_url(link):
                discovered.add(link)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for seed in sorted(discovered):
            f.write(seed + "\n")


def save_summary(results: list[PageResult], output_path: str) -> None:
    total_pages = len(results)
    total_errors = sum(1 for r in results if r.error is not None)

    categories = {}
    risk_labels = {}
    languages = {}
    top_keywords = {}

    for r in results:
        categories[r.category] = categories.get(r.category, 0) + 1
        risk_labels[r.risk_label] = risk_labels.get(r.risk_label, 0) + 1
        languages[r.language] = languages.get(r.language, 0) + 1

        if r.keywords:
            for keyword, count in r.keywords.items():
                top_keywords[keyword] = top_keywords.get(keyword, 0) + count

    summary = {
        "total_pages": total_pages,
        "total_errors": total_errors,
        "categories": categories,
        "risk_labels": risk_labels,
        "languages": languages,
        "top_keywords": dict(sorted(top_keywords.items(), key=lambda x: x[1], reverse=True)[:10]),
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def print_summary(results: list[PageResult]) -> None:
    print("\n=== Resumen del crawl ===")
    print(f"Páginas analizadas: {len(results)}")

    for page in results:
        print(f"\nURL: {page.url}")
        print(f"Depth: {page.depth}")
        print(f"Status: {page.status_code}")
        print(f"Título: {page.title}")
        print(f"Categoría: {page.category}")
        print(f"Confianza: {page.confidence}")
        print(f"Risk Score: {page.risk_score}")
        print(f"Risk Label: {page.risk_label}")
        print(f"Keywords: {page.keywords}")
        print(f"User-Agent: {page.user_agent}")
        print(f"Enlaces internos: {page.internal_links_count}")
        print(f"Enlaces onion externos: {page.external_onion_links_count}")
        print(f"Enlaces clearnet: {page.clearnet_links_count}")
        print(f"Tiempo respuesta (ms): {page.response_time_ms}")
        if page.error:
            print(f"Error: {page.error}")
            print(f"Tipo error: {page.error_type}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tor OSINT Crawler")
    parser.add_argument("seed", help="URL .onion inicial o archivo de seeds")
    parser.add_argument("--max-pages", type=int, default=5, help="Número máximo de páginas a visitar")
    parser.add_argument("--max-depth", type=int, default=1, help="Profundidad máxima de crawling")
    parser.add_argument("--delay", type=float, default=2.0, help="Segundos entre requests")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()

    start_urls = load_seed_urls(args.seed)

    if not start_urls:
        raise SystemExit("No se encontraron seeds válidas.")

    results = crawl(
        start_urls=start_urls,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay_seconds=args.delay,
    )

    save_results_json(results, "results/crawl_results.json")
    save_results_csv(results, "results/crawl_results.csv")
    save_discovered_seeds(results, "results/discovered_seeds.txt")
    save_summary(results, "results/summary.json")

    print_summary(results)
    print("\nResultados guardados en results/crawl_results.json")
    print("Resultados guardados en results/crawl_results.csv")
    print("Seeds descubiertas guardadas en results/discovered_seeds.txt")
    print("Resumen guardado en results/summary.json")
    print(f"Log del crawler guardado en {LOG_FILE}")


if __name__ == "__main__":
    main()