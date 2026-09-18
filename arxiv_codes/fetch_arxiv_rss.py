#!/usr/bin/env python3
"""Fetch arXiv eess.AS papers from multiple sources, newest-preferring.

来源按「稳定 → 易限流」排序，逐个尝试，任一成功即返回：

1. rss.arxiv.org 分类 RSS —— 官方 feed，一次请求就给全标题/作者/完整摘要，
   不在 export.arxiv.org 那套 API 限流之内（实测稳定 200）。
2. export.arxiv.org/api/query —— 官方 Atom API，按 IP 限速（频发 429）。
3. arxiv.org/list/eess.AS/recent —— 网页兜底，逐篇抓摘要（最慢，最易触发限流）。

前两个都走不通时才会用到第 3 个，且只有在三个来源**全部抛异常**时才判定失败。
"""

from __future__ import annotations

import email.utils
import html as html_lib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone


DEFAULT_RSS_URL = os.environ.get(
    "ARXIV_RSS_URL",
    "https://rss.arxiv.org/rss/eess.AS",
)
DEFAULT_API_URL = os.environ.get(
    "ARXIV_API_URL",
    "https://export.arxiv.org/api/query?search_query=cat:eess.AS&sortBy=submittedDate&sortOrder=descending&max_results=50",
)
DEFAULT_RECENT_URL = os.environ.get(
    "ARXIV_RECENT_URL",
    "https://arxiv.org/list/eess.AS/recent",
)
# arXiv 要求 User-Agent 能标识调用方；旧值指向的是第三方仓库，会被当成爬虫。
DEFAULT_USER_AGENT = os.environ.get(
    "ARXIV_USER_AGENT",
    "daily-report/1.0 (+https://github.com/h0muraaa/daily-report)",
)
ARXIV_BASE_URL = "https://arxiv.org"

RSS_DC_NS = {"dc": "http://purl.org/dc/elements/1.1/"}
# RSS 的 description 前缀形如 "arXiv:2609.17981v1 Announce Type: new \nAbstract: ..."
RSS_DESC_PREFIX_RE = re.compile(r"^arXiv:\S+\s+Announce Type:\s*\S+\s*", re.I)
ABSTRACT_LABEL_RE = re.compile(r"^Abstract:\s*", re.I)


def _clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape((value or "").strip()))


def _strip_tags(value: str) -> str:
    return _clean_text(re.sub(r"<[^>]+>", " ", value))


def _build_opener(use_proxy: bool = False) -> urllib.request.OpenerDirector:
    """Build urllib opener, optionally with proxy from PROXY env var."""
    if use_proxy:
        proxy_url = os.environ.get("PROXY")
        if proxy_url:
            proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


def _download_routes() -> list[tuple[str, bool]]:
    """下载线路：先直连，配了 PROXY 就再从第 2 次尝试起走代理。"""
    routes = [("直连", False)]
    if os.environ.get("PROXY"):
        routes.append(("代理", True))
    return routes


def _download_url(url: str, output_path: str, accept: str, retries: int = 6, delay: int = 5) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    last_error: Exception | None = None
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": accept,
        },
    )
    routes = _download_routes()

    for attempt in range(retries):
        label, use_proxy = routes[min(attempt, len(routes) - 1)]
        opener = _build_opener(use_proxy=use_proxy)
        try:
            with opener.open(request, timeout=30) as response:
                payload = response.read()
            with open(output_path, "wb") as handle:
                handle.write(payload)
            if attempt:
                print(f"（第 {attempt + 1} 次尝试经{label}成功）")
            return
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < retries - 1:
                backoff = delay * (2 ** attempt)
                print(f"下载失败 ({label}, attempt {attempt + 1}/{retries}): {exc}, {backoff}s 后重试...")
                time.sleep(backoff)

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

    candidates = list(
        dict.fromkeys(
            [
                abs_url,
                abs_url.replace("https://export.arxiv.org", "https://arxiv.org"),
            ]
        )
    )
    proxy_url = os.environ.get("PROXY")

    for candidate in candidates:
        request = urllib.request.Request(
            candidate,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        page = None
        for attempt in range(3):
            use_proxy = False
            if attempt > 0 and proxy_url:
                use_proxy = True

            opener = _build_opener(use_proxy=use_proxy)
            try:
                with opener.open(request, timeout=30) as response:
                    page = response.read().decode("utf-8", errors="replace")
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    if attempt == 0 and proxy_url:
                        print(f"429 限流，尝试使用代理获取摘要: {proxy_url}")
                        continue
                    if attempt < 2:
                        time.sleep(5 * (2 ** attempt))
                        continue
                page = None
                break
            except (urllib.error.URLError, TimeoutError, OSError):
                page = None
                break

        if page is None:
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


def _normalize_pubdate(value: str) -> str:
    """'Thu, 17 Sep 2026 00:00:00 -0400' -> '2026-09-17T04:00:00Z'，解析不了就原样返回。"""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value
    if parsed is None:
        return value
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_rss_feed(rss_path: str) -> list[dict]:
    """解析 rss.arxiv.org 的分类 RSS。一次请求即可拿到标题/作者/完整摘要。"""
    tree = ET.parse(rss_path)
    root = tree.getroot()

    papers: list[dict] = []
    for item in root.findall("./channel/item"):
        abs_url = _clean_text(item.findtext("link", default=""))
        if not abs_url:
            continue

        # description 是纯文本：'arXiv:<id>v<n> Announce Type: <type>\nAbstract: <正文>'
        abstract = _clean_text(item.findtext("description", default=""))
        abstract = RSS_DESC_PREFIX_RE.sub("", abstract)
        abstract = ABSTRACT_LABEL_RE.sub("", abstract)

        creators = _clean_text(item.findtext("dc:creator", default="", namespaces=RSS_DC_NS))
        authors = [name for name in (_clean_text(part) for part in creators.split(",")) if name]

        papers.append(
            {
                "title": _clean_text(item.findtext("title", default="")),
                "authors": authors,
                "abstract": abstract,
                "abs_url": abs_url,
                "published": _normalize_pubdate(item.findtext("pubDate", default="")),
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


def _fetch_from_rss_feed(rss_path: str) -> list[dict]:
    _download_url(DEFAULT_RSS_URL, rss_path, "application/rss+xml,application/xml,text/xml,*/*")
    return _parse_rss_feed(rss_path)


def _fetch_from_api(xml_path: str) -> list[dict]:
    _download_url(DEFAULT_API_URL, xml_path, "application/atom+xml,application/xml,text/xml,*/*")
    return _parse_atom_xml(xml_path)


def _fetch_from_recent_page(page_path: str) -> list[dict]:
    if not os.path.exists(page_path):
        _download_url(DEFAULT_RECENT_URL, page_path, "text/html,application/xhtml+xml,*/*")

    with open(page_path, "r", encoding="utf-8", errors="replace") as handle:
        page = handle.read()

    if "<dt>" not in page or "/abs/" not in page:
        _download_url(DEFAULT_RECENT_URL, page_path, "text/html,application/xhtml+xml,*/*")
        with open(page_path, "r", encoding="utf-8", errors="replace") as handle:
            page = handle.read()

    return _parse_recent_page(page, {})


def parse_arxiv_feed(rss_path: str, xml_path: str, recent_path: str, output_path: str) -> list[dict]:
    """逐个来源尝试，任一来源拿到论文即返回。

    三个来源全部抛异常才算抓取失败；只是「今天没有新论文」不该让整个工作流红掉，
    但也不能静默——每种情况都打印出来，避免再出现 find -mtime 那种无声失效。
    """
    sources = (
        ("arXiv 分类 RSS (rss.arxiv.org)", _fetch_from_rss_feed, rss_path),
        ("arXiv Atom API (export.arxiv.org)", _fetch_from_api, xml_path),
        ("arXiv 最新列表页", _fetch_from_recent_page, recent_path),
    )

    errors: list[str] = []
    papers: list[dict] = []
    source = ""
    for label, loader, path in sources:
        try:
            papers = loader(path)
        except Exception as exc:
            errors.append(f"{label}: {type(exc).__name__}: {exc}")
            print(f"⚠️  {label} 抓取失败，换下一个来源...")
            continue
        if papers:
            source = label
            break
        errors.append(f"{label}: 下载成功但解析出 0 篇论文")
        print(f"⚠️  {label} 下载成功但解析出 0 篇论文，换下一个来源...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(papers, handle, indent=2, ensure_ascii=False)

    if not source:
        for line in errors:
            print(f"  ✗ {line}")
        if errors and all("下载成功但解析出 0 篇论文" in line for line in errors):
            print(f"ℹ️  所有来源都能访问，但都没有论文（今天可能没有新提交），写入空的 {output_path}")
            print("解析到 0 篇论文")
            return papers
        raise RuntimeError("所有 arXiv 来源都抓取失败:\n  " + "\n  ".join(errors))

    print(f"解析到 {len(papers)} 篇论文")
    print(f"来源: {source}")
    for line in errors:
        print(f"  （已跳过 {line}）")
    return papers


if __name__ == "__main__":
    output_dir = os.environ.get("OUTPUT_DIR", "./arxiv-daily-output")
    rss_path = os.path.join(output_dir, "rss_feed.xml")
    xml_path = os.path.join(output_dir, "rss_data.xml")
    recent_path = os.path.join(output_dir, "recent_page.html")
    output_path = os.path.join(output_dir, "papers.json")
    parse_arxiv_feed(rss_path, xml_path, recent_path, output_path)
