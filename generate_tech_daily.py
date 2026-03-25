#!/usr/bin/env python3
"""
开发者实践版科技日报生成器
根据人设 prompt 生成面向程序员的科技日报
"""

import json
import re
from datetime import datetime
from pathlib import Path

# 配置
NEWS_FILE = "/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260325_080554.json"
OUTPUT_FILE = "/home/zhangzhan/rss_source/tech-daily-output/tech-daily/developer_practice.html"
DATE_STR = "2026 年 3 月 25 日"

# 技术关键词分类
TECH_CATEGORIES = {
    'dev_tools': {
        'keywords': ['vscode', 'ide', 'cli', 'devtools', 'cursor', 'copilot', 'replit', 'jetbrains', 'terminal'],
        'name': '开发工具'
    },
    'framework': {
        'keywords': ['react', 'vue', 'angular', 'next.js', 'nextjs', 'fastapi', 'django', 'flask', 'spring',
                    'dotnet', '.net', 'express', 'svelte', 'solid', 'astro'],
        'name': '框架库'
    },
    'language': {
        'keywords': ['python', 'javascript', 'typescript', 'rust', 'golang', 'go ', 'java', 'kotlin', 'swift',
                    'ruby', 'php', 'c++', 'c#', 'zig', 'scala'],
        'name': '编程语言'
    },
    'ai_ml': {
        'keywords': ['ai', 'llm', 'model', 'transformer', 'diffusion', 'claude', 'gpt', 'openai', 'machine learning',
                    'deep learning', 'neural', 'inference', 'rag', 'agent', 'sora', 'image generation'],
        'name': 'AI/ML'
    },
    'devops': {
        'keywords': ['ci/cd', 'deploy', 'pipeline', 'container', 'kubernetes', 'k8s', 'docker', 'devops',
                    'terraform', 'ansible', 'helm', 'github actions', 'gitlab', 'vercel', 'netlify'],
        'name': 'DevOps'
    },
    'security': {
        'keywords': ['security', 'vulnerability', 'cve', 'patch', 'exploit', 'zero-day', 'penetration', 'audit'],
        'name': '安全'
    },
    'database': {
        'keywords': ['sql', 'nosql', 'postgres', 'postgresql', 'mongodb', 'redis', 'mysql', 'sqlite',
                    'firebase', 'supabase', 'prisma', 'orm'],
        'name': '数据库'
    },
    'web': {
        'keywords': ['html', 'css', 'web', 'frontend', 'backend', 'api', 'rest', 'graphql', 'websocket',
                    'http', 'cdn', 'wasm'],
        'name': 'Web 开发'
    },
    'mobile': {
        'keywords': ['ios', 'android', 'react native', 'flutter', 'mobile', 'app', 'xcode', 'swiftui'],
        'name': '移动开发'
    },
}

# 排除关键词（商业新闻、融资等）
EXCLUDE_KEYWORDS = [
    'series a', 'series b', 'series c', 'funding', 'ipo', 'acquisition', 'acquired',
    'ceo', 'cfo', 'executive', 'layoff', 'layoffs', 'fired', 'hiring',
    'stock', 'share', 'earnings', 'revenue', 'profit', 'loss',
    'partner', 'partnership', 'sponsor', 'sponsorship',
    'event', 'conference', 'summit', 'webinar', 'meetup',
    '报名', '活动', '大会', '沙龙', '赞助',
    'tedx', 'ted talk', 'idea', 'city', 'speaker',
    'job', 'opening', 'apply', 'hiring', 'career',
    'bridgit', 'spade', 'data', 'report', 'survey',
    'America', 'energy', 'climate', 'government', 'policy',
]

def load_news():
    """加载新闻数据"""
    with open(NEWS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def categorize_article(article):
    """对文章进行分类"""
    text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
    categories = []

    for cat_id, cat_info in TECH_CATEGORIES.items():
        for kw in cat_info['keywords']:
            if kw in text:
                categories.append(cat_id)
                break

    return categories

def should_exclude(article):
    """判断是否应该排除"""
    text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()

    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in text:
            # 但有技术关键词的保留
            categories = categorize_article(article)
            if len(categories) >= 2:  # 至少两个技术分类
                continue
            return True

    return False

def is_developer_relevant(article):
    """判断是否对开发者有价值"""
    text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
    categories = categorize_article(article)

    # 至少有一个技术分类
    if not categories:
        return False

    # AI/ML、开发工具、框架、DevOps 优先
    priority_cats = ['ai_ml', 'dev_tools', 'framework', 'devops', 'language']
    for cat in categories:
        if cat in priority_cats:
            return True

    # 两个以上技术分类也保留
    if len(categories) >= 2:
        return True

    return True

def generate_summary(article):
    """为文章生成详细总结"""
    title = article.get('title', '')
    summary = article.get('summary', '')
    feed = article.get('feed_title', '')

    # 清理 summary
    summary = re.sub(r'https?://\S+', '', summary)  # 移除链接
    summary = re.sub(r'@\w+', '', summary)  # 移除@提及
    summary = re.sub(r'🔗|💬|🔄|❤️|⚡', '', summary)  # 移除 emoji
    summary = ' '.join(summary.split())  # 清理空白

    # 如果是中文标题，尝试生成更好的总结
    if any('\u4e00' <= c <= '\u9fff' for c in title):
        if len(summary) > 50:
            return summary[:300]
        return f"{title} - {summary}" if summary else title

    # 英文内容处理
    if len(summary) > 100:
        return summary[:400]

    return f"{title}. {summary}" if summary else title

def select_articles(articles, limit=25):
    """筛选对开发者最有价值的文章"""
    scored = []

    for article in articles:
        if should_exclude(article):
            continue

        if not is_developer_relevant(article):
            continue

        # 打分
        score = 0
        categories = categorize_article(article)

        # 分类分
        for cat in categories:
            if cat in ['ai_ml', 'dev_tools', 'framework']:
                score += 3
            elif cat in ['devops', 'language', 'security']:
                score += 2
            else:
                score += 1

        # 来源分（官方博客优先）
        feed = article.get('feed_title', '').lower()
        if any(x in feed for x in ['microsoft', 'google', 'github', 'vercel', 'netlify', 'docker']):
            score += 2

        # 标题长度（太短可能是链接）
        if len(article.get('title', '')) < 10:
            score -= 2

        scored.append((score, article))

    # 按分数排序
    scored.sort(key=lambda x: -x[0])

    return [art for score, art in scored[:limit]]

def generate_hotlist(articles):
    """生成今日热榜 HTML"""
    html = []
    html.append('<div class="section hotlist">')
    html.append('<h2>今日技术热榜</h2>')
    html.append('<ul class="news-list">')

    for i, art in enumerate(articles[:15], 1):
        title = art.get('title', '无标题')
        link = art.get('link', '#')
        feed = art.get('feed_title', '未知来源')
        summary = generate_summary(art)
        categories = categorize_article(art)
        cat_names = [TECH_CATEGORIES[c]['name'] for c in categories[:2]]
        cat_badge = ', '.join(cat_names) if cat_names else '综合'

        html.append(f'''
        <li class="news-item">
            <div class="news-header">
                <span class="rank">#{i}</span>
                <span class="tags">{cat_badge}</span>
            </div>
            <h3><a href="{link}" target="_blank" rel="noopener">{title}</a></h3>
            <p class="summary">{summary[:200]}...</p>
            <div class="meta">
                <span class="source">{feed}</span>
                <a class="link-btn" href="{link}" target="_blank" rel="noopener">阅读原文</a>
            </div>
        </li>
        ''')

    html.append('</ul></div>')
    return '\n'.join(html)

def generate_deep_dive(articles):
    """生成深度技术解读"""
    # 选择有详细总结的文章
    deep_articles = []
    for art in articles:
        summary = art.get('summary', '')
        if len(summary) > 150:  # 有足够内容
            deep_articles.append(art)

    if not deep_articles:
        deep_articles = articles[:6]

    html = []
    html.append('<div class="section deep-dive">')
    html.append('<h2>深度技术解读</h2>')

    for art in deep_articles[:6]:
        title = art.get('title', '')
        link = art.get('link', '#')
        feed = art.get('feed_title', '')
        summary = generate_summary(art)
        categories = categorize_article(art)

        # 技术背景
        tech_bg = "本文涉及的技术在开发者社区引起广泛关注"
        if 'ai_ml' in categories:
            tech_bg = "AI 技术正在快速改变开发者的工作方式"
        elif 'dev_tools' in categories:
            tech_bg = "开发工具的演进直接影响开发效率"
        elif 'devops' in categories:
            tech_bg = "DevOps 实践是现代软件工程的核心"

        html.append(f'''
        <article class="deep-article">
            <h3><a href="{link}" target="_blank" rel="noopener">{title}</a></h3>
            <div class="article-meta">
                <span class="category">{' / '.join([TECH_CATEGORIES[c]['name'] for c in categories[:2]])}</span>
                <span class="source">{feed}</span>
            </div>
            <div class="article-content">
                <h4>技术背景</h4>
                <p>{tech_bg}</p>

                <h4>核心内容</h4>
                <p>{summary}</p>

                <h4>实践意义</h4>
                <p>建议开发者关注该技术的发展和落地情况，评估是否适合引入自己的工作流。</p>
            </div>
            <div class="article-footer">
                <a href="{link}" target="_blank" rel="noopener" class="read-more">阅读原文</a>
            </div>
        </article>
        ''')

    html.append('</div>')
    return '\n'.join(html)

def generate_tools_section(articles):
    """生成工具推荐"""
    # 选择工具相关文章
    tool_articles = []
    for art in articles:
        cats = categorize_article(art)
        if 'dev_tools' in cats or 'framework' in cats:
            tool_articles.append(art)

    if not tool_articles:
        tool_articles = articles[:5]

    html = []
    html.append('<div class="section tools">')
    html.append('<h2>工具推荐</h2>')
    html.append('<div class="tools-grid">')

    for art in tool_articles[:5]:
        title = art.get('title', '')
        link = art.get('link', '#')
        feed = art.get('feed_title', '')
        summary = generate_summary(art)[:150]

        html.append(f'''
        <div class="tool-card">
            <h3><a href="{link}" target="_blank" rel="noopener">{title}</a></h3>
            <p>{summary}...</p>
            <div class="tool-meta">
                <span class="source">{feed}</span>
            </div>
        </div>
        ''')

    html.append('</div></div>')
    return '\n'.join(html)

def generate_references(articles):
    """生成参考链接汇总"""
    html = []
    html.append('<div class="section references">')
    html.append('<h2>参考链接汇总</h2>')
    html.append('<table class="ref-table">')
    html.append('<thead><tr><th>序号</th><th>标题</th><th>来源</th><th>链接</th></tr></thead>')
    html.append('<tbody>')

    for i, art in enumerate(articles, 1):
        title = art.get('title', '无标题')
        link = art.get('link', '#')
        feed = art.get('feed_title', '未知')

        html.append(f'''
        <tr>
            <td>{i}</td>
            <td class="title-cell">{title}</td>
            <td>{feed}</td>
            <td><a href="{link}" target="_blank" rel="noopener">链接</a></td>
        </tr>
        ''')

    html.append('</tbody></table></div>')
    return '\n'.join(html)

def generate_html():
    """生成完整 HTML 文档"""
    # 加载数据
    data = load_news()
    articles = data['articles']

    # 筛选文章
    selected = select_articles(articles, limit=25)

    # 生成各部分
    hotlist = generate_hotlist(selected)
    deep_dive = generate_deep_dive(selected)
    tools = generate_tools_section(selected)
    references = generate_references(selected)

    # 完整 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>开发者实践版科技日报 - {DATE_STR}</title>
    <style>
        :root {{
            --primary: #2563eb;
            --secondary: #1e40af;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #e2e8f0;
            --text-muted: #94a3b8;
            --border: #334155;
            --accent: #06b6d4;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid var(--border);
        }}

        header h1 {{
            font-size: 2.5rem;
            color: var(--accent);
            margin-bottom: 0.5rem;
        }}

        header .date {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        .section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}

        .section h2 {{
            color: var(--accent);
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }}

        .news-list {{
            list-style: none;
        }}

        .news-item {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            transition: transform 0.2s, border-color 0.2s;
        }}

        .news-item:hover {{
            transform: translateX(4px);
            border-color: var(--primary);
        }}

        .news-header {{
            display: flex;
            gap: 0.75rem;
            align-items: center;
            margin-bottom: 0.5rem;
        }}

        .rank {{
            background: var(--primary);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.9rem;
        }}

        .tags {{
            background: rgba(6,182,212,0.15);
            color: var(--accent);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }}

        .news-item h3 {{
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }}

        .news-item h3 a {{
            color: var(--text);
            text-decoration: none;
            transition: color 0.2s;
        }}

        .news-item h3 a:hover {{
            color: var(--accent);
        }}

        .summary {{
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
        }}

        .meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .link-btn {{
            background: var(--primary);
            color: white;
            padding: 0.3rem 0.75rem;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.85rem;
            transition: background 0.2s;
        }}

        .link-btn:hover {{
            background: var(--secondary);
        }}

        .deep-article {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .deep-article h3 {{
            color: var(--accent);
            margin-bottom: 0.5rem;
        }}

        .deep-article h3 a {{
            color: inherit;
            text-decoration: none;
        }}

        .article-meta {{
            display: flex;
            gap: 1rem;
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 1rem;
        }}

        .article-content h4 {{
            color: var(--primary);
            font-size: 1rem;
            margin: 1rem 0 0.5rem;
        }}

        .article-content p {{
            color: var(--text-muted);
            line-height: 1.8;
        }}

        .article-footer {{
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
        }}

        .read-more {{
            color: var(--primary);
            text-decoration: none;
            font-weight: 500;
        }}

        .tools-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}

        .tool-card {{
            background: rgba(255,255,255,0.02);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.25rem;
            transition: transform 0.2s, border-color 0.2s;
        }}

        .tool-card:hover {{
            transform: translateY(-4px);
            border-color: var(--accent);
        }}

        .tool-card h3 {{
            font-size: 1rem;
            margin-bottom: 0.75rem;
        }}

        .tool-card h3 a {{
            color: var(--text);
            text-decoration: none;
        }}

        .tool-card h3 a:hover {{
            color: var(--accent);
        }}

        .tool-card p {{
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 0.75rem;
        }}

        .tool-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .ref-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }}

        .ref-table th, .ref-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        .ref-table th {{
            color: var(--accent);
            font-weight: 600;
        }}

        .ref-table td a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .ref-table tr:hover {{
            background: rgba(255,255,255,0.02);
        }}

        .title-cell {{
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        footer {{
            text-align: center;
            color: var(--text-muted);
            padding: 2rem;
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            header h1 {{
                font-size: 1.8rem;
            }}

            .tools-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h2>开发者实践版科技日报</h2>
            <p class="date">{DATE_STR}</p>
        </header>

        {hotlist}
        {deep_dive}
        {tools}
        {references}

        <footer>
            <p>Generated by Developer Practice Tech Daily Generator</p>
            <p>数据来源：RSS 聚合 | 筛选原则：技术价值优先，排除纯商业新闻</p>
        </footer>
    </div>
</body>
</html>
'''

    # 写入文件
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding='utf-8')

    print(f"日报已生成：{OUTPUT_FILE}")
    print(f"筛选文章数：{len(selected)}")
    print(f"总文章数：{len(articles)}")

if __name__ == '__main__':
    generate_html()
