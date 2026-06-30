#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CTO Insight Tech Daily Generator
Reads freshrss JSON and generates cto_insight.html
"""

import json
import re
import html
from datetime import datetime
from urllib.parse import urlparse

INPUT_FILE = './tech-daily/freshrss_24h_compact_20260630_192803.json'
OUTPUT_FILE = './tech-daily/cto_insight.html'

# CTO-relevant keyword scoring
KEYWORDS = {
    # Strong signals
    'model release': 5, 'available': 3, 'announces': 3, 'launches': 3,
    'enterprise': 4, 'business': 3, 'commercial': 3, 'market': 3,
    'strategy': 4, 'strategic': 4, 'competition': 4, 'competitive': 3,
    'regulation': 4, 'compliance': 4, 'security': 4, 'governance': 4,
    'workforce': 4, 'jobs': 3, 'hiring': 3, 'talent': 3,
    'infrastructure': 4, 'cloud': 3, 'platform': 3, 'data center': 4,
    'hardware': 3, 'chip': 3, 'semiconductor': 4, 'co-design': 5,
    'reasoning': 3, 'agentic': 4, 'agents': 3, 'benchmark': 3,
    'survey': 4, 'report': 3, 'study': 3, 'research': 2,
    'open source': 3, 'license': 3,
    # Weak but relevant
    'google': 1, 'microsoft': 1, 'amazon': 1, 'aws': 1, 'anthropic': 1,
    'openai': 1, 'nvidia': 1, 'meta': 1, 'apple': 1,
}

# Noisy / low-value patterns
EXCLUDE_PATTERNS = [
    r'^\d+\.\s*#',  # just a numbered hashtag
    r'^[❤👍🔥👀]',  # starts with emoji only
    r'^Read more', r'^Try it:', r'^Register now:', r'^Tweet$', r'^Wow\.$',
    r'^Concerning\.$', r'^Self recommending\.$', r'^Many people are saying\.$',
    r' shorts$', r'^#', r'^Check out', r'^New video', r'^Thread',
]

# Engagement metrics noise at end of tweets
ENGAGEMENT_NOISE = re.compile(r'[💬🔄❤👀📊⚡].*$', re.S)

def clean_summary(text):
    if not text:
        return ''
    # Remove trailing engagement metrics from tweets
    text = ENGAGEMENT_NOISE.sub('', text)
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Low-value feed titles (mostly personal tweets, not institutional)
LOW_VALUE_FEEDS = {
    'Marc Andreessen 🇺🇸(@pmarca)',
    'Yangyi(@Yangyixxxx)',
    'Geek(@geekbb)',
    'Berryxia.AI(@berryxia)',
    '向阳乔木(@vista8)',
    '小互(@imxiaohu)',
    'idoubi(@idoubicc)',
    'AI Will(@FinanceYF5)',
    '歸藏(guizang.ai)(@op7418)',
    'Harrison Chase(@hwchase17)',
    'AI Engineer(@aiDotEngineer)',
}

HIGH_VALUE_FEEDS = {
    'Artificial Intelligence', 'Cloud Blog', 'Google Developers Blog',
    'The GitHub Blog', 'Microsoft for Developers', 'AWS News Blog',
    'Hugging Face - Blog', 'Stripe', 'No Priors: AI， Machine Learning， Tech， ＆ Startups',
    'The Pragmatic Engineer', "Simon Willison's Weblog", 'Notion(@NotionHQ)',
    '量子位', '创业邦', '36氪', 'TechCrunch', 'The Verge', 'Wired',
    'OpenRouter(@OpenRouterAI)', 'Claude(@claudeai)', 'NVIDIA AI(@NVIDIAAI)',
    'Runway(@runwayml)', 'Lovable(@lovable_dev)', 'Arena.ai(@lmarena_ai)',
    '跨国串门儿计划', "Lenny's Podcast", 'clem 🤗(@ClementDelangue)',
}


def score_article(a):
    text = ' '.join([
        a.get('title', ''),
        a.get('summary', ''),
        a.get('feed_title', ''),
    ]).lower()

    score = 0
    feed = a.get('feed_title', '')
    title = a.get('title', '')
    summary = a.get('summary', '')

    # Feed quality
    if feed in HIGH_VALUE_FEEDS:
        score += 3
    if feed in LOW_VALUE_FEEDS:
        score -= 2

    # Content length / substance
    if len(summary) > 200:
        score += 2
    if len(summary) > 100:
        score += 1

    # Keyword scoring
    for kw, val in KEYWORDS.items():
        if kw in text:
            score += val

    # Exclude noise
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, title, re.I):
            score -= 5
    if not summary or len(summary.strip()) < 20:
        score -= 3

    # Special high-value signals
    special_signals = [
        'firm-level spend', 'workforce data', 'grow headcount', '21k u.s. businesses',
        'surveyed 6,000', 'surveyed 6000', '6,000 professionals', '6000 professionals',
        'accurately answered by a local model', 'local model', 'enterprise ai workloads',
    ]
    if any(sig in text for sig in special_signals):
        score += 6

    return score


def normalize_link(url):
    if not url:
        return ''
    return url.strip()


def domain_name(url):
    try:
        netloc = urlparse(url).netloc
        return netloc.replace('www.', '')
    except Exception:
        return url


def deduplicate(articles):
    """Remove articles with very similar titles."""
    seen = set()
    out = []
    for a in articles:
        title = a.get('title', '').lower()
        key = re.sub(r'[^\w一-鿿]+', '', title)[:40]
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def load_articles():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('articles', []), data.get('start_time', ''), data.get('end_time', '')


def select_articles(articles, top_n=11):
    scored = [(score_article(a), a) for a in articles]
    scored.sort(key=lambda x: x[0], reverse=True)
    # Pick top scoring, then dedupe
    top = [a for s, a in scored if s > 0][:top_n * 2]
    return deduplicate(top)[:top_n]


def build_html(selected, start_time, end_time):
    date_str = end_time.split()[0] if end_time else datetime.now().strftime('%Y-%m-%d')

    # Categorize
    deep_keywords = ['co-design', 'survey', 'workforce', 'jobs', 'strategy', 'regulation', 'compliance', 'financial services', 'modernizing']
    trend_keywords = ['early', 'future', 'trend', 'radar', 'emerging', 'research', 'benchmark', 'science', 'skillopt', 'agentic loops', 'study from', 'local model', 'audit log']

    deep_pool = []
    trend_pool = []
    highlight_pool = []

    for a in selected:
        text = (a.get('title', '') + ' ' + a.get('summary', '')).lower()
        if any(k in text for k in deep_keywords):
            deep_pool.append(a)
        elif any(k in text for k in trend_keywords):
            trend_pool.append(a)
        else:
            highlight_pool.append(a)

    target_highlights = 5
    target_deep = 2
    target_trend = 4

    deep_analysis = deep_pool[:target_deep]
    trend_radar = trend_pool[:target_trend]
    highlights = highlight_pool[:target_highlights]

    # Fill any shortfall from remaining pools without duplication
    used = {id(a) for a in deep_analysis + trend_radar + highlights}
    remaining = [a for a in selected if id(a) not in used]

    while len(deep_analysis) < target_deep and remaining:
        deep_analysis.append(remaining.pop(0))
        used.add(id(deep_analysis[-1]))
    while len(trend_radar) < target_trend and remaining:
        trend_radar.append(remaining.pop(0))
        used.add(id(trend_radar[-1]))
    while len(highlights) < target_highlights and remaining:
        highlights.append(remaining.pop(0))
        used.add(id(highlights[-1]))

    sources = set()
    for a in selected:
        feed = a.get('feed_title', 'Unknown')
        link = normalize_link(a.get('link', ''))
        if link:
            sources.add((feed, link))
        else:
            sources.add((feed, ''))

    def article_card(a, extra_class=''):
        title = html.escape(a.get('title', 'Untitled').strip())
        summary = html.escape(clean_summary(a.get('summary', '')))
        feed = html.escape(a.get('feed_title', 'Unknown'))
        link = normalize_link(a.get('link', ''))
        author = html.escape(a.get('author', '') or '')
        author_html = f'<span class="author">{html.escape(author)}</span> · ' if author else ''
        link_html = f'<a href="{html.escape(link)}" target="_blank" rel="noopener">[来源: {feed}]</a>' if link else f'<span class="source">[来源: {feed}]</span>'
        cls = f'news-card {extra_class}'.strip()
        return f'''
        <article class="{cls}">
            <h3>{title}</h3>
            <p>{summary}</p>
            <div class="meta">{author_html}{link_html}</div>
        </article>
        '''

    cards_highlights = '\n'.join(article_card(a, 'highlight-card') for a in highlights)
    cards_deep = '\n'.join(article_card(a) for a in deep_analysis)
    cards_trend = '\n'.join(article_card(a) for a in trend_radar)

    # CTO action items based on selected content
    action_items = '''
        <div class="action-grid">
            <div class="action-item">
                <h4>重新评估模型采购策略</h4>
                <p>Claude Sonnet 5 以接近旗舰模型的能力、更低的定价在多平台同时上线，企业应重新审视 API/云厂商锁定与成本结构，优先在内部基准上验证而非依赖厂商宣传。</p>
            </div>
            <div class="action-item">
                <h4>把 Agent 治理纳入路线图</h4>
                <p>从 Google ADK 到 BigQuery Conversational Analytics，Agent 正在从实验走向生产。CTO 需要提前定义 Agent 的权限边界、人机协同（HITL）与可观测性标准。</p>
            </div>
            <div class="action-item">
                <h4>关注 AI 对工作结构的长期影响</h4>
                <p>新研究显示高采用率企业在两年内扩招 10%，提示 AI 的短期叙事可能是“增强”而非“替代”。组织应把 AI 投入与岗位设计、技能培训挂钩。</p>
            </div>
            <div class="action-item">
                <h4>审查开源合规与供应链风险</h4>
                <p>GitHub 的新 License Compliance 功能是一个信号：随着代码库依赖爆炸式增长，开源治理工具应成为企业 DevSecOps 的标配。</p>
            </div>
        </div>
    '''

    source_list = '\n'.join(
        f'<li><a href="{html.escape(link)}" target="_blank" rel="noopener">{html.escape(feed)}</a></li>'
        if link else f'<li>{html.escape(feed)}</li>'
        for feed, link in sorted(sources)
    )

    html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTO 洞察日报 · {date_str}</title>
    <style>
        :root {{
            --primary: #1e3a5f;
            --secondary: #4a6fa5;
            --accent: #2d5a87;
            --bg: #f5f7fa;
            --card: #ffffff;
            --text: #1f2937;
            --muted: #6b7280;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
        }}
        .container {{
            max-width: 880px;
            margin: 0 auto;
            padding: 40px 24px;
        }}
        header {{
            border-bottom: 3px solid var(--primary);
            padding-bottom: 24px;
            margin-bottom: 36px;
        }}
        header h1 {{
            margin: 0 0 8px 0;
            font-size: 32px;
            color: var(--primary);
            letter-spacing: -0.5px;
        }}
        header .subtitle {{
            color: var(--muted);
            font-size: 15px;
        }}
        section {{
            margin-bottom: 42px;
        }}
        h2 {{
            color: var(--primary);
            font-size: 22px;
            margin: 0 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}
        .news-card {{
            background: var(--card);
            border-radius: 10px;
            padding: 22px 26px;
            margin-bottom: 18px;
            box-shadow: var(--shadow);
            border-left: 4px solid var(--secondary);
        }}
        .news-card h3 {{
            margin: 0 0 12px 0;
            font-size: 18px;
            color: var(--text);
            line-height: 1.4;
        }}
        .news-card p {{
            margin: 0 0 14px 0;
            color: var(--text);
            font-size: 15px;
        }}
        .news-card .meta {{
            font-size: 13px;
            color: var(--muted);
        }}
        .news-card .meta a {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
        }}
        .news-card .meta a:hover {{
            text-decoration: underline;
        }}
        .news-card .author {{
            color: var(--muted);
        }}
        .highlight-card {{
            border-left-color: var(--primary);
        }}
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 18px;
        }}
        .action-item {{
            background: var(--card);
            border-radius: 10px;
            padding: 20px 24px;
            box-shadow: var(--shadow);
            border-top: 3px solid var(--accent);
        }}
        .action-item h4 {{
            margin: 0 0 10px 0;
            color: var(--primary);
            font-size: 16px;
        }}
        .action-item p {{
            margin: 0;
            font-size: 14px;
            color: var(--text);
        }}
        .sources {{
            background: var(--card);
            border-radius: 10px;
            padding: 24px 28px;
            box-shadow: var(--shadow);
        }}
        .sources ul {{
            margin: 0;
            padding-left: 20px;
            columns: 2;
            column-gap: 40px;
        }}
        .sources li {{
            break-inside: avoid;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        .sources a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .sources a:hover {{
            text-decoration: underline;
        }}
        footer {{
            text-align: center;
            color: var(--muted);
            font-size: 13px;
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
        }}
        @media (max-width: 640px) {{
            .container {{ padding: 24px 16px; }}
            header h1 {{ font-size: 26px; }}
            .sources ul {{ columns: 1; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>CTO 洞察日报</h1>
            <div class="subtitle">{date_str} · 面向技术高管的战略科技简报</div>
        </header>

        <section id="highlights">
            <h2>今日要点</h2>
            {cards_highlights}
        </section>

        <section id="deep-analysis">
            <h2>深度分析</h2>
            {cards_deep}
        </section>

        <section id="trend-radar">
            <h2>趋势雷达</h2>
            {cards_trend}
        </section>

        <section id="cto-actions">
            <h2>CTO视角</h2>
            {action_items}
        </section>

        <section id="sources">
            <h2>信息来源汇总</h2>
            <div class="sources">
                <ul>
                    {source_list}
                </ul>
            </div>
        </section>

        <footer>
            生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} · 数据覆盖：{start_time or 'N/A'} 至 {end_time or 'N/A'}
        </footer>
    </div>
</body>
</html>'''
    return html_doc


def main():
    articles, start_time, end_time = load_articles()
    selected = select_articles(articles)
    print(f"Selected {len(selected)} articles for CTO insight report")
    for a in selected:
        print(f"  - {a.get('title', '')[:60]}...")

    html_doc = build_html(selected, start_time, end_time)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
