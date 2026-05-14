#!/usr/bin/env python3
"""
生成开发者实践版科技日报
"""
import json
import re
from datetime import datetime

INPUT_FILE = "/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260514_192521.json"
OUTPUT_FILE = "/home/runner/work/daily-report/daily-report/tech-daily/developer_practice.html"

# 开发者相关关键词（用于筛选和排序）
DEV_KEYWORDS = {
    "high": [
        "API", "SDK", "CLI", "GitHub", "git", "Docker", "Kubernetes", "k8s",
        "Rust", "Go ", "Golang", "Python", "JavaScript", "TypeScript", "Node.js",
        "React", "Vue", "Angular", "Next.js", "Nuxt", "Svelte",
        "framework", "library", "package", "npm", "pip", "cargo",
        "database", "SQL", "PostgreSQL", "MongoDB", "Redis",
        "CI/CD", "DevOps", "testing", "benchmark", "performance",
        "open source", "开源", "release", "version", "update", "changelog",
        "tutorial", "guide", "how to", "best practice", "pattern",
        "compiler", "interpreter", "runtime", "engine",
        "Linux", "kernel", "WSL", "terminal", "shell", "bash", "zsh",
        "VS Code", "IDE", "editor", "plugin", "extension",
        "cloud", "AWS", "Azure", "GCP", "serverless", "edge",
        "WebAssembly", "WASM", "microservice", "monolith", "architecture",
        "encryption", "security", "vulnerability", "CVE",
        "LLM", "model", "inference", "GPU", "CPU", "optimization",
        "code", "programming", "developer", "engineer", "build", "deploy"
    ],
    "medium": [
        "AI", "machine learning", "deep learning", "neural",
        "prompt", "agent", "automation", "workflow",
        "blockchain", "web3", "crypto",
        "frontend", "backend", "fullstack", "stack",
        "REST", "GraphQL", "gRPC", "WebSocket", "HTTP",
        "CSS", "HTML", "DOM", "browser", "web",
        "mobile", "iOS", "Android", "Flutter", "React Native",
        "cache", "memory", "storage", "disk", "I/O",
        "async", "sync", "parallel", "concurrent", "thread",
        "JSON", "XML", "YAML", "TOML", "protobuf",
        "OAuth", "JWT", "authentication", "authorization",
        "log", "monitoring", "observability", "tracing",
        "refactor", "debug", "bug", "fix", "patch",
        "specification", "RFC", "standard", "protocol"
    ]
}

EXCLUDE_KEYWORDS = [
    "stock", "shares", "invest", "fundraising", "IPO", "valuation",
    "acquisition", "acquired", "merger",
    "hired", "appointed", "CEO", "CTO", "VP", "executive", "leader",
    "layoff", "fired", "resigned", "departed",
    "lawsuit", "legal", "regulation", "regulator",
    "rumor", " reportedly", "allegedly",
    "travel", "vacation", "hiking", "backpack",
    "watch this", "tune in", "live stream", "podcast",
    "Form 1", "Form 2", "general contact",
    "just published a photo", "just posted a video"
]


def score_article(article):
    """给文章打分，分数越高越适合开发者"""
    text = f"{article.get('title', '')} {article.get('summary', '')} {article.get('feed_title', '')}"
    text_lower = text.lower()

    # 排除明显不相关的内容
    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in text_lower:
            return -100

    score = 0
    for kw in DEV_KEYWORDS["high"]:
        if kw.lower() in text_lower:
            score += 3
    for kw in DEV_KEYWORDS["medium"]:
        if kw.lower() in text_lower:
            score += 1

    # 有summary的内容更有价值
    if article.get('summary') and len(article.get('summary', '')) > 50:
        score += 2

    # 来源加权
    dev_sources = [
        "GitHub", "Hacker News", "Dev.to", "Stack Overflow",
        "Mozilla", "Vercel", "Cloudflare", "Tailwind",
        "React", "Vue.js", "Angular", "Node.js",
        "Rust", "Go ", "Python", "JavaScript",
        "Docker", "Kubernetes", "Linux",
        "AWS", "Google Cloud", "Azure",
        "MDN", "Web.dev", "CSS-Tricks",
        "InfoQ", "The New Stack", "DevOps",
        "Ars Technica", "Wired", "TechCrunch"
    ]
    feed_title = article.get('feed_title', '')
    for src in dev_sources:
        if src.lower() in feed_title.lower():
            score += 2
            break

    return score


def clean_text(text):
    """清理文本中的HTML实体和多余空白"""
    if not text:
        return ""
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def clean_summary(summary):
    """清理summary中的社交媒体统计信息"""
    if not summary:
        return ""
    # 移除社交媒体统计
    summary = re.sub(r'💬\d+🔄\d+❤️\d+👀\d+📊\d+.*$', '', summary)
    summary = re.sub(r'⚡ Powered by xgo\.ing', '', summary)
    summary = re.sub(r'🔗 View on \w+', '', summary)
    summary = re.sub(r'Your browser does not support the video tag\.', '', summary)
    summary = clean_text(summary)
    return summary


def generate_html(articles, export_time):
    """生成HTML日报"""
    date_str = export_time.split()[0] if export_time else datetime.now().strftime('%Y-%m-%d')

    # 取前30条最有价值的内容
    scored = [(a, score_article(a)) for a in articles]
    scored = [(a, s) for a, s in scored if s > 0]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_articles = scored[:30]

    # 分类
    hot_news = []      # 今日技术热榜
    deep_dive = []     # 深度技术解读
    tools = []         # 工具推荐
    guides = []        # 实践指南

    for article, score in top_articles:
        title_lower = article.get('title', '').lower()
        summary_lower = article.get('summary', '').lower()
        combined = title_lower + ' ' + summary_lower

        if any(kw in combined for kw in ['release', 'version', 'update', 'launch', 'announce', 'beta', 'alpha', 'new', '开源', 'open source']):
            hot_news.append(article)
        elif any(kw in combined for kw in ['tool', 'library', 'package', 'npm', 'plugin', 'extension', 'cli', 'sdk', 'framework']):
            tools.append(article)
        elif any(kw in combined for kw in ['guide', 'tutorial', 'how to', 'best practice', 'pattern', 'tip', 'trick', 'cheatsheet']):
            guides.append(article)
        else:
            deep_dive.append(article)

    # 确保每个分类都有内容
    all_selected = []
    all_selected.extend(hot_news[:10])
    all_selected.extend(deep_dive[:8])
    all_selected.extend(tools[:6])
    all_selected.extend(guides[:6])

    # 去重
    seen_links = set()
    unique_selected = []
    for a in all_selected:
        link = a.get('link', '')
        if link and link not in seen_links:
            seen_links.add(link)
            unique_selected.append(a)

    # 重新分配
    hot_news = unique_selected[:8]
    deep_dive = unique_selected[8:14]
    tools = unique_selected[14:20]
    guides = unique_selected[20:26]

    # 收集所有来源
    sources = {}
    for a in unique_selected:
        link = a.get('link', '')
        feed = a.get('feed_title', '未知来源')
        if feed not in sources:
            sources[feed] = set()
        sources[feed].add(link)

    def render_article_card(article):
        title = clean_text(article.get('title', '无标题'))
        summary = clean_summary(article.get('summary', ''))
        link = article.get('link', '#')
        feed = clean_text(article.get('feed_title', '未知来源'))

        # 如果summary为空或太短，用title填充
        if not summary or len(summary) < 20:
            summary = title

        # 截断过长的summary
        if len(summary) > 500:
            summary = summary[:500] + '...'

        return f'''
        <article class="news-card">
            <h3 class="news-title">{title}</h3>
            <p class="news-summary">{summary}</p>
            <div class="news-meta">
                <a href="{link}" target="_blank" rel="noopener">[来源: {feed}]</a>
            </div>
        </article>
        '''

    def render_section(title, articles, icon):
        if not articles:
            return ""
        cards = "\n".join(render_article_card(a) for a in articles)
        return f'''
        <section class="section">
            <h2 class="section-title">{icon} {title}</h2>
            <div class="news-grid">
                {cards}
            </div>
        </section>
        '''

    # 来源汇总
    source_links = []
    for feed, links in sorted(sources.items()):
        for link in sorted(links)[:3]:  # 每个来源最多3条
            source_links.append(f'<li><a href="{link}" target="_blank" rel="noopener">{feed}</a></li>')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>开发者实践日报 - {date_str}</title>
    <style>
        :root {{
            --bg-primary: #0d1117;
            --bg-secondary: #161b22;
            --bg-card: #21262d;
            --border: #30363d;
            --text-primary: #c9d1d9;
            --text-secondary: #8b949e;
            --accent: #58a6ff;
            --accent-green: #3fb950;
            --accent-yellow: #d29922;
            --accent-purple: #a371f7;
            --code-bg: #1e2530;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.7;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 40px;
        }}
        .date-badge {{
            display: inline-block;
            background: var(--bg-card);
            border: 1px solid var(--border);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 16px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }}
        h1 {{
            font-size: 32px;
            font-weight: 700;
            color: var(--accent);
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: var(--text-secondary);
            font-size: 16px;
        }}
        .section {{
            margin-bottom: 48px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: var(--accent-green);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border);
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }}
        .news-grid {{
            display: grid;
            gap: 16px;
        }}
        .news-card {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            transition: border-color 0.2s, transform 0.2s;
        }}
        .news-card:hover {{
            border-color: var(--accent);
            transform: translateY(-2px);
        }}
        .news-title {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 10px;
            line-height: 1.5;
        }}
        .news-summary {{
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 12px;
            line-height: 1.7;
        }}
        .news-meta {{
            font-size: 13px;
        }}
        .news-meta a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .news-meta a:hover {{
            text-decoration: underline;
        }}
        .sources-section {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-top: 40px;
        }}
        .sources-title {{
            font-size: 18px;
            font-weight: 600;
            color: var(--accent-yellow);
            margin-bottom: 16px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
        }}
        .sources-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 8px;
        }}
        .sources-list li {{
            font-size: 13px;
        }}
        .sources-list a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .sources-list a:hover {{
            text-decoration: underline;
        }}
        footer {{
            text-align: center;
            padding: 40px 0;
            color: var(--text-secondary);
            font-size: 13px;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}
        @media (max-width: 600px) {{
            .container {{ padding: 20px 12px; }}
            h1 {{ font-size: 24px; }}
            .sources-list {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="date-badge">{date_str}</div>
            <h1>开发者实践日报</h1>
            <p class="subtitle">面向一线开发者的技术动态、工具更新与最佳实践</p>
        </header>

        {render_section("今日技术热榜", hot_news, "🔥")}
        {render_section("深度技术解读", deep_dive, "🔍")}
        {render_section("工具推荐", tools, "🛠️")}
        {render_section("实践指南", guides, "📋")}

        <section class="sources-section">
            <h2 class="sources-title">参考链接汇总</h2>
            <ul class="sources-list">
                {''.join(source_links)}
            </ul>
        </section>

        <footer>
            <p>数据来源于 FreshRSS 24小时聚合 · 生成时间: {export_time}</p>
            <p>开发者实践版 · 关注技术实现细节与最佳实践</p>
        </footer>
    </div>
</body>
</html>
'''
    return html


def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    export_time = data.get('export_time', '')

    print(f"总文章数: {len(articles)}")

    html = generate_html(articles, export_time)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"已生成: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
