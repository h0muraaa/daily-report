#!/usr/bin/env python3
"""Fetch arXiv eess.AS papers from RSS first, then recent page fallback."""

from __future__ import annotations

import html as html_lib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from xml.dom import minidom


DEFAULT_RSS_URL = os.environ.get(
    "ARXIV_RSS_URL",
    "https://export.arxiv.org/api/query?search_query=cat:eess.AS&sortBy=submittedDate&sortOrder=descending&max_results=50",
)
DEFAULT_RECENT_URL = os.environ.get(
    "ARXIV_RECENT_URL",
    "https://export.arxiv.org/list/eess.AS/recent",
)
DEFAULT_USER_AGENT = os.environ.get(
    "ARXIV_USER_AGENT",
    "cloud-cron-tasks/1.0 (+https://github.com/seekerzz/cloud_cron_tasks)",
)
ARXIV_BASE_URL = "https://export.arxiv.org"


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape((value or "").strip()))


def _strip_tags(value: str) -> str:
    return _clean_text(re.sub(r"<[^>]+>", " ", value))


def _download_url(url: str, output_path: str, accept: str, retries: int = 3, delay: int = 5) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    last_error: Exception | None = None
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": accept,
        },
    )

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read()
            with open(output_path, "wb") as handle:
                handle.write(payload)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(delay)

    raise RuntimeError(f"Failed to download {url}: {last_error}")


def _make_absolute(url: str) -> str:
    url = _clean_text(url)
    if not url:
        return url
    return urllib.parse.urljoin(ARXIV_BASE_URL, url)


def _extract_authors(block: str) -> list[str]:
    authors = [
        _clean_text(match)
        for match in re.findall(r"<a[^>]*>(.*?)</a>", block, re.S)
    ]
    return [author for author in authors if author]


def _extract_field(block: str, field_class: str) -> str:
    pattern = rf"<div class=['\"]{re.escape(field_class)}['\"][^>]*>.*?<span class=['\"]descriptor['\"]>.*?</span>\s*(.*?)\s*</div>"
    match = re.search(pattern, block, re.S)
    return _strip_tags(match.group(1)) if match else ""


def _fetch_abstract(abs_url: str, cache: dict[str, str]) -> str:
    if abs_url in cache:
        return cache[abs_url]

    candidates = [
        abs_url,
        abs_url.replace("https://export.arxiv.org", "https://arxiv.org"),
    ]

    for candidate in candidates:
        request = urllib.request.Request(
            candidate,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                page = response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError):
            continue

        match = re.search(
            r"<blockquote class=['\"]abstract[^'\"]*['\"]>(.*?)</blockquote>",
            page,
            re.S,
        )
        if match:
            abstract = _strip_tags(match.group(1))
            abstract = re.sub(r"^Abstract:\s*", "", abstract, flags=re.I)
            cache[abs_url] = abstract
            return abstract

    cache[abs_url] = ""
    return ""


def _build_atom_xml(papers: list[dict]) -> str:
    ns = "http://www.w3.org/2005/Atom"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}feed")
    ET.SubElement(root, f"{{{ns}}}title").text = "arXiv eess.AS recent submissions"
    ET.SubElement(root, f"{{{ns}}}id").text = DEFAULT_RSS_URL
    ET.SubElement(root, f"{{{ns}}}updated").text = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for paper in papers:
        entry = ET.SubElement(root, f"{{{ns}}}entry")
        ET.SubElement(entry, f"{{{ns}}}title").text = paper.get("title", "")
        ET.SubElement(entry, f"{{{ns}}}id").text = paper.get("abs_url", "")
        ET.SubElement(entry, f"{{{ns}}}summary").text = paper.get("abstract", "")
        published = paper.get("published", "")
        if published:
            ET.SubElement(entry, f"{{{ns}}}published").text = published
        updated = paper.get("published", "")
        if updated:
            ET.SubElement(entry, f"{{{ns}}}updated").text = updated

        for author_name in paper.get("authors", []):
            author = ET.SubElement(entry, f"{{{ns}}}author")
            ET.SubElement(author, f"{{{ns}}}name").text = author_name

        if paper.get("comments"):
            ET.SubElement(entry, f"{{{ns}}}content").text = f"Comments: {paper['comments']}"

    xml_bytes = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(xml_bytes).toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")


def _parse_atom_xml(xml_path: str) -> list[dict]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    papers: list[dict] = []
    for entry in root.findall("atom:entry", ns):
        papers.append(
            {
                "title": _clean_text(entry.findtext("atom:title", default="", namespaces=ns)),
                "authors": [
                    _clean_text(author.findtext("atom:name", default="", namespaces=ns))
                    for author in entry.findall("atom:author", ns)
                ],
                "abstract": _clean_text(entry.findtext("atom:summary", default="", namespaces=ns)),
                "abs_url": _clean_text(entry.findtext("atom:id", default="", namespaces=ns)),
                "published": _clean_text(entry.findtext("atom:published", default="", namespaces=ns)),
            }
        )

    return papers


def _parse_recent_page(page: str, abstract_cache: dict[str, str]) -> list[dict]:
    papers: list[dict] = []
    entry_pattern = re.compile(r"<dt>(?P<dt>.*?)</dt>\s*<dd>(?P<body>.*?)</dd>", re.S)

    for match in entry_pattern.finditer(page):
        dt_block = match.group("dt")
        body = match.group("body")
        abs_match = re.search(
            r"<a href\s*=\s*['\"](?P<abs_href>/abs/(?P<arxiv_id>[^'\"]+))['\"][^>]*>",
            dt_block,
            re.S,
        )
        if not abs_match:
            continue

        arxiv_id = _clean_text(abs_match.group("arxiv_id"))
        abs_url = _make_absolute(abs_match.group("abs_href"))
        abstract = _fetch_abstract(abs_url, abstract_cache)

        papers.append(
            {
                "arxiv_id": arxiv_id,
                "title": _extract_field(body, "list-title"),
                "authors": _extract_authors(_extract_field(body, "list-authors")),
                "abstract": abstract,
                "comments": _extract_field(body, "list-comments"),
                "subjects": _extract_field(body, "list-subjects"),
                "journal_ref": _extract_field(body, "list-journal-ref"),
                "abs_url": abs_url,
                "published": "",
            }
        )

    return papers


def _convert_recent_page_to_xml(page_path: str, xml_path: str) -> list[dict]:
    if not os.path.exists(page_path):
        _download_url(DEFAULT_RECENT_URL, page_path, "text/html,application/xhtml+xml,*/*")

    with open(page_path, "r", encoding="utf-8", errors="replace") as handle:
        page = handle.read()

    if "<dt>" not in page or "/abs/" not in page:
        _download_url(DEFAULT_RECENT_URL, page_path, "text/html,application/xhtml+xml,*/*")
        with open(page_path, "r", encoding="utf-8", errors="replace") as handle:
            page = handle.read()

    papers = _parse_recent_page(page, {})
    xml_content = _build_atom_xml(papers)

    os.makedirs(os.path.dirname(xml_path), exist_ok=True)
    with open(xml_path, "w", encoding="utf-8") as handle:
        handle.write(xml_content)

    return papers


def parse_arxiv_feed(xml_path: str, recent_path: str, output_path: str) -> list[dict]:
    """Parse RSS query first, then fallback to recent page converted into Atom XML."""
    rss_error: Exception | None = None

    try:
        _download_url(
            DEFAULT_RSS_URL,
            xml_path,
            "application/atom+xml,application/xml,text/xml,*/*",
        )
        papers = _parse_atom_xml(xml_path)
        if papers:
            source = "RSS query"
        else:
            raise ValueError("RSS feed parsed to zero entries")
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError, ValueError) as exc:
        rss_error = exc
        papers = _convert_recent_page_to_xml(recent_path, xml_path)
        source = "recent page fallback"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(papers, handle, indent=2, ensure_ascii=False)

    print(f"解析到 {len(papers)} 篇论文")
    print(f"来源: {source}")
    if rss_error:
        print(f"RSS 回退原因: {rss_error}")
    return papers


if __name__ == "__main__":
    output_dir = os.environ.get("OUTPUT_DIR", "./arxiv-daily-output")
    xml_path = os.path.join(output_dir, "rss_data.xml")
    recent_path = os.path.join(output_dir, "recent_page.html")
    output_path = os.path.join(output_dir, "papers.json")
    parse_arxiv_feed(xml_path, recent_path, output_path)
