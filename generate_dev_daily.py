#!/usr/bin/env python3
"""Generate developer-practice tech daily from FreshRSS compact JSON."""
import json
import os
import sys
import anthropic

INPUT_JSON = "/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260611_200639.json"
PROMPT_FILE = "/home/runner/work/daily-report/daily-report/.claude/skills/tech-daily-generator/prompts/developer_practice.md"
OUTPUT_DIR = "/home/runner/work/daily-report/daily-report/tech-daily"
MODEL = "claude-sonnet-4-6"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_articles(articles):
    lines = []
    for idx, a in enumerate(articles, 1):
        title = a.get("title", "")
        link = a.get("link", "")
        feed = a.get("feed_title", "")
        author = a.get("author", "")
        summary = a.get("summary", "")
        lines.append(f"[{idx}] {title}")
        lines.append(f"    Source: {feed}")
        if author:
            lines.append(f"    Author: {author}")
        lines.append(f"    Link: {link}")
        lines.append(f"    Summary: {summary}")
        lines.append("")
    return "\n".join(lines)


def main():
    data = load_json(INPUT_JSON)
    articles = data.get("articles", [])
    system_prompt = load_prompt(PROMPT_FILE)

    user_prompt = f"""今天是 {data.get('export_time', '2026-06-11')}。
以下是过去24小时（{data.get('start_time')} 至 {data.get('end_time')}）采集的 {len(articles)} 条科技新闻，每条包含标题、来源、链接和摘要。

请严格遵循开发者实践版人设，从中自主筛选对开发者最有价值的内容，生成一份完整的开发者实践版科技日报HTML文件。

要求：
1. 输出完整、独立的HTML文档（含<head>、<body>、内嵌CSS样式），采用深色代码主题、等宽字体。
2. 日报结构必须包含：今日技术热榜、深度技术解读、工具推荐、实践指南、参考链接汇总。
3. 每条新闻必须有完整总结段落（2-3句话以上），说明是什么、为什么重要、关键细节，并标注来源链接。
4. 使用原文的 link 和 feed_title 字段标注来源，HTML链接格式为：
   <a href="LINK" target="_blank" rel="noopener">[来源: feed_title]</a>
5. 底部“参考链接汇总”列出所有引用的新闻来源。
6. 不要只列标题，不要贴未处理的原文，确保内容专业、有信息增量、可落地。

=== 新闻数据开始 ===
{format_articles(articles)}
=== 新闻数据结束 ===

请直接输出HTML文件完整内容，不要输出任何解释性文字。"""

    client = anthropic.Anthropic()
    print(f"Calling {MODEL} with {len(articles)} articles...", file=sys.stderr)
    html = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            html += text
            if len(html) % 10000 == 0:
                print(f"  received {len(html)} chars...", file=sys.stderr, flush=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "developer_practice.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
