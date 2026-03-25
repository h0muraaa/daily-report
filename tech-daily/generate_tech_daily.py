#!/usr/bin/env python3
"""
开发者实践版科技日报生成器

根据人设 prompt 生成面向程序员的科技日报，包含：
- 今日技术热榜（15-25 条）
- 深度技术解读（6-10 条）
- 工具推荐（3-5 个）
- 参考链接汇总
"""

import json
import re
from datetime import datetime
import os

# 输入输出路径
INPUT_JSON = "/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260325_080554.json"
OUTPUT_HTML = "/home/zhangzhan/rss_source/tech-daily-output/tech-daily/developer_practice.html"

# 开发者关注的技术领域关键词
DEV_CATEGORIES = {
    'ai_ml': ['ai', 'ml', 'llm', 'transformer', 'diffusion', 'embedding', 'fine-tune', 'rag', 'agent', 'model', 'inference', 'training'],
    'frontend': ['react', 'vue', 'angular', 'svelte', 'nextjs', 'vite', 'webpack', 'css', 'html', 'javascript', 'typescript', 'frontend'],
    'backend': ['python', 'java', 'go', 'rust', 'nodejs', 'fastapi', 'django', 'flask', 'spring', 'api', 'graphql', 'rest'],
    'devops': ['docker', 'kubernetes', 'ci/cd', 'github actions', 'gitlab', 'terraform', 'ansible', 'devops', 'sre', 'monitoring'],
    'cloud': ['aws', 'azure', 'gcp', 'cloud', 'serverless', 'lambda', 'ecs', 's3', 'rds', 'vpc'],
    'database': ['postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'database', 'sql', 'nosql', 'orm', 'migration'],
    'tools': ['vscode', 'cursor', 'jetbrains', 'cli', 'terminal', 'ide', 'extension', 'plugin', 'sdk', 'devtool'],
    'security': ['security', 'vulnerability', 'cve', 'pentest', 'authentication', 'oauth', 'encryption', 'zero-trust'],
    'mobile': ['ios', 'android', 'react native', 'flutter', 'swift', 'kotlin', 'mobile app'],
    'data': ['data engineering', 'etl', 'spark', 'kafka', 'airflow', 'data pipeline', 'streaming', 'batch'],
}

# 高优先级技术源
PRIORITY_SOURCES = [
    'Visual Studio Code', 'Microsoft for Developers', 'Vercel', 'GitHub',
    'InfoQ', 'Stack Overflow', 'Hacker News', 'arXiv', 'cs.',
    'Simon Willison', 'Hugging Face', 'Replit', 'Cursor', 'Databricks',
    'AWS', 'Google Cloud', 'Docker', 'Kubernetes', 'Node.js', 'Python',
    'Replicate', 'LangChain', 'Firebase', 'Stripe', 'Cloudflare'
]


def load_articles(filepath):
    """加载新闻数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def categorize_article(article):
    """判断文章属于哪个技术类别"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    feed = (article.get('feed_title', '') or '').lower()
    text = f"{title} {summary} {feed}"

    categories = []
    for cat, keywords in DEV_CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                categories.append(cat)
                break
    return categories


def is_developer_focused(article):
    """判断是否是开发者关注的内容"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    feed = (article.get('feed_title', '') or '').lower()
    link = article.get('link', '')

    # 排除纯社交媒体帖子（太短的）
    if ('x.com' in link or 'twitter.com' in link) and len(summary) < 150:
        return False

    # 排除纯商业新闻
    exclude_keywords = ['融资', 'series', 'funding', 'acquisition', 'ipo', '估值', '投资', '收购']
    for kw in exclude_keywords:
        if kw in title or kw in summary:
            return False

    # 检查是否包含技术关键词
    all_dev_keywords = set()
    for kws in DEV_CATEGORIES.values():
        all_dev_keywords.update(kws)

    text = f"{title} {summary} {feed}"
    match_count = sum(1 for kw in all_dev_keywords if kw in text)

    # 高优先级源的内容
    for src in PRIORITY_SOURCES:
        if src.lower() in feed:
            return True

    return match_count >= 2


def extract_summary(article):
    """从文章提取或生成摘要"""
    summary = article.get('summary', '')
    title = article.get('title', '')

    if not summary:
        return title

    # 清理过长的摘要
    if len(summary) > 500:
        summary = summary[:500] + '...'

    return summary.strip()


def generate_source_link(article):
    """生成信息来源链接 HTML"""
    link = article.get('link', '#')
    feed_title = article.get('feed_title', '')

    # 缩短 feed title
    display_title = feed_title
    if len(display_title) > 30:
        display_title = display_title[:28] + '...'

    return f'<a href="{link}" target="_blank" class="source-tag">{display_title}</a>'


def select_hot_articles(articles, limit=20):
    """筛选热榜文章"""
    scored = []
    for art in articles:
        if not is_developer_focused(art):
            continue

        score = 0
        feed = (art.get('feed_title', '') or '').lower()

        # 优先级源加分
        for src in PRIORITY_SOURCES:
            if src.lower() in feed:
                score += 3
                break

        # 有详细摘要加分
        if len(art.get('summary', '')) > 200:
            score += 1

        # 包含技术关键词加分
        cats = categorize_article(art)
        score += len(cats)

        scored.append((score, art))

    # 按分数排序
    scored.sort(key=lambda x: -x[0])
    return [art for score, art in scored[:limit]]


def select_deep_dive_articles(articles, limit=8):
    """筛选深度解读文章（技术性强、有详细内容的）"""
    candidates = []
    for art in articles:
        if not is_developer_focused(art):
            continue

        summary = art.get('summary', '')
        title = art.get('title', '')

        # 需要有一定的长度
        if len(summary) < 150:
            continue

        # 排除纯公告类
        if any(x in title.lower() for x in ['job', 'hiring', 'event', 'webinar']):
            continue

        # 技术深度判断
        depth_score = 0
        cats = categorize_article(art)
        depth_score += len(cats)

        if any(x in summary.lower() for x in ['how to', 'tutorial', 'guide', 'deep dive', 'analysis',
                                               'architecture', 'implementation', 'benchmark', 'performance']):
            depth_score += 2

        candidates.append((depth_score, art))

    candidates.sort(key=lambda x: -x[0])
    return [art for score, art in candidates[:limit]]


def select_tools(articles, limit=4):
    """筛选工具推荐"""
    tools = []
    for art in articles:
        title = (art.get('title', '') or '').lower()
        summary = (art.get('summary', '') or '').lower()
        feed = (art.get('feed_title', '') or '').lower()

        # 工具相关关键词
        tool_keywords = ['release', 'launch', 'beta', 'alpha', 'new version', 'update',
                        'tool', 'extension', 'plugin', 'sdk', 'library', 'framework',
                        'ide', 'cli', 'vscode', 'github']

        is_tool = any(kw in title or kw in summary for kw in tool_keywords)

        # 特定工具源
        tool_sources = ['visual studio', 'jetbrains', 'replit', 'cursor', 'figma', 'vercel']
        is_tool = is_tool or any(src in feed for src in tool_sources)

        if is_tool and is_developer_focused(art):
            tools.append(art)

    # 去重（按标题）
    seen = set()
    unique_tools = []
    for tool in tools:
        key = tool.get('title', '')[:30]
        if key not in seen:
            seen.add(key)
            unique_tools.append(tool)

    return unique_tools[:limit]


def generate_summary_for_article(article):
    """为文章生成简洁的中文总结"""
    title = article.get('title', '')
    summary = article.get('summary', '')
    feed = article.get('feed_title', '')

    # 如果有详细摘要，提取关键信息
    if len(summary) > 200:
        # 尝试提取第一句作为核心
        sentences = re.split(r'[.!?。！？]', summary)
        key_points = []
        for s in sentences[:3]:
            s = s.strip()
            if len(s) > 20 and len(s) < 200:
                key_points.append(s)

        if key_points:
            return ' '.join(key_points)

    return summary[:300] if summary else title


def generate_html(tech_data):
    """生成 HTML 日报"""
    articles = tech_data.get('articles', [])

    # 选择各类文章
    hot_articles = select_hot_articles(articles, limit=20)
    deep_dive_articles = select_deep_dive_articles(articles, limit=8)
    tools = select_tools(articles, limit=4)

    today = datetime.now().strftime('%Y-%m-%d')

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>开发者实践版科技日报 - {today}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        header p {{
            opacity: 0.8;
            font-size: 1.1em;
            color: #aaa;
        }}

        .section {{
            margin-bottom: 50px;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #00d9ff;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(0, 217, 255, 0.3);
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .section-title .count {{
            background: rgba(0, 217, 255, 0.2);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.6em;
        }}

        /* 热榜样式 */
        .hot-list {{
            display: grid;
            gap: 16px;
        }}
        .hot-item {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }}
        .hot-item:hover {{
            background: rgba(255,255,255,0.08);
            transform: translateX(5px);
        }}
        .hot-item .rank {{
            display: inline-block;
            width: 28px;
            height: 28px;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            color: #1a1a2e;
            text-align: center;
            line-height: 28px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 0.9em;
            margin-right: 12px;
        }}
        .hot-item .title {{
            color: #fff;
            font-size: 1.1em;
            display: inline;
        }}
        .hot-item .title a {{
            color: #fff;
            text-decoration: none;
        }}
        .hot-item .title a:hover {{
            color: #00d9ff;
        }}
        .hot-item .summary {{
            color: #aaa;
            font-size: 0.9em;
            margin-top: 10px;
            line-height: 1.6;
            padding-left: 40px;
        }}
        .hot-item .meta {{
            margin-top: 10px;
            padding-left: 40px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        /* 深度解读样式 */
        .deep-dive-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(480px, 1fr));
            gap: 24px;
        }}
        .deep-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }}
        .deep-card:hover {{
            background: rgba(255,255,255,0.08);
            border-color: rgba(0, 217, 255, 0.3);
        }}
        .deep-card h3 {{
            color: #fff;
            font-size: 1.2em;
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        .deep-card h3 a {{
            color: #fff;
            text-decoration: none;
        }}
        .deep-card h3 a:hover {{
            color: #00d9ff;
        }}
        .deep-card .summary {{
            color: #ccc;
            font-size: 0.95em;
            line-height: 1.7;
            margin-bottom: 16px;
        }}
        .deep-card .tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .deep-card .tag {{
            background: rgba(0, 217, 255, 0.15);
            color: #00d9ff;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.8em;
        }}

        /* 工具推荐样式 */
        .tools-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }}
        .tool-card {{
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.1), rgba(0, 255, 136, 0.05));
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(0, 217, 255, 0.2);
        }}
        .tool-card h3 {{
            color: #00ff88;
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .tool-card h3 a {{
            color: #00ff88;
            text-decoration: none;
        }}
        .tool-card h3 a:hover {{
            color: #00d9ff;
        }}
        .tool-card .description {{
            color: #ddd;
            font-size: 0.95em;
            line-height: 1.6;
            margin-bottom: 12px;
        }}
        .tool-card .source {{
            color: #888;
            font-size: 0.85em;
        }}

        /* 参考链接样式 */
        .references-section {{
            background: rgba(255,255,255,0.03);
            border-radius: 16px;
            padding: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .ref-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 12px;
        }}
        .ref-item {{
            background: rgba(255,255,255,0.05);
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .ref-item a {{
            color: #00d9ff;
            text-decoration: none;
            font-size: 0.95em;
            display: block;
            margin-bottom: 6px;
            word-break: break-word;
        }}
        .ref-item a:hover {{
            text-decoration: underline;
        }}
        .ref-item .source {{
            color: #888;
            font-size: 0.8em;
        }}

        /* 来源标签 */
        .source-tag {{
            display: inline-block;
            background: rgba(0, 217, 255, 0.1);
            color: #00d9ff;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            text-decoration: none;
            border: 1px solid rgba(0, 217, 255, 0.2);
        }}
        .source-tag:hover {{
            background: rgba(0, 217, 255, 0.2);
        }}

        /* 响应式 */
        @media (max-width: 768px) {{
            .deep-dive-grid, .tools-grid {{
                grid-template-columns: 1fr;
            }}
            header h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>开发者实践版科技日报</h1>
            <p>聚焦技术细节 · 关注工具更新 · 分享最佳实践</p>
            <p style="margin-top: 10px; color: #666;">{today} · 过去 24 小时技术动态</p>
        </header>
'''

    # 今日技术热榜
    html += '''
        <section class="section">
            <h2 class="section-title">
                今日技术热榜 <span class="count">''' + str(len(hot_articles)) + ''' 条</span>
            </h2>
            <div class="hot-list">
'''

    for i, art in enumerate(hot_articles, 1):
        title = art.get('title', 'No Title')
        link = art.get('link', '#')
        summary = generate_summary_for_article(art)
        source_link = generate_source_link(art)

        # 截断过长的标题
        if len(title) > 100:
            title = title[:97] + '...'

        html += f'''
                <div class="hot-item">
                    <span class="rank">{i}</span>
                    <span class="title"><a href="{link}" target="_blank">{title}</a></span>
                    <div class="summary">{summary[:200]}{'...' if len(summary) > 200 else ''}</div>
                    <div class="meta">{source_link}</div>
                </div>
'''

    html += '''
            </div>
        </section>
'''

    # 深度技术解读
    html += '''
        <section class="section">
            <h2 class="section-title">
                深度技术解读 <span class="count">''' + str(len(deep_dive_articles)) + ''' 条</span>
            </h2>
            <div class="deep-dive-grid">
'''

    for art in deep_dive_articles:
        title = art.get('title', 'No Title')
        link = art.get('link', '#')
        summary = generate_summary_for_article(art)
        cats = categorize_article(art)
        source_link = generate_source_link(art)

        # 生成类别标签
        cat_names = {
            'ai_ml': 'AI/ML',
            'frontend': '前端',
            'backend': '后端',
            'devops': 'DevOps',
            'cloud': '云计算',
            'database': '数据库',
            'tools': '开发工具',
            'security': '安全',
            'mobile': '移动开发',
            'data': '数据工程'
        }
        tags = ''.join(f'<span class="tag">{cat_names.get(c, c)}</span>' for c in cats[:3])

        html += f'''
                <div class="deep-card">
                    <h3><a href="{link}" target="_blank">{title}</a></h3>
                    <div class="tags">{tags}</div>
                    <div class="summary">{summary[:350]}{'...' if len(summary) > 350 else ''}</div>
                    <div>{source_link}</div>
                </div>
'''

    html += '''
            </div>
        </section>
'''

    # 工具推荐
    html += '''
        <section class="section">
            <h2 class="section-title">
                工具推荐 <span class="count">''' + str(len(tools)) + ''' 个</span>
            </h2>
            <div class="tools-grid">
'''

    for tool in tools:
        title = tool.get('title', 'No Title')
        link = tool.get('link', '#')
        summary = generate_summary_for_article(tool)

        html += f'''
                <div class="tool-card">
                    <h3><a href="{link}" target="_blank">{title}</a></h3>
                    <div class="description">{summary[:250]}{'...' if len(summary) > 250 else ''}</div>
                    <div class="source">{generate_source_link(tool)}</div>
                </div>
'''

    html += '''
            </div>
        </section>
'''

    # 参考链接汇总
    html += '''
        <section class="section references-section">
            <h2 class="section-title">参考链接汇总</h2>
            <div class="ref-grid">
'''

    # 收集所有唯一链接
    all_links = {}
    for art in hot_articles + deep_dive_articles + tools:
        link = art.get('link', '#')
        title = art.get('title', 'No Title')
        feed = art.get('feed_title', 'Unknown')

        if link and link != '#' and link not in all_links:
            all_links[link] = {'title': title[:60], 'feed': feed}

    for link, info in list(all_links.items())[:50]:  # 限制最多 50 条
        html += f'''
                <div class="ref-item">
                    <a href="{link}" target="_blank">{info['title']}</a>
                    <span class="source">{info['feed']}</span>
                </div>
'''

    html += '''
            </div>
        </section>
    </div>
</body>
</html>
'''

    return html


def main():
    """主函数"""
    print("加载新闻数据...")
    tech_data = load_articles(INPUT_JSON)
    print(f"加载了 {len(tech_data.get('articles', []))} 篇文章")

    print("生成开发者实践版科技日报...")
    html_content = generate_html(tech_data)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)

    # 写入文件
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"日报已生成：{OUTPUT_HTML}")


if __name__ == '__main__':
    main()
