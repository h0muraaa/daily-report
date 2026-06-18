#!/usr/bin/env python3
"""Generate investment analysis HTML daily report from JSON news data."""

import json
import os
import re
from datetime import datetime
from html import escape

import anthropic

INPUT_FILE = "./tech-daily/freshrss_24h_compact_20260618_200609.json"
OUTPUT_FILE = "./tech-daily/investment_analysis.html"
PROMPT_FILE = "./.claude/skills/tech-daily-generator/prompts/investment_analysis.md"

# Investment relevance scoring
INVESTMENT_KEYWORDS = [
    "fund", "funding", "raise", "raised", "series", "valuation", "valued",
    "invest", "investment", "investor", "vc", "venture", "capital",
    "ipo", "acquisition", "acquire", "acquired", "merger", "bought", "buyout",
    "revenue", "profit", "earnings", "stock", "share", "market cap",
    "economy", "financial", "million", "billion", "unicorn", "startup",
    "business model", "pricing", "cost", "expense", "sales", "growth",
    "scale", "scaling", "runway", "burn rate", "unit economics",
    "deepseek", "openai", "anthropic", "claude", "gpt", "agent",
    "compute", "gpu", "cloud", "saas", "platform", "datacenter",
    "ai bubble", "overvalued", "undervalued", "bubble", "crash", "consolidation",
]

HIGH_VALUE_SOURCES = [
    "Y Combinator", "Sequoia", "a16z", "Accel", "Benchmark",
    "TechCrunch", "The Information", "Bloomberg", "Reuters",
    "CNBC", "Wall Street Journal", "Financial Times", "Crunchbase",
    "OpenAI", "Anthropic", "Google", "Microsoft", "Meta",
    "NVIDIA", "Apple", "xAI", "Amazon", "Oracle", "Palantir",
    "a16z", "pmarca", "naval", "Ray Dalio", "Gary Marcus",
]

EXCLUDE_KEYWORDS = [
    "sunlight", "birthday", "spa day", "chair", "homosexuality",
    "molotov", "drone", "ukraine", "warfare", "rogan",
]


def clean_text(text):
    if not text:
        return ""
    # Remove Twitter engagement metrics and noise
    text = re.sub(r"💬\d+🔄\d+❤️\d+👀\d+📊\d+", "", text)
    text = re.sub(r"⚡ Powered by xgo\.ing", "", text)
    text = re.sub(r"🔗 View on Twitter", "", text)
    text = re.sub(r"🔗 View Quoted Tweet", "", text)
    text = re.sub(r"Your browser does not support the video tag\.", "", text)
    return " ".join(text.split()).strip()


def score_article(article):
    title = (article.get("title") or "").lower()
    summary = (article.get("summary") or "").lower()
    feed_title = (article.get("feed_title") or "").lower()
    text = title + " " + summary

    # Exclude low-relevance content
    for kw in EXCLUDE_KEYWORDS:
        if kw in text:
            return 0

    score = 0
    for kw in INVESTMENT_KEYWORDS:
        if kw in text:
            score += 1
    for src in HIGH_VALUE_SOURCES:
        if src.lower() in feed_title:
            score += 2

    # Bonus for articles with substantial summaries
    if len(summary) > 200:
        score += 1

    return score


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    export_time = data.get("export_time", "")

    print(f"Total articles: {len(articles)}")

    scored = []
    for article in articles:
        s = score_article(article)
        if s >= 3:
            scored.append((s, article))

    scored.sort(key=lambda x: x[0], reverse=True)
    selected = scored[:30]

    print(f"Selected {len(selected)} investment-relevant articles")

    # Build article list for prompt
    article_texts = []
    for idx, (score, article) in enumerate(selected, 1):
        title = clean_text(article.get("title", ""))
        summary = clean_text(article.get("summary", ""))
        feed = article.get("feed_title", "")
        link = article.get("link", "")
        article_texts.append(
            f"[{idx}] Title: {title}\nSource: {feed}\nLink: {link}\nSummary: {summary}\n"
        )

    articles_block = "\n".join(article_texts)

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        role_prompt = f.read()

    system_prompt = f"""{role_prompt}

You are generating an investment analysis tech daily report for {data.get('start_time', '')[:10]} to {data.get('end_time', '')[:10]}.

IMPORTANT OUTPUT REQUIREMENTS:
1. Output ONLY a complete, valid HTML document. No markdown, no explanations outside the HTML.
2. Use professional financial report styling: clean, business/finance aesthetic with navy, dark green, gold, or slate tones.
3. Structure the report as:
   - 市场概览 (5-8 key investment/market dynamics)
   - 深度投资分析 (1-2 in-depth analyses)
   - 赛道雷达 (2-4 sectors to watch)
   - 估值观察 (valuation trends/methodology observations)
   - 数据来源声明 (list all sources used, with clickable links)
4. Each news item must have a substantive summary paragraph (2-3+ sentences), explaining what happened, why it matters to investors, and key details.
5. Every news item must cite its source using: <a href="LINK" target="_blank" rel="noopener">[来源: SOURCE_NAME]</a>
6. The bottom 数据来源声明 section must list each unique source with clickable links.
7. The HTML document must be self-contained with CSS in a <style> block.
8. Language: Chinese (Simplified) for the report body.
9. Do not invent facts not present in the provided articles.
10. CRITICAL: Output ONLY the raw HTML. Do NOT wrap the output in markdown code fences (no ```html or ```).
"""

    user_prompt = f"""Below are {len(selected)} articles from the past 24 hours. Generate the investment analysis daily report HTML.

{articles_block}

Generate the complete HTML report now."""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    html = response.content[0].text

    # Strip markdown code fences if present
    html = html.strip()
    if html.startswith("```html"):
        html = html[len("```html"):].strip()
    elif html.startswith("```"):
        html = html[len("```"):].strip()
    if html.endswith("```"):
        html = html[:-len("```")].strip()

    # Ensure output is a complete HTML doc
    if not html.strip().startswith("<!DOCTYPE") and not html.strip().startswith("<html"):
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>投资分析日报</title>
</head>
<body>
{html}
</body>
</html>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nGenerated: {OUTPUT_FILE}")
    print(f"Articles used: {len(selected)}")


if __name__ == "__main__":
    main()
