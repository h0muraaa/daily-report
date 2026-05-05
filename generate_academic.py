#!/usr/bin/env python3
import json
import re
from datetime import datetime

# Read JSON file
with open('/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260505_190140.json') as f:
    data = json.load(f)

articles = data.get('articles', [])
print(f"Total articles: {len(articles)}")

# Academic research filtering keywords and patterns
academic_keywords = [
    'paper', 'arxiv', 'neurips', 'icml', 'cvpr', 'acl', 'iclr', 'emnlp',
    'research', 'study', 'dataset', 'benchmark', 'model', 'llm', 'transformer',
    'training', 'fine-tuning', 'rlhf', 'alignment', 'hallucination',
    'reasoning', 'agent', 'multimodal', 'vision', 'embedding', 'inference',
    '开源', '论文', '模型', '研究', '学术', 'preprint', 'publication',
    'huggingface', 'github', 'weights', 'checkpoint', 'release',
    'microsoft research', 'google research', 'deepmind', 'anthropic',
    'mit', 'stanford', 'berkeley', 'cmu', 'openai', 'nvidia research',
    'speculative decoding', 'token prediction', 'memory', 'attention',
    'safety', 'security', 'vulnerability', 'attack', 'evaluation',
    'fine-tuned', 'distilled', 'quantized', 'moE', 'mixture of experts',
    'rag', 'retrieval', 'generation', 'synthesis'
]

# Scoring function for academic relevance
def score_academic(article):
    score = 0
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    feed = article.get('feed_title', '').lower()
    text = title + ' ' + summary + ' ' + feed

    # High-value academic sources
    high_value_sources = [
        'microsoft research', 'google research', 'deepmind', 'anthropic',
        'openai', 'nvidia', 'mit', 'stanford', 'berkeley', 'cmu',
        'huggingface', 'arXiv', 'papers', 'martin fowler'
    ]
    for source in high_value_sources:
        if source in feed:
            score += 3

    # Academic keywords
    for kw in academic_keywords:
        if kw in text:
            score += 1

    # Specific patterns that indicate academic value
    if 'paper:' in text or 'arxiv' in text or 'huggingface.co/papers' in text:
        score += 5
    if 'researchers' in text and ('study' in text or 'found' in text or 'showed' in text):
        score += 3
    if 'dataset' in text or 'benchmark' in text:
        score += 3
    if 'open-source' in text or 'open source' in text or 'apache 2.0' in text:
        score += 2
    if 'vulnerability' in text and ('%' in text or 'percent' in text):
        score += 3

    # Penalize non-academic content
    non_academic = ['apple id', 'turkey', 'app store', 'nft', 'crypto', 'blockchain',
                    'invest', 'stock price', 'earnings', 'ipo', 'funding round']
    for na in non_academic:
        if na in text:
            score -= 5

    # Penalize pure product announcements without technical depth
    product_only = ['now available', 'now live', 'rolling out', 'launching today',
                    'partnership', 'strategic partnership']
    for po in product_only:
        if po in text and 'paper' not in text and 'research' not in text:
            score -= 2

    return score

# Score and sort articles
scored = [(a, score_academic(a)) for a in articles]
scored.sort(key=lambda x: x[1], reverse=True)

# Print top scored articles for debugging
print("\n--- Top 30 scored articles ---")
for i, (a, s) in enumerate(scored[:30]):
    print(f"{s:3d} | {a['title'][:80]} | {a['feed_title']}")

# Select top articles for the report (minimum score threshold)
min_score = 4
top_articles = [(a, s) for a, s in scored if s >= min_score]
print(f"\nSelected {len(top_articles)} articles with score >= {min_score}")

# Categorize articles
categories = {
    'research_papers': [],      # Papers, studies, academic research
    'open_source': [],          # Open source models, datasets, tools
    'model_releases': [],       # Model releases with technical details
    'security_safety': [],      # AI safety, security, alignment
    'systems_infra': [],        # Systems, infrastructure, inference optimization
    'trends_observations': [],  # Research trends, methodological insights
}

for article, score in top_articles:
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    text = title + ' ' + summary
    feed = article.get('feed_title', '').lower()

    if 'paper:' in text or 'arxiv' in text or 'huggingface.co/papers' in text or 'paper' in title.lower():
        categories['research_papers'].append((article, score))
    elif 'open-source' in text or 'open source' in text or 'github' in text or 'huggingface' in text or 'weights' in text or 'dataset' in text:
        if 'model' in text or 'llm' in text or 'gemma' in text or 'weights' in text:
            categories['open_source'].append((article, score))
        else:
            categories['open_source'].append((article, score))
    elif 'security' in text or 'vulnerability' in text or 'safety' in text or 'attack' in text or 'alignment' in text:
        categories['security_safety'].append((article, score))
    elif 'inference' in text or 'speed' in text or 'latency' in text or 'token' in text or 'gpu' in text or 'decoding' in text:
        categories['systems_infra'].append((article, score))
    elif 'model' in text and ('release' in text or 'launch' in text or 'new' in text):
        categories['model_releases'].append((article, score))
    else:
        categories['trends_observations'].append((article, score))

# Print categorization
for cat, items in categories.items():
    print(f"\n{cat}: {len(items)} articles")
    for a, s in items[:5]:
        print(f"  {s} | {a['title'][:70]}")

# Now generate HTML
html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>学术研究员科技日报 - {datetime.now().strftime("%Y年%m月%d日")}</title>
    <style>
        :root {{
            --primary: #1a365d;
            --secondary: #2c5282;
            --accent: #3182ce;
            --bg: #f7fafc;
            --card-bg: #ffffff;
            --text: #1a202c;
            --text-light: #4a5568;
            --border: #e2e8f0;
            --link: #2b6cb0;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            background: var(--bg);
            color: var(--text);
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
            border-bottom: 2px solid var(--primary);
            margin-bottom: 40px;
        }}
        header h1 {{
            font-size: 2.2em;
            color: var(--primary);
            font-weight: 700;
            letter-spacing: -0.02em;
        }}
        header .subtitle {{
            font-size: 1.1em;
            color: var(--text-light);
            margin-top: 8px;
        }}
        header .date {{
            font-size: 0.95em;
            color: var(--text-light);
            margin-top: 12px;
            font-style: italic;
        }}
        .section {{
            margin-bottom: 48px;
        }}
        .section-title {{
            font-size: 1.5em;
            color: var(--primary);
            border-left: 4px solid var(--accent);
            padding-left: 16px;
            margin-bottom: 24px;
            font-weight: 600;
        }}
        .article {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 20px;
        }}
        .article h3 {{
            font-size: 1.15em;
            color: var(--primary);
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .article p {{
            color: var(--text-light);
            font-size: 0.95em;
            margin-bottom: 12px;
        }}
        .article .source {{
            font-size: 0.85em;
            color: var(--text-light);
        }}
        .article .source a {{
            color: var(--link);
            text-decoration: none;
        }}
        .article .source a:hover {{
            text-decoration: underline;
        }}
        .score {{
            display: inline-block;
            background: var(--accent);
            color: white;
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 12px;
            margin-left: 8px;
            vertical-align: middle;
        }}
        .references {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 24px;
        }}
        .references h2 {{
            font-size: 1.3em;
            color: var(--primary);
            margin-bottom: 16px;
        }}
        .references ul {{
            list-style: none;
        }}
        .references li {{
            margin-bottom: 8px;
            font-size: 0.9em;
        }}
        .references a {{
            color: var(--link);
            text-decoration: none;
        }}
        .references a:hover {{
            text-decoration: underline;
        }}
        footer {{
            text-align: center;
            padding: 40px 0;
            color: var(--text-light);
            font-size: 0.85em;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }}
        .highlight {{
            background: #ebf8ff;
            padding: 16px;
            border-radius: 6px;
            border-left: 3px solid var(--accent);
            margin-bottom: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>学术研究员科技日报</h1>
            <div class="subtitle">聚焦人工智能与计算机科学前沿研究</div>
            <div class="date">{datetime.now().strftime("%Y年%m月%d日")} | 数据来源：过去24小时</div>
        </header>
'''

# Research Papers section
if categories['research_papers']:
    html += '''
        <div class="section">
            <h2 class="section-title">研究动态</h2>
'''
    for article, score in categories['research_papers'][:10]:
        title = article.get('title', '')
        summary = article.get('summary', '')
        link = article.get('link', '')
        feed = article.get('feed_title', '')
        # Clean up summary
        summary = re.sub(r'💬\d+\s*🔄\d+\s*❤️\d+\s*👀\d+\s*📊?\d*\s*⚡ Powered by xgo\.ing', '', summary)
        summary = re.sub(r'🔗 View on Twitter|🔗 View Quoted Tweet', '', summary)
        summary = summary.strip()
        if len(summary) > 400:
            summary = summary[:400] + '...'
        html += f'''
            <div class="article">
                <h3>{title}</h3>
                <p>{summary}</p>
                <div class="source">
                    <a href="{link}" target="_blank" rel="noopener">[来源: {feed}]</a>
                </div>
            </div>
'''
    html += '        </div>\n'

# Security & Safety section
if categories['security_safety']:
    html += '''
        <div class="section">
            <h2 class="section-title">安全与对齐研究</h2>
'''
    for article, score in categories['security_safety'][:6]:
        title = article.get('title', '')
        summary = article.get('summary', '')
        link = article.get('link', '')
        feed = article.get('feed_title', '')
        summary = re.sub(r'💬\d+\s*🔄\d+\s*❤️\d+\s*👀\d+\s*📊?\d*\s*⚡ Powered by xgo\.ing', '', summary)
        summary = re.sub(r'🔗 View on Twitter|🔗 View Quoted Tweet', '', summary)
        summary = summary.strip()
        if len(summary) > 400:
            summary = summary[:400] + '...'
        html += f'''
            <div class="article">
                <h3>{title}</h3>
                <p>{summary}</p>
                <div class="source">
                    <a href="{link}" target="_blank" rel="noopener">[来源: {feed}]</a>
                </div>
            </div>
'''
    html += '        </div>\n'

# Open Source section
if categories['open_source']:
    html += '''
        <div class="section">
            <h2 class="section-title">开源资源</h2>
'''
    for article, score in categories['open_source'][:6]:
        title = article.get('title', '')
        summary = article.get('summary', '')
        link = article.get('link', '')
        feed = article.get('feed_title', '')
        summary = re.sub(r'💬\d+\s*🔄\d+\s*❤️\d+\s*👀\d+\s*📊?\d*\s*⚡ Powered by xgo\.ing', '', summary)
        summary = re.sub(r'🔗 View on Twitter|🔗 View Quoted Tweet', '', summary)
        summary = summary.strip()
        if len(summary) > 400:
            summary = summary[:400] + '...'
        html += f'''
            <div class="article">
                <h3>{title}</h3>
                <p>{summary}</p>
                <div class="source">
                    <a href="{link}" target="_blank" rel="noopener">[来源: {feed}]</a>
                </div>
            </div>
'''
    html += '        </div>\n'

# Systems & Infrastructure section
if categories['systems_infra']:
    html += '''
        <div class="section">
            <h2 class="section-title">系统与基础设施</h2>
'''
    for article, score in categories['systems_infra'][:6]:
        title = article.get('title', '')
        summary = article.get('summary', '')
        link = article.get('link', '')
        feed = article.get('feed_title', '')
        summary = re.sub(r'💬\d+\s*🔄\d+\s*❤️\d+\s*👀\d+\s*📊?\d*\s*⚡ Powered by xgo\.ing', '', summary)
        summary = re.sub(r'🔗 View on Twitter|🔗 View Quoted Tweet', '', summary)
        summary = summary.strip()
        if len(summary) > 400:
            summary = summary[:400] + '...'
        html += f'''
            <div class="article">
                <h3>{title}</h3>
                <p>{summary}</p>
                <div class="source">
                    <a href="{link}" target="_blank" rel="noopener">[来源: {feed}]</a>
                </div>
            </div>
'''
    html += '        </div>\n'

# Trends section
if categories['trends_observations'] or categories['model_releases']:
    html += '''
        <div class="section">
            <h2 class="section-title">趋势观察</h2>
'''
    combined = categories['trends_observations'] + categories['model_releases']
    for article, score in combined[:6]:
        title = article.get('title', '')
        summary = article.get('summary', '')
        link = article.get('link', '')
        feed = article.get('feed_title', '')
        summary = re.sub(r'💬\d+\s*🔄\d+\s*❤️\d+\s*👀\d+\s*📊?\d*\s*⚡ Powered by xgo\.ing', '', summary)
        summary = re.sub(r'🔗 View on Twitter|🔗 View Quoted Tweet', '', summary)
        summary = summary.strip()
        if len(summary) > 400:
            summary = summary[:400] + '...'
        html += f'''
            <div class="article">
                <h3>{title}</h3>
                <p>{summary}</p>
                <div class="source">
                    <a href="{link}" target="_blank" rel="noopener">[来源: {feed}]</a>
                </div>
            </div>
'''
    html += '        </div>\n'

# References section
html += '''
        <div class="section">
            <div class="references">
                <h2>参考文献</h2>
                <ul>
'''

# Collect all unique sources
all_sources = set()
for cat_items in categories.values():
    for article, score in cat_items:
        link = article.get('link', '')
        feed = article.get('feed_title', '')
        title = article.get('title', '')
        if link and feed:
            all_sources.add((feed, link, title))

for feed, link, title in sorted(all_sources)[:50]:
    html += f'                    <li><a href="{link}" target="_blank" rel="noopener">{feed}</a> — {title[:60]}</li>\n'

html += '''
                </ul>
            </div>
        </div>

        <footer>
            <p>学术研究员科技日报 | 由 tech-daily-generator 自动生成</p>
            <p>数据周期：过去24小时</p>
        </footer>
    </div>
</body>
</html>
'''

# Write output
output_path = '/home/runner/work/daily-report/daily-report/tech-daily/academic_research.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nGenerated: {output_path}")
print(f"File size: {len(html)} bytes")
