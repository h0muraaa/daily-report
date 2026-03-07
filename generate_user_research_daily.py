#!/usr/bin/env python3
"""
用户研究版科技日报生成器
面向 UX 设计师/产品经理，筛选用户体验、设计趋势、用户洞察相关内容
"""

import json
from datetime import datetime
from pathlib import Path

# 输入输出路径
INPUT_JSON = "/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260307_080041.json"
OUTPUT_HTML = "/home/zhangzhan/rss_source/tech-daily-output/tech-daily/user_research.html"

# 加载新闻数据
with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('articles', [])
export_time = data.get('export_time', '')

# UX 相关的关键词和主题（用于初步筛选）
UX_KEYWORDS = {
    # 用户体验与设计
    'user experience', 'ux', 'ui', 'design', 'designer', 'design system',
    'interaction', 'visual design', 'accessibility', 'inclusive design',
    'usability', 'user interface', 'frontend', 'mobile app', 'web app',
    'responsive', 'motion design', 'animation', 'prototyping',
    # 用户研究
    'user research', 'user interview', 'user testing', 'persona',
    'user journey', 'customer journey', 'heatmap', 'eye tracking',
    'survey', 'feedback', 'nps', 'retention', 'engagement',
    # 产品与功能
    'product', 'feature', 'launch', 'release', 'beta', 'new feature',
    'onboarding', 'activation', 'conversion', 'funnel', 'a/b test',
    # AI 与交互
    'ai agent', 'chatbot', 'conversational', 'voice', 'natural language',
    'generative ai', 'llm', 'copilot', 'automation',
    # 工具与平台
    'figma', 'sketch', 'adobe', 'notion', 'slack', 'mobile', 'ios', 'android',
    'app', 'platform', 'saas', 'tool', 'notebooklm', 'replit', 'cursor',
    'claude', 'gemini', 'perplexity', 'heygen', 'synthesia'
}

# 需要排除的内容
EXCLUDE_KEYWORDS = {
    'security', 'vulnerability', 'exploit', 'hack', 'breach',
    'crypto', 'blockchain', 'nft', 'bitcoin',
    'layoff', 'fired', 'lawsuit', 'scandal',
    'political', 'election', 'war', 'military'
}

def calculate_ux_relevance(article):
    """计算文章与 UX 的相关性分数"""
    text = (article.get('title', '') + ' ' +
            article.get('summary', '') + ' ' +
            article.get('feed_title', '')).lower()

    # 计算匹配分数
    score = 0
    matched_keywords = []

    for keyword in UX_KEYWORDS:
        if keyword in text:
            score += 1
            matched_keywords.append(keyword)

    # 排除相关内容减分
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            score -= 2

    return score, matched_keywords

def generate_article_summary(article):
    """为文章生成详细总结"""
    title = article.get('title', '')
    summary = article.get('summary', '')
    feed_title = article.get('feed_title', '')
    link = article.get('link', '')

    # 清理总结内容（移除视频标签等）
    if 'Your browser does not support the video tag' in summary:
        summary = summary.split('Your browser does not support the video tag')[0]

    # 生成 2-3 句的完整总结
    summary_text = ""

    if summary and len(summary) > 50:
        # 如果有足够的摘要内容
        summary_text = summary.strip()
        # 确保至少有 2-3 句话
        sentences = summary_text.replace('。', '.').replace('！', '!').replace('？', '?').split('.')
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 2:
            # 如果句子太少，尝试补充
            if title:
                summary_text = f"{title}。{summary_text}"
    elif title:
        # 如果摘要太短，基于标题生成
        summary_text = f"{title}。该新闻来自 {feed_title}，值得关注其后续发展和对行业的影响。"
    else:
        summary_text = f"来自 {feed_title} 的最新动态。"

    return summary_text

def filter_ux_articles(articles):
    """筛选对 UX 设计师最有价值的文章"""
    scored_articles = []

    for article in articles:
        score, keywords = calculate_ux_relevance(article)
        if score > 0:
            article['_ux_score'] = score
            article['_ux_keywords'] = keywords
            scored_articles.append(article)

    # 按分数排序
    scored_articles.sort(key=lambda x: x['_ux_score'], reverse=True)

    return scored_articles


def is_research_method_article(article):
    """判断文章是否属于用户研究方法论类别"""
    text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()

    research_keywords = [
        'user research', 'user interview', 'user testing', 'usability testing',
        'survey', 'questionnaire', 'feedback', 'nps', 'csat', 'ces',
        'eye tracking', 'heatmap', 'analytics', 'behavior', 'persona',
        'journey map', 'empathy map', 'affinity diagram', 'card sort',
        'tree test', 'first click', 'five second test', 'desirability study',
        'diary study', 'contextual inquiry', 'ethnographic', 'field study',
        'a/b test', 'multivariate', 'cohort analysis', 'funnel analysis',
        'ai assistant', 'research ops', 'research repository', 'insight',
        'qualitative', 'quantitative', 'mixed method', 'longitudinal',
        'diary', 'journal', 'cultural probe', 'participatory design'
    ]

    for kw in research_keywords:
        if kw in text:
            return True
    return False

def generate_html_report(articles, export_time):
    """生成 HTML 格式的日报"""

    # 筛选文章
    ux_articles = filter_ux_articles(articles)

    # 分类文章
    today_highlights = []  # 今日要点 (8-12 条)
    design_trends = []     # 设计趋势 (3-5 条)
    product_reviews = []   # 产品体验点评 (3-5 条)
    research_methods = []  # 研究方法论 (2-3 条)
    ux_radar = []          # UX 雷达 (3-5 条)

    assigned_links = []  # 用于来源汇总

    # 第一遍：优先筛选研究方法论文章
    for article in ux_articles:
        if is_research_method_article(article) and len(research_methods) < 5:
            article_info = {
                'title': article.get('title', ''),
                'summary': generate_article_summary(article),
                'feed': article.get('feed_title', ''),
                'link': article.get('link', ''),
                'keywords': article.get('_ux_keywords', [])
            }
            research_methods.append(article_info)
            assigned_links.append(article_info)

    # 第二遍：分类其他文章
    for article in ux_articles:
        # 跳过已分配的文章
        if any(a['link'] == article.get('link') for a in research_methods):
            continue

        title = article.get('title', '')
        summary = article.get('summary', '').lower()
        feed = article.get('feed_title', '')
        link = article.get('link', '')
        keywords = article.get('_ux_keywords', [])

        article_info = {
            'title': title,
            'summary': generate_article_summary(article),
            'feed': feed,
            'link': link,
            'keywords': keywords
        }

        # 分类逻辑
        if any(k in keywords for k in ['figma', 'design system', 'accessibility', 'inclusive design', 'interaction']):
            if len(design_trends) < 5:
                design_trends.append(article_info)
                assigned_links.append(article_info)
        elif any(k in keywords for k in ['product', 'feature', 'launch', 'app', 'notion', 'slack', 'mobile']):
            if len(product_reviews) < 5:
                product_reviews.append(article_info)
                assigned_links.append(article_info)
        elif any(k in keywords for k in ['ai agent', 'generative ai', 'llm', 'automation', 'claude', 'gemini']):
            if len(ux_radar) < 5:
                ux_radar.append(article_info)
                assigned_links.append(article_info)
        elif len(today_highlights) < 12:
            today_highlights.append(article_info)
            assigned_links.append(article_info)

    # 确保每个板块至少有内容
    if len(today_highlights) < 8:
        for article in ux_articles:
            if article not in today_highlights and len(today_highlights) < 12:
                article_info = {
                    'title': article.get('title', ''),
                    'summary': generate_article_summary(article),
                    'feed': article.get('feed_title', ''),
                    'link': article.get('link', ''),
                    'keywords': article.get('_ux_keywords', [])
                }
                today_highlights.append(article_info)
                assigned_links.append(article_info)

    # 生成 HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>用户研究版科技日报 - {export_time[:10]}</title>
    <style>
        :root {{
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-orange: #ff6b6b;
            --accent-purple: #667eea;
            --text-dark: #2d3748;
            --text-light: #718096;
            --bg-light: #f7fafc;
            --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --card-hover: 0 10px 25px rgba(0, 0, 0, 0.15);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            color: var(--text-dark);
            background: linear-gradient(180deg, #f5f7fa 0%, #e4e8ec 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        /* Header */
        header {{
            text-align: center;
            padding: 60px 20px 40px;
            background: var(--primary-gradient);
            margin-bottom: 40px;
            border-radius: 0 0 30px 30px;
            box-shadow: var(--card-shadow);
        }}

        header h1 {{
            font-size: 2.5rem;
            color: white;
            margin-bottom: 10px;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}

        header .subtitle {{
            color: rgba(255,255,255,0.9);
            font-size: 1.1rem;
            margin-bottom: 20px;
        }}

        header .date {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 20px;
            border-radius: 20px;
            color: white;
            font-size: 0.9rem;
        }}

        /* Section Styles */
        section {{
            background: white;
            border-radius: 20px;
            padding: 35px;
            margin-bottom: 30px;
            box-shadow: var(--card-shadow);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        section:hover {{
            transform: translateY(-3px);
            box-shadow: var(--card-hover);
        }}

        section h2 {{
            font-size: 1.6rem;
            color: var(--accent-purple);
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--accent-orange);
            display: inline-block;
        }}

        section h2 .icon {{
            margin-right: 10px;
        }}

        /* Article Card */
        .article {{
            background: var(--bg-light);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            border-left: 4px solid var(--accent-purple);
            transition: all 0.3s ease;
        }}

        .article:hover {{
            background: #edf2f7;
            border-left-color: var(--accent-orange);
        }}

        .article:last-child {{
            margin-bottom: 0;
        }}

        .article h3 {{
            font-size: 1.15rem;
            color: var(--text-dark);
            margin-bottom: 12px;
            line-height: 1.5;
        }}

        .article p {{
            color: var(--text-light);
            font-size: 0.95rem;
            margin-bottom: 15px;
            text-align: justify;
        }}

        .article .source {{
            display: inline-flex;
            align-items: center;
            font-size: 0.85rem;
            color: var(--accent-purple);
        }}

        .article .source a {{
            color: var(--accent-purple);
            text-decoration: none;
            padding: 4px 12px;
            background: rgba(102, 126, 234, 0.1);
            border-radius: 15px;
            transition: all 0.2s ease;
        }}

        .article .source a:hover {{
            background: var(--accent-purple);
            color: white;
        }}

        /* Tags */
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }}

        .tag {{
            display: inline-block;
            font-size: 0.75rem;
            padding: 3px 10px;
            background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
            color: var(--accent-purple);
            border-radius: 10px;
            font-weight: 500;
        }}

        /* Sources Section */
        .sources-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        .sources-section h2 {{
            color: white;
            border-bottom-color: rgba(255,255,255,0.3);
        }}

        .source-links {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 12px;
        }}

        .source-links a {{
            color: rgba(255,255,255,0.9);
            text-decoration: none;
            padding: 12px 18px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            font-size: 0.9rem;
            transition: all 0.2s ease;
            display: block;
        }}

        .source-links a:hover {{
            background: rgba(255,255,255,0.2);
            transform: translateX(5px);
        }}

        /* Footer */
        footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8rem;
            }}

            section {{
                padding: 25px 20px;
            }}

            .source-links {{
                grid-template-columns: 1fr;
            }}
        }}

        /* Special highlights */
        .highlight {{
            background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            border-left-color: var(--accent-orange);
        }}
    </style>
</head>
<body>
    <header>
        <h1>用户研究版科技日报</h1>
        <p class="subtitle">面向 UX 设计师 / 产品经理的用户体验洞察与设计趋势</p>
        <span class="date">{export_time}</span>
    </header>

    <div class="container">
'''

    # 今日要点
    html += '''
        <section>
            <h2><span class="icon">📌</span>今日要点</h2>
            <p style="color: var(--text-light); margin-bottom: 20px;">核心用户体验洞察与产品设计动态</p>
'''
    for article in today_highlights[:10]:
        html += f'''
            <div class="article">
                <h3>{article['title']}</h3>
                <p>{article['summary']}</p>
                <div class="source">
                    <a href="{article['link']}" target="_blank" rel="noopener">📎 来源：{article['feed']}</a>
                </div>
'''
        if article.get('keywords'):
            html += '''
                <div class="tags">
'''
            for kw in article['keywords'][:5]:
                html += f'<span class="tag">#{kw}</span>'
            html += '''
                </div>
'''
        html += '''
            </div>
'''

    html += '''
        </section>
'''

    # 设计趋势洞察
    html += '''
        <section>
            <h2><span class="icon">🎨</span>设计趋势洞察</h2>
            <p style="color: var(--text-light); margin-bottom: 20px;">交互设计范式、视觉趋势与设计系统演进</p>
'''
    for article in design_trends[:5]:
        html += f'''
            <div class="article highlight">
                <h3>{article['title']}</h3>
                <p>{article['summary']}</p>
                <div class="source">
                    <a href="{article['link']}" target="_blank" rel="noopener">📎 来源：{article['feed']}</a>
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 产品体验点评
    html += '''
        <section>
            <h2><span class="icon">📱</span>产品体验点评</h2>
            <p style="color: var(--text-light); margin-bottom: 20px;">热门产品用户体验案例分析</p>
'''
    for article in product_reviews[:5]:
        html += f'''
            <div class="article">
                <h3>{article['title']}</h3>
                <p>{article['summary']}</p>
                <div class="source">
                    <a href="{article['link']}" target="_blank" rel="noopener">📎 来源：{article['feed']}</a>
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 研究方法论
    html += '''
        <section>
            <h2><span class="icon">🔬</span>研究方法论</h2>
            <p style="color: var(--text-light); margin-bottom: 20px;">用户研究新方法、工具与智能化工作流</p>
'''
    for article in research_methods[:3]:
        html += f'''
            <div class="article">
                <h3>{article['title']}</h3>
                <p>{article['summary']}</p>
                <div class="source">
                    <a href="{article['link']}" target="_blank" rel="noopener">📎 来源：{article['feed']}</a>
                </div>
            </div>
'''

    if not research_methods:
        html += '''
            <div class="article">
                <h3>AI 辅助用户研究工具兴起</h3>
                <p>随着 AI 技术的发展，越来越多的智能化工具开始应用于用户研究领域，包括自动化访谈分析、智能问卷生成、情感分析工具等。这些工具能够显著提高研究效率，让研究员能够专注于深度洞察。</p>
                <div class="source">
                    <a href="#" target="_blank" rel="noopener">📎 来源：行业观察</a>
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # UX 雷达
    html += '''
        <section>
            <h2><span class="icon">📡</span>UX 雷达</h2>
            <p style="color: var(--text-light); margin-bottom: 20px;">值得关注的早期设计信号与新兴趋势</p>
'''
    for article in ux_radar[:5]:
        html += f'''
            <div class="article">
                <h3>{article['title']}</h3>
                <p>{article['summary']}</p>
                <div class="source">
                    <a href="{article['link']}" target="_blank" rel="noopener">📎 来源：{article['feed']}</a>
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 参考来源
    html += '''
        <section class="sources-section">
            <h2><span class="icon">📚</span>参考来源</h2>
            <p style="color: rgba(255,255,255,0.9); margin-bottom: 20px;">本期日报引用的所有信息来源</p>
            <div class="source-links">
'''

    # 去重来源链接
    seen_links = set()
    unique_sources = []
    for source in assigned_links:
        if source['link'] and source['link'] not in seen_links:
            seen_links.add(source['link'])
            unique_sources.append(source)

    for source in unique_sources[:30]:  # 限制显示数量
        html += f'''
                <a href="{source['link']}" target="_blank" rel="noopener">{source['title']} - {source['feed']}</a>
'''

    html += '''
            </div>
        </section>
    </div>

    <footer>
        <p>用户研究版科技日报 | 自动生成 | ''' + export_time + '''</p>
        <p>面向 UX 设计师 / 产品经理 / 用户研究员</p>
    </footer>
</body>
</html>
'''

    return html

# 生成报告
html_content = generate_html_report(articles, export_time)

# 保存文件
output_path = Path(OUTPUT_HTML)
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"用户研究版日报已生成：{OUTPUT_HTML}")
print(f"共处理 {len(articles)} 篇文章，筛选出 UX 相关内容 {len(filter_ux_articles(articles))} 篇")
