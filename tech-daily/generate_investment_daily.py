#!/usr/bin/env python3
"""
投资分析版科技日报生成器
从投资者视角筛选新闻，关注市场机会、估值逻辑、风险评估
"""

import json
from datetime import datetime
from typing import List, Dict, Any

# 输入输出路径
INPUT_JSON = '/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260325_080554.json'
OUTPUT_HTML = '/home/zhangzhan/rss_source/tech-daily-output/tech-daily/investment_analysis.html'

# 投资相关关键词（按优先级分类）
INVESTMENT_KEYWORDS = {
    'high': ['融资', '投资', '并购', 'IPO', '上市', '估值', '收购', '领投', '参投',
             'funding', 'acquisition', 'IPO', 'valuation', 'Series A', 'Series B',
             'Series C', 'invest', 'raise', 'billion', 'million'],
    'medium': ['财报', '轮', '亿美元', '百万美元', '营收', '利润', '财报', '季报', '年报',
               'revenue', 'earnings', 'profit', 'quarterly', 'annual'],
    'low': ['创业', '创始人', '初创', '孵化器', 'YC', 'a16z', '红杉', '风投', 'PE', 'VC',
            'startup', 'founder', 'incubator', 'venture', 'capital']
}

def load_articles(json_path: str) -> List[Dict[str, Any]]:
    """加载 JSON 文章数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('articles', [])

def calculate_investment_score(article: Dict[str, Any]) -> int:
    """计算文章的投资相关度分数"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    feed_title = (article.get('feed_title', '') or '').lower()

    text = f"{title} {summary} {feed_title}"

    score = 0
    for kw in INVESTMENT_KEYWORDS['high']:
        if kw.lower() in text:
            score += 3
    for kw in INVESTMENT_KEYWORDS['medium']:
        if kw.lower() in text:
            score += 2
    for kw in INVESTMENT_KEYWORDS['low']:
        if kw.lower() in text:
            score += 1

    return score

def filter_investment_articles(articles: List[Dict[str, Any]], min_score: int = 2) -> List[Dict[str, Any]]:
    """筛选投资相关文章"""
    scored_articles = []
    for article in articles:
        score = calculate_investment_score(article)
        if score >= min_score:
            article['investment_score'] = score
            scored_articles.append(article)

    # 按分数排序
    scored_articles.sort(key=lambda x: x['investment_score'], reverse=True)
    return scored_articles

def categorize_articles(articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """将文章分类到不同板块"""
    categories = {
        'market_overview': [],      # 市场概览 - 投融资动态
        'deep_analysis': [],        # 深度分析 - 重点投资事件
        'sector_radar': [],         # 赛道雷达 - 细分赛道
        'valuation_watch': [],      # 估值观察
        'tomorrow_watch': []        # 明日看点
    }

    # 分类关键词
    sector_keywords = {
        'AI/大模型': ['GPT', 'AI', '大模型', 'LLM', 'Gemini', 'Claude', 'OpenAI', 'Anthropic', 'deepseek'],
        '半导体/芯片': ['芯片', '半导体', 'GPU', 'NVIDIA', '英伟达', 'AMD', 'Intel', '博通'],
        '云计算/SaaS': ['云', 'SaaS', 'PaaS', 'IaaS', 'AWS', 'Azure', 'Google Cloud'],
        '智能硬件': ['硬件', '手机', 'MacBook', '电池', '机器人', 'Tesla', '比亚迪'],
        '互联网平台': ['平台', 'Google', 'GitHub', 'App', '第三方', '支付', '游戏']
    }

    for article in articles:
        title = (article.get('title', '') or '').lower()
        summary = (article.get('summary', '') or '').lower()
        text = f"{title} {summary}"

        # 判断是否属于深度分析（高分文章）
        if article.get('investment_score', 0) >= 4:
            categories['deep_analysis'].append(article)
        # 判断是否属于估值相关
        elif any(kw in text for kw in ['估值', 'valuation', 'billion', '亿美', '市值']):
            categories['valuation_watch'].append(article)
        # 按赛道分类
        else:
            categorized = False
            for sector, keywords in sector_keywords.items():
                if any(kw.lower() in text for kw in keywords):
                    categories['sector_radar'].append({**article, 'sector': sector})
                    categorized = True
                    break

            # 未分类的放入市场概览
            if not categorized:
                categories['market_overview'].append(article)

    # 明日看点：选择有前瞻性的新闻
    future_keywords = ['将', '即将', '预计', '计划', '预告', 'upcoming', 'will', 'going to']
    for article in articles:
        title = (article.get('title', '') or '').lower()
        summary = (article.get('summary', '') or '').lower()
        if any(kw in title or kw in summary for kw in future_keywords):
            if article not in categories['tomorrow_watch']:
                categories['tomorrow_watch'].append(article)

    # 限制每个类别的数量
    categories['market_overview'] = categories['market_overview'][:12]
    categories['deep_analysis'] = categories['deep_analysis'][:8]
    categories['sector_radar'] = categories['sector_radar'][:10]
    categories['valuation_watch'] = categories['valuation_watch'][:8]
    categories['tomorrow_watch'] = categories['tomorrow_watch'][:5]

    return categories

def generate_summary(article: Dict[str, Any]) -> str:
    """为文章生成 2-3 句投资视角的总结"""
    title = article.get('title', '')
    summary = article.get('summary', '')

    # 清理摘要中的多余字符
    summary = summary.replace('💬', '').replace('🔄', '').replace('❤️', '')
    summary = summary.replace('👀', '').replace('📊', '').replace('⚡', '')
    summary = ' '.join(summary.split())  # 移除多余空格

    # 如果是中文摘要，直接使用（通常已包含关键信息）
    if any('\u4e00' <= c <= '\u9fff' for c in summary[:100]):
        # 截断过长的摘要
        if len(summary) > 300:
            summary = summary[:300].rsplit(' ', 1)[0] + '...'
        return summary

    # 如果是英文摘要，尝试生成投资视角的解读
    if title:
        return f"重要动态：{title}。投资者需关注其市场影响和商业模式变化。"

    return summary[:200] if summary else "暂无详细信息"

def generate_investment_insight(article: Dict[str, Any]) -> str:
    """生成投资逻辑分析"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    text = f"{title} {summary}"

    insights = []

    # 融资相关
    if any(kw in text for kw in ['融资', 'funding', '领投', 'Series']):
        insights.append("融资事件反映赛道热度，建议关注领投方背景和资金用途")

    # IPO 相关
    if any(kw in text for kw in ['IPO', '上市', 'public']):
        insights.append("IPO 进程影响一级市场退出预期，估值对标需审慎")

    # 估值相关
    if any(kw in text for kw in ['估值', 'valuation', 'billion', '亿']):
        insights.append("高估值需验证商业模式可持续性，关注营收增速和留存率")

    # AI/大模型
    if any(kw in text for kw in ['AI', '大模型', 'GPT', 'LLM']):
        insights.append("AI 赛道竞争加剧，关注差异化定位和商业化落地能力")

    # 芯片/半导体
    if any(kw in text for kw in ['芯片', '半导体', 'GPU', 'NVIDIA']):
        insights.append("半导体周期底部布局机会，关注国产替代和 AI 算力需求")

    # 默认洞察
    if not insights:
        insights.append("建议持续关注公司基本面和行业动态")

    return " | ".join(insights)

def generate_risk_hint(article: Dict[str, Any]) -> str:
    """生成风险提示"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    text = f"{title} {summary}"

    risks = []

    if any(kw in text for kw in ['涨价', 'price', 'cost']):
        risks.append("成本上升风险")
    if any(kw in text for kw in ['离职', 'departure', 'exit']):
        risks.append("核心团队变动风险")
    if any(kw in text for kw in ['竞争', 'competition', 'rival']):
        risks.append("行业竞争加剧风险")
    if any(kw in text for kw in ['监管', 'regulation', 'policy']):
        risks.append("政策监管风险")
    if any(kw in text for kw in ['亏损', 'loss', 'deficit']):
        risks.append("盈利不确定性风险")

    return " | ".join(risks) if risks else "常规经营风险"

def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    if not text:
        return ""
    return (text.replace('&', '&amp;')
               .replace('<', '&lt;')
               .replace('>', '&gt;')
               .replace('"', '&quot;')
               .replace("'", '&#39;'))

def generate_html_report(categories: Dict[str, List[Dict[str, Any]]],
                         metadata: Dict[str, Any]) -> str:
    """生成 HTML 报告"""

    report_date = metadata.get('end_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))[:10]
    total_articles = metadata.get('total_count', 0)
    source_count = metadata.get('source_count', 0)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>科技投资日报 - {report_date}</title>
    <style>
        :root {{
            --primary-color: #1a5f7a;
            --secondary-color: #57837b;
            --accent-color: #c38e70;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #2c3e50;
            --text-light: #7f8c8d;
            --border-color: #e0e0e0;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        header .meta {{
            font-size: 0.95rem;
            opacity: 0.9;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}

        header .meta span {{
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 20px;
        }}

        .section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border: 1px solid var(--border-color);
        }}

        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid var(--primary-color);
        }}

        .section-title {{
            font-size: 1.5rem;
            color: var(--primary-color);
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-title .icon {{
            font-size: 1.8rem;
        }}

        .section-count {{
            background: var(--primary-color);
            color: white;
            font-size: 0.85rem;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }}

        .card {{
            background: #fafbfc;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .card-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-color);
            margin-bottom: 8px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
        }}

        .card-title a {{
            color: var(--primary-color);
            text-decoration: none;
            word-break: break-word;
        }}

        .card-title a:hover {{
            text-decoration: underline;
        }}

        .card-source {{
            display: inline-block;
            background: var(--secondary-color);
            color: white;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
        }}

        .card-summary {{
            color: var(--text-light);
            font-size: 0.95rem;
            line-height: 1.7;
            margin-bottom: 12px;
            text-align: justify;
        }}

        .card-meta {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            font-size: 0.85rem;
            padding-top: 12px;
            border-top: 1px solid var(--border-color);
        }}

        .card-meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .card-meta-label {{
            color: var(--text-light);
            font-weight: 500;
        }}

        .card-meta-value {{
            color: var(--primary-color);
            font-weight: 600;
        }}

        .insight-box {{
            background: #e8f4f8;
            border-left: 4px solid var(--primary-color);
            padding: 12px 15px;
            margin-top: 12px;
            border-radius: 0 8px 8px 0;
        }}

        .insight-label {{
            color: var(--primary-color);
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 5px;
        }}

        .insight-content {{
            color: var(--text-color);
            font-size: 0.9rem;
        }}

        .risk-box {{
            background: #fef3e2;
            border-left: 4px solid var(--warning-color);
            padding: 12px 15px;
            margin-top: 10px;
            border-radius: 0 8px 8px 0;
        }}

        .risk-label {{
            color: var(--warning-color);
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 5px;
        }}

        .risk-content {{
            color: var(--text-color);
            font-size: 0.9rem;
        }}

        .deep-analysis .card {{
            background: linear-gradient(135deg, #fafbfc 0%, #f0f4f8 100%);
            border: 1px solid #d0dce0;
        }}

        .valuation-badge {{
            display: inline-block;
            background: var(--accent-color);
            color: white;
            font-size: 0.8rem;
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 600;
            margin-left: 10px;
        }}

        .sector-tag {{
            display: inline-block;
            background: var(--secondary-color);
            color: white;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            margin-right: 8px;
        }}

        .data-source {{
            background: #f8f9fa;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-top: 30px;
        }}

        .data-source h3 {{
            color: var(--primary-color);
            font-size: 1.1rem;
            margin-bottom: 15px;
        }}

        .source-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 10px;
            max-height: 300px;
            overflow-y: auto;
        }}

        .source-item {{
            background: white;
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            font-size: 0.85rem;
        }}

        .source-item a {{
            color: var(--primary-color);
            text-decoration: none;
            word-break: break-word;
        }}

        .source-item a:hover {{
            text-decoration: underline;
        }}

        footer {{
            text-align: center;
            padding: 30px;
            color: var(--text-light);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
            margin-top: 30px;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8rem;
            }}

            .section {{
                padding: 15px;
            }}

            .card {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 科技投资日报</h1>
            <div class="meta">
                <span>📅 报告日期：{report_date}</span>
                <span>📰 监测文章：{total_articles} 篇</span>
                <span>📡 数据源：{source_count} 个</span>
                <span>🎯 投资视角筛选</span>
            </div>
        </header>
'''

    # 1. 市场概览
    market_items = categories.get('market_overview', [])[:12]
    html += f'''
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">🌍</span>
                    市场概览
                </h2>
                <span class="section-count">{len(market_items)} 条动态</span>
            </div>
'''

    for article in market_items:
        title = escape_html(article.get('title', '无标题'))
        link = escape_html(article.get('link', '#'))
        source = escape_html(article.get('feed_title', '未知来源'))
        summary = escape_html(generate_summary(article))
        published = escape_html(article.get('published_date', ''))

        html += f'''
            <div class="card">
                <div class="card-title">
                    <a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>
                    <span class="card-source">{source}</span>
                </div>
                <div class="card-summary">{summary}</div>
                <div class="card-meta">
                    <span class="card-meta-item">
                        <span class="card-meta-label">来源:</span>
                        <a href="{link}" target="_blank" rel="noopener noreferrer" class="card-meta-value">{source}</a>
                    </span>
                    {f'<span class="card-meta-item"><span class="card-meta-label">时间:</span><span class="card-meta-value">{published}</span></span>' if published else ''}
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 2. 深度分析
    deep_items = categories.get('deep_analysis', [])[:8]
    html += f'''
        <section class="section deep-analysis">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">🔍</span>
                    深度分析
                </h2>
                <span class="section-count">{len(deep_items)} 条精选</span>
            </div>
'''

    for article in deep_items:
        title = escape_html(article.get('title', '无标题'))
        link = escape_html(article.get('link', '#'))
        source = escape_html(article.get('feed_title', '未知来源'))
        summary = escape_html(generate_summary(article))
        insight = escape_html(generate_investment_insight(article))
        risk = escape_html(generate_risk_hint(article))
        published = escape_html(article.get('published_date', ''))

        html += f'''
            <div class="card">
                <div class="card-title">
                    <a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>
                    <span class="card-source">{source}</span>
                </div>
                <div class="card-summary">{summary}</div>
                <div class="insight-box">
                    <div class="insight-label">💡 投资逻辑</div>
                    <div class="insight-content">{insight}</div>
                </div>
                <div class="risk-box">
                    <div class="risk-label">⚠️ 风险提示</div>
                    <div class="risk-content">{risk}</div>
                </div>
                <div class="card-meta">
                    <span class="card-meta-item">
                        <span class="card-meta-label">来源链接:</span>
                        <a href="{link}" target="_blank" rel="noopener noreferrer" class="card-meta-value">点击查看原文</a>
                    </span>
                    {f'<span class="card-meta-item"><span class="card-meta-label">发布:</span><span class="card-meta-value">{published}</span></span>' if published else ''}
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 3. 赛道雷达
    sector_items = categories.get('sector_radar', [])[:10]
    sectors_grouped = {}
    for item in sector_items:
        sector = item.get('sector', '其他')
        if sector not in sectors_grouped:
            sectors_grouped[sector] = []
        sectors_grouped[sector].append(item)

    html += f'''
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">📡</span>
                    赛道雷达
                </h2>
                <span class="section-count">{len(sector_items)} 条</span>
            </div>
'''

    for sector, items in sectors_grouped.items():
        html += f'''
            <div class="card">
                <div class="card-title">
                    <span class="sector-tag">{escape_html(sector)}</span>
                    <span>{len(items)} 条相关动态</span>
                </div>
'''
        for article in items[:3]:  # 每个赛道最多显示 3 条
            title = escape_html(article.get('title', '无标题'))
            link = escape_html(article.get('link', '#'))
            source = escape_html(article.get('feed_title', '未知来源'))
            summary = escape_html(generate_summary(article)[:150])

            html += f'''
                <div style="margin: 10px 0 10px 20px; padding-left: 15px; border-left: 2px solid var(--border-color);">
                    <div style="margin-bottom: 5px;">
                        <a href="{link}" target="_blank" rel="noopener noreferrer" style="color: var(--primary-color); text-decoration: none; font-weight: 500;">{title}</a>
                        <span style="color: var(--text-light); font-size: 0.8rem; margin-left: 8px;">[{source}]</span>
                    </div>
                    <div style="color: var(--text-light); font-size: 0.85rem;">{summary}</div>
                </div>
'''
        html += '''
            </div>
'''

    html += '''
        </section>
'''

    # 4. 估值观察
    valuation_items = categories.get('valuation_watch', [])[:8]
    html += f'''
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">💰</span>
                    估值观察
                </h2>
                <span class="section-count">{len(valuation_items)} 条</span>
            </div>
'''

    for article in valuation_items:
        title = escape_html(article.get('title', '无标题'))
        link = escape_html(article.get('link', '#'))
        source = escape_html(article.get('feed_title', '未知来源'))
        summary = escape_html(generate_summary(article))
        insight = escape_html(generate_investment_insight(article))
        published = escape_html(article.get('published_date', ''))

        html += f'''
            <div class="card">
                <div class="card-title">
                    <a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>
                    <span class="card-source">{source}</span>
                </div>
                <div class="card-summary">{summary}</div>
                <div class="insight-box">
                    <div class="insight-label">📈 估值逻辑</div>
                    <div class="insight-content">{insight}</div>
                </div>
                <div class="card-meta">
                    <span class="card-meta-item">
                        <span class="card-meta-label">原文链接:</span>
                        <a href="{link}" target="_blank" rel="noopener noreferrer" class="card-meta-value">查看来源</a>
                    </span>
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 5. 明日看点
    tomorrow_items = categories.get('tomorrow_watch', [])[:5]
    html += f'''
        <section class="section">
            <div class="section-header">
                <h2 class="section-title">
                    <span class="icon">🔮</span>
                    明日看点
                </h2>
                <span class="section-count">{len(tomorrow_items)} 条前瞻</span>
            </div>
'''

    for article in tomorrow_items:
        title = escape_html(article.get('title', '无标题'))
        link = escape_html(article.get('link', '#'))
        source = escape_html(article.get('feed_title', '未知来源'))
        summary = escape_html(generate_summary(article))
        published = escape_html(article.get('published_date', ''))

        html += f'''
            <div class="card">
                <div class="card-title">
                    <a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>
                    <span class="card-source">{source}</span>
                </div>
                <div class="card-summary">{summary}</div>
                <div class="card-meta">
                    <span class="card-meta-item">
                        <span class="card-meta-label">来源:</span>
                        <a href="{link}" target="_blank" rel="noopener noreferrer" class="card-meta-value">{source}</a>
                    </span>
                    {f'<span class="card-meta-item"><span class="card-meta-label">预期时间:</span><span class="card-meta-value">{published}</span></span>' if published else ''}
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 6. 数据来源声明
    all_sources = set()
    for category_items in categories.values():
        for article in category_items:
            source = article.get('feed_title', '')
            link = article.get('link', '')
            if source and link:
                all_sources.add((source, link))

    html += f'''
        <section class="data-source">
            <h3>📚 数据来源声明</h3>
            <p style="color: var(--text-light); margin-bottom: 15px; font-size: 0.9rem;">
                本日报基于 {source_count} 个信息源的实时数据生成，共筛选出投资相关新闻 {sum(len(v) for v in categories.values())} 条。
                所有新闻版权均归原始来源所有，点击链接可直接访问原文。
            </p>
            <div class="source-list">
'''

    for source, link in sorted(all_sources, key=lambda x: x[0])[:50]:  # 最多显示 50 个来源
        html += f'''
                <div class="source-item">
                    <a href="{escape_html(link)}" target="_blank" rel="noopener noreferrer">{escape_html(source)}</a>
                </div>
'''

    html += '''
            </div>
        </section>

        <footer>
            <p>科技投资日报 | 数据驱动的投资决策参考</p>
            <p style="margin-top: 10px; color: var(--text-light);">
                ⚠️ 免责声明：本日报仅供参考，不构成投资建议。投资有风险，决策需谨慎。
            </p>
        </footer>
    </div>
</body>
</html>
'''

    return html

def main():
    """主函数"""
    print("加载文章数据...")
    articles = load_articles(INPUT_JSON)
    print(f"共加载 {len(articles)} 篇文章")

    # 获取元数据
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print("筛选投资相关新闻...")
    investment_articles = filter_investment_articles(articles, min_score=2)
    print(f"筛选出 {len(investment_articles)} 篇投资相关文章")

    print("分类整理文章...")
    categories = categorize_articles(investment_articles)

    print("生成 HTML 报告...")
    html_content = generate_html_report(categories, metadata)

    print(f"保存报告到：{OUTPUT_HTML}")
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("✅ 报告生成完成!")
    print(f"\n各板块文章数量:")
    for name, items in categories.items():
        print(f"  - {name}: {len(items)} 篇")

if __name__ == '__main__':
    main()
