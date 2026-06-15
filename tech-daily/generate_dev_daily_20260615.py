#!/usr/bin/env python3
"""Generate developer practice daily tech report for 2026-06-15."""

import json
import os
import urllib.request
import urllib.error
from html import escape
from datetime import datetime

INPUT_JSON = "/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260615_204209.json"
PROMPT_FILE = "/home/runner/work/daily-report/daily-report/.claude/skills/tech-daily-generator/prompts/developer_practice.md"
OUTPUT_DIR = "/home/runner/work/daily-report/daily-report/tech-daily"
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.kimi.com/coding")
MODEL = "kimi-for-coding"


def load_articles():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("articles", []), data.get("export_time", "")


def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def clean_article(a):
    """Keep only fields needed for generation."""
    return {
        "title": a.get("title", ""),
        "link": a.get("link", ""),
        "feed_title": a.get("feed_title", ""),
        "summary": a.get("summary", ""),
    }


def is_dev_relevant(article):
    """Filter out obvious non-dev content."""
    title = article.get("title", "")
    summary = article.get("summary", "")
    feed = article.get("feed_title", "")
    text = (title + " " + summary).lower()

    # Drop very short social-only noise
    if len(summary) < 12:
        return False

    keywords = [
        "code", "coding", "programming", "developer", "engineer", "software",
        "open source", "github", "api", "framework", "library", "sdk", "tool",
        "tools", "cli", "ide", "devops", "ci/cd", "docker", "kubernetes", "cloud",
        "server", "backend", "frontend", "web", "app", "python", "javascript",
        "typescript", "rust", "golang", "go ", "java", "react", "vue", "angular",
        "node.js", "next.js", "database", "sql", "llm", "rag", "fine-tuning",
        "embedding", "vector", "benchmark", "performance", "optimization",
        "testing", "security", "debug", "architecture", "microservice", "monorepo",
        "container", "serverless", "tensorflow", "pytorch", "huggingface",
        "langchain", "langsmith", "openai", "anthropic", "gemini", "cursor",
        "windsurf", "copilot", "cline", "agent", "agents", "prompt engineering",
        "spring", "boot", "aws", "gcp", "azure", "vercel", "cloudflare",
        "mermaid", "katex", "markdown", "workflow", "sandbox", "mcp",
    ]

    tech_feeds = {
        "InfoQ", "Cloud Blog", "Vercel News", "Simon Willison's Weblog",
        "Simon Willison(@simonw)", "LangChain(@LangChainAI)", "OpenAI",
        "The GitHub Blog", "GitHub(@github)", "AWS Architecture Blog",
        "The Cloudflare Blog", "Visual Studio Blog", "The JetBrains Blog",
        "Stack Overflow Blog", "ByteByteGo Newsletter", "AI SDK(@aisdk)",
        "freeCodeCamp Programming Tutorials: Python， JavaScript， Git ＆ More",
        "freeCodeCamp.org",
    }

    has_kw = any(kw in text for kw in keywords)
    is_tech_feed = feed in tech_feeds
    return has_kw or is_tech_feed


def score_article(a):
    """Score by depth and dev relevance."""
    score = 0
    title = a.get("title", "")
    summary = a.get("summary", "")
    feed = a.get("feed_title", "")
    text = (title + " " + summary).lower()

    if len(summary) > 400:
        score += 4
    elif len(summary) > 200:
        score += 3
    elif len(summary) > 100:
        score += 1
    else:
        score -= 2

    depth = [
        "architecture", "benchmark", "performance", "optimization", "deployment",
        "pipeline", "testing", "debug", "kernel", "cuda", "gpu", "security",
        "vulnerability", "cve", "open source", "repository", "release",
    ]
    for d in depth:
        if d in text:
            score += 1

    if feed in {"InfoQ", "Cloud Blog", "The GitHub Blog", "Vercel News", "AWS Architecture Blog"}:
        score += 2
    if feed in {"LangChain(@LangChainAI)", "OpenAI", "Simon Willison's Weblog", "Simon Willison(@simonw)"}:
        score += 1

    return score


def curate_articles(articles, max_per_feed=2, total_target=90):
    """Curate articles with per-feed caps and scoring."""
    filtered = [clean_article(a) for a in articles if is_dev_relevant(a)]
    filtered = [(a, score_article(a)) for a in filtered]
    filtered.sort(key=lambda x: x[1], reverse=True)

    feed_counts = {}
    result = []
    for a, _ in filtered:
        feed = a["feed_title"]
        if feed_counts.get(feed, 0) >= max_per_feed:
            continue
        result.append(a)
        feed_counts[feed] = feed_counts.get(feed, 0) + 1
        if len(result) >= total_target:
            break
    return result


def build_generation_prompt(role_prompt, articles, export_time):
    today = datetime.now().strftime("%Y-%m-%d")
    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)

    return f"""{role_prompt}

今天是 {today}。以下是从 FreshRSS 抓取的最新技术新闻（导出时间：{export_time}），共 {len(articles)} 条候选。

请基于这些候选新闻，严格以"开发者实践版"角色视角：
1. 自主筛选出最有价值的 10-14 条内容。
2. 将筛选出的内容组织成以下结构：
   - 今日技术热榜（5-7 条）
   - 深度技术解读（1-2 条）
   - 工具推荐（2-3 条）
   - 实践指南（2-3 条）
   - 参考链接汇总（列出所有引用来源的 feed_title 和 link）
3. 每条新闻必须有完整的总结段落（至少 2-3 句话），说明是什么、为什么重要、关键细节。
4. 每条新闻必须标注来源，HTML 格式：
   <a href="原始链接" target="_blank" rel="noopener">[来源: 网站名]</a>
5. 底部"参考链接汇总"使用源名称作为链接文本，列出所有来源。
6. 生成完整、独立的 HTML 文件（含 CSS 样式）。开发者版使用深色代码主题、等宽字体。
7. 只输出 HTML 代码，不要输出 markdown 代码块标记或其他说明文字。

候选新闻数据：
{articles_json}
"""


def call_api(prompt, max_tokens=12000):
    url = f"{BASE_URL.rstrip('/')}/v1/messages"
    payload = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "enabled", "budget_tokens": 8192},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_html(response):
    content = response.get("content", [])
    text_parts = []
    for block in content:
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
    text = "".join(text_parts)
    # Strip markdown code fences if any
    text = text.strip()
    if text.startswith("```html"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def main():
    articles, export_time = load_articles()
    role_prompt = load_prompt()
    curated = curate_articles(articles, max_per_feed=2, total_target=90)
    print(f"Loaded {len(articles)} articles, curated to {len(curated)}.")

    prompt = build_generation_prompt(role_prompt, curated, export_time)
    print(f"Prompt length: {len(prompt)} chars")

    response = call_api(prompt, max_tokens=16000)
    html = extract_html(response)

    output_path = os.path.join(OUTPUT_DIR, "developer_practice.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Generated: {output_path} ({len(html)} chars)")


if __name__ == "__main__":
    main()
