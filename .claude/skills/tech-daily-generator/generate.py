#!/usr/bin/env python3
"""Generate a role-specific tech daily report from FreshRSS JSON export."""

import argparse
import json
import os
import re
from pathlib import Path

import requests


def load_prompt(role: str) -> str:
    skill_dir = Path(__file__).parent
    prompt_path = skill_dir / "prompts" / f"{role}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Role prompt not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def select_articles(articles: list[dict], max_articles: int = 35) -> list[dict]:
    """Heuristic scoring for developer-relevant articles."""
    dev_keywords = [
        "code", "coding", "programming", "developer", "engineer", "software",
        "github", "git", "api", "framework", "library", "tool", "tools", "ide",
        "visual studio", "vscode", "cli", "command line", "rust", "python",
        "javascript", "typescript", "go ", "golang", "java", "kotlin", "swift",
        "wasm", "webassembly", "docker", "kubernetes", "k8s", "container",
        "database", "sql", "postgres", "mysql", "redis", "mongodb",
        "testing", "test", "ci/cd", "devops", "deployment", "release",
        "version", "update", "bug", "fix", "patch", "security", "vulnerability",
        "performance", "optimization", "optimize", "benchmark", "latency",
        "architecture", "microservice", "serverless", "cloud", "aws", "azure",
        "llm", "machine learning", "open source", "open-source", "tutorial",
        "guide", "how to", "best practice", "lesson", "learn", "build",
        "package", "npm", "pip", "crate", "module", "dependency",
        "linux", "kernel", "browser", "frontend", "backend", "full stack",
    ]
    exclude_keywords = [
        "stock", "stocks", "invest", "investment", "market", "fund", "vc",
        "startup funding", "acquired", "acquisition", "ipo", "earnings",
        "ceo", "diary of a ceo", "political", "trump", "musk", "tesla",
        "youtube short", "sell your", "bubble",
    ]

    def score(a: dict) -> int:
        text = f"{a.get('title', '')} {a.get('summary', '')} {a.get('feed_title', '')}".lower()
        s = sum(1 for kw in dev_keywords if kw in text)
        s -= sum(3 for kw in exclude_keywords if kw in text)
        tech_sources = [
            "infoq", "microsoft for developers", "github", "hacker news",
            "simon willison", "openrouter", "vercel", "cloudflare",
            "freecodecamp", "jetbrains", "google ai developers",
        ]
        if any(src in a.get("feed_title", "").lower() for src in tech_sources):
            s += 2
        return s

    scored = [(score(a), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:max_articles] if _ > 0]


def build_prompt(role_prompt: str, articles: list[dict]) -> str:
    parts = [role_prompt, "\n\n## 输入新闻数据\n\n"]
    for i, a in enumerate(articles, 1):
        title = a.get("title", "")
        summary = a.get("summary", "") or ""
        link = a.get("link", "")
        feed = a.get("feed_title", "")
        # Strip HTML tags from summary for cleaner prompt
        summary_plain = re.sub(r"<[^>]+>", " ", summary)
        summary_plain = re.sub(r"\s+", " ", summary_plain).strip()[:1200]
        parts.append(f"### 新闻 {i}\n")
        parts.append(f"标题: {title}\n")
        parts.append(f"来源: {feed}\n")
        parts.append(f"链接: {link}\n")
        parts.append(f"摘要: {summary_plain}\n\n")
    parts.append(
        "\n\n请基于以上新闻，严格按照开发者实践版人设和日报结构，生成一份完整的HTML科技日报。"
        "必须包含：今日技术热榜、深度技术解读、工具推荐、实践指南、参考链接汇总。"
        "每条新闻必须有2-3句话的完整总结，并标注可点击的来源链接。"
        "只输出完整HTML文档，不要输出其他说明文字。"
    )
    return "".join(parts)


def call_anthropic(prompt: str, timeout: int = 600) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 8192,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = requests.post(
        f"{base_url}/v1/messages",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    return data["content"][0]["text"]


def main():
    parser = argparse.ArgumentParser(description="Generate tech daily report")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--role", required=True, help="Role identifier")
    parser.add_argument("--output", default="./tech-daily/", help="Output directory")
    args = parser.parse_args()

    data = json.load(open(args.input, encoding="utf-8"))
    articles = data.get("articles", [])
    role_prompt = load_prompt(args.role)
    selected = select_articles(articles)
    prompt = build_prompt(role_prompt, selected)

    print(f"Selected {len(selected)} articles out of {len(articles)}")
    html = call_anthropic(prompt)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.role}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
