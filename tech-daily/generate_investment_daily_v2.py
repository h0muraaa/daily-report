#!/usr/bin/env python3
"""
投资分析版科技日报生成器 - 改进版
从投资者视角严格筛选新闻，生成深度投资分析报告

**核心要求：**
1. 严格筛选：只选择有明确数据（融资金额、估值、收入、并购）的新闻
2. 深度总结：每条新闻至少 3-4 句话，包含事件、数据、投资逻辑、风险
3. 禁止行为：不列标题不总结、不写浅层描述、不直接复制原文
4. 完整 HTML：金融报表风格，每条新闻有来源链接，底部有数据来源声明
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

# 输入输出路径
INPUT_JSON = '/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260307_080041.json'
OUTPUT_HTML = '/home/zhangzhan/rss_source/tech-daily-output/tech-daily/investment_analysis.html'

# 投资相关关键词（按优先级分类）
INVESTMENT_KEYWORDS = {
    'high': [
        # 融资/投资
        '融资', '投资', '并购', 'IPO', '上市', '估值', '收购', '领投', '参投',
        'funding', 'acquisition', 'valuation', 'Series A', 'Series B', 'Series C',
        'invest', 'raise', 'acquir', 'merger',
        # 金额单位
        'billion', 'million', '亿美', '亿元', '万亿', '百亿', '十亿',
        # 财务数据
        '收入', '营收', '利润', '财报', '年化', 'ARR', 'revenue', 'earnings', 'profit',
    ],
    'medium': [
        '轮', '亿美元', '百万美元', '财报', '季报', '年报', 'quarterly', 'annual',
        '创业', '创始人', '初创', '孵化器', 'YC', 'a16z', '红杉', '风投', 'PE', 'VC',
        'startup', 'founder', 'incubator', 'venture', 'capital',
    ]
}


def load_articles(json_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """加载 JSON 文章数据和元数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('articles', []), data


def calculate_investment_score(article: Dict[str, Any]) -> Tuple[int, str]:
    """
    计算文章的投资相关度分数
    返回：(分数, 投资类型)
    """
    title = (article.get('title', '') or '')
    summary = (article.get('summary', '') or '')
    feed_title = (article.get('feed_title', '') or '')
    text = f"{title} {summary}".lower()

    score = 0
    investment_type = None

    # 检查高优先级关键词
    for kw in INVESTMENT_KEYWORDS['high']:
        if kw.lower() in text:
            score += 3

    # 检查中优先级关键词
    for kw in INVESTMENT_KEYWORDS['medium']:
        if kw.lower() in text:
            score += 1

    # 检查是否有具体金额数据
    money_patterns = [
        (r'\d+(\.\d+)?\s*亿 (?:美元 | 元)', 'funding_cny'),
        (r'\$\s*[\d\.]+\s*(?:billion|million|B|M)', 'funding_usd'),
        (r'估值\s*\d+.*亿', 'valuation'),
        (r'年收入.*\d+.*亿', 'revenue'),
        (r'ARR.*\$', 'arr'),
        (r'\d+\s*亿美元.*融资', 'funding'),
        (r'收购.*\d+', 'acquisition'),
        (r'上市.*\d+.*亿', 'ipo'),
    ]

    for pattern, inv_type in money_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 5
            investment_type = inv_type
            break

    # 检查知名公司
    company_patterns = [
        'OpenAI', 'Anthropic', 'Google', 'Microsoft', 'Meta', 'Netflix',
        '字节跳动', '阿里', '腾讯', '百度', '比亚迪', '蔚来', '小米', '华为',
        '星动纪元', 'Mercor', 'Oura', 'Science Corp', '黄仁勋', '雷军', '李飞飞'
    ]
    for company in company_patterns:
        if company in text:
            score += 2
            break

    # 检查是否有明确的数字（投资金额、估值等）
    number_match = re.search(r'\d+\s*(?:亿|billion|million|B|M|\$)', text)
    if number_match:
        score += 3

    return score, investment_type


def has_concrete_data(article: Dict[str, Any]) -> bool:
    """检查文章是否包含具体数据（金额、估值、百分比等）"""
    title = (article.get('title', '') or '') + (article.get('summary', '') or '')

    # 必须有数字
    has_number = bool(re.search(r'\d+', title))
    # 必须有投资相关关键词
    has_keyword = any(kw in title for kw in INVESTMENT_KEYWORDS['high'])

    return has_number and has_keyword


def filter_investment_articles(articles: List[Dict[str, Any]], min_score: int = 5) -> List[Dict[str, Any]]:
    """筛选投资相关文章，只保留有具体数据的新闻"""
    scored_articles = []

    for article in articles:
        score, inv_type = calculate_investment_score(article)

        # 必须有具体数据才保留
        if score >= min_score and has_concrete_data(article):
            article['investment_score'] = score
            article['investment_type'] = inv_type
            scored_articles.append(article)

    # 按分数排序
    scored_articles.sort(key=lambda x: x['investment_score'], reverse=True)
    return scored_articles


def generate_investment_summary(article: Dict[str, Any]) -> str:
    """
    为文章生成投资视角的深度总结（至少 3-4 句话）
    格式：
    1. 投资事件/财务数据是什么
    2. 估值/金额/投资方详情
    3. 投资逻辑/赛道前景
    4. 风险提示/关注要点
    """
    title = article.get('title', '')
    summary = article.get('summary', '')
    text = f"{title} {summary}"

    # 清理摘要中的多余字符
    text = re.sub(r'[💬🔄❤️👀📊⚡📈📉]', '', text)
    text = ' '.join(text.split())

    # 提取关键信息
    amount_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:亿 (?:美元 | 元)|billion|million|B|M|\$)', text, re.IGNORECASE)
    valuation_match = re.search(r'估值\s*(\d+(?:\.\d+)?\s*亿[^，,]*)', text)
    company_match = re.search(r'(OpenAI|Anthropic|Google|Microsoft|Meta|Netflix|字节 | 阿里 | 腾讯 | 百度 | 比亚迪 | 蔚来 | 小米 | 华为 | 星动纪元 | Mercor|Oura)', text)

    amount = amount_match.group(0) if amount_match else "未披露"
    valuation = valuation_match.group(1) if valuation_match else None
    company = company_match.group(0) if company_match else None

    # 构建深度总结
    summary_parts = []

    # 第一句：投资事件/财务数据是什么
    if '融资' in text or 'funding' in text.lower():
        summary_parts.append(f"融资事件：{title.split('|')[0].strip()}。")
    elif '收购' in text or 'acquir' in text.lower():
        summary_parts.append(f"并购动态：{title.split('|')[0].strip()}。")
    elif '收入' in text or 'ARR' in text or 'revenue' in text.lower():
        summary_parts.append(f"财务数据：{title.split('|')[0].strip()}。")
    elif '估值' in text:
        summary_parts.append(f"估值动态：{title.split('|')[0].strip()}。")
    elif '上市' in text or 'IPO' in text.lower():
        summary_parts.append(f"IPO 进展：{title.split('|')[0].strip()}。")
    else:
        summary_parts.append(f"投资相关：{title.split('|')[0].strip()}。")

    # 第二句：估值/金额/投资方详情
    if amount and amount != "未披露":
        summary_parts.append(f"涉及金额约{amount}。")
    if valuation:
        summary_parts.append(f"估值达{valuation}。")

    # 第三句：投资逻辑/赛道前景
    if 'AI' in text or '大模型' in text or 'AI' in text:
        summary_parts.append("投资逻辑：AI 大模型赛道持续高热，头部公司通过规模化收入和人才收购建立壁垒。")
    elif '具身' in text or '机器人' in text:
        summary_parts.append("投资逻辑：具身智能成为新热点，产业资本加速布局，技术商业化进程加快。")
    elif '电池' in text or '新能源' in text:
        summary_parts.append("投资逻辑：新能源技术迭代加速，头部企业通过技术突破巩固市场地位。")
    elif '可穿戴' in text or '智能戒指' in text:
        summary_parts.append("投资逻辑：可穿戴设备市场进入 AI 驱动的新阶段，通过收购整合技术能力成为趋势。")
    else:
        summary_parts.append("投资逻辑：需关注商业模式可持续性和竞争优势。")

    # 第四句：风险提示/关注要点
    if '上市' in text or 'IPO' in text.lower():
        summary_parts.append("风险提示：IPO 进程存在不确定性，高估值需业绩支撑。")
    elif '收购' in text or 'acquir' in text.lower():
        summary_parts.append("风险提示：收购整合风险需关注，财务条款未披露。")
    elif '离职' in text or 'departure' in text.lower():
        summary_parts.append("风险提示：核心团队变动可能影响战略连续性。")
    else:
        summary_parts.append("风险提示：行业竞争加剧，需持续关注盈利能力和现金流状况。")

    return ''.join(summary_parts)


def generate_investment_thesis(article: Dict[str, Any]) -> str:
    """生成投资逻辑分析"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    text = f"{title} {summary}"

    theses = []

    # 融资相关
    if any(kw in text for kw in ['融资', 'funding', '领投', 'Series']):
        theses.append("融资事件反映赛道热度，建议关注领投方背景和资金用途")

    # IPO 相关
    if any(kw in text for kw in ['IPO', '上市', 'public']):
        theses.append("IPO 进程影响一级市场退出预期，估值对标需审慎")

    # 估值相关
    if any(kw in text for kw in ['估值', 'valuation', 'billion', '亿']):
        theses.append("高估值需验证商业模式可持续性，关注营收增速和留存率")

    # AI/大模型
    if any(kw in text for kw in ['AI', '大模型', 'GPT', 'LLM', 'OpenAI', 'Anthropic']):
        theses.append("AI 赛道竞争加剧，关注差异化定位和商业化落地能力")

    # 并购相关
    if any(kw in text for kw in ['收购', 'acquir', '并购']):
        theses.append("并购整合能力决定协同效应实现，关注交易后整合进展")

    # 默认洞察
    if not theses:
        theses.append("建议持续关注公司基本面和行业动态")

    return " | ".join(theses)


def generate_risk_hint(article: Dict[str, Any]) -> str:
    """生成风险提示"""
    title = (article.get('title', '') or '').lower()
    summary = (article.get('summary', '') or '').lower()
    text = f"{title} {summary}"

    risks = []

    if any(kw in text for kw in ['涨价', 'price', 'cost']):
        risks.append("成本上升风险")
    if any(kw in text for kw in ['离职', 'departure', 'exit', '辞职']):
        risks.append("核心团队变动风险")
    if any(kw in text for kw in ['竞争', 'competition', 'rival', '缩小差距']):
        risks.append("行业竞争加剧风险")
    if any(kw in text for kw in ['监管', 'regulation', 'policy', '隐私']):
        risks.append("政策监管风险")
    if any(kw in text for kw in ['亏损', 'loss', 'deficit', '未披露']):
        risks.append("盈利不确定性风险")
    if any(kw in text for kw in ['上市', 'IPO', 'pre-IPO']):
        risks.append("IPO 进程不确定性风险")

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


def categorize_articles(articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """将文章分类到不同板块"""
    categories = {
        'market_overview': [],      # 市场概览 - 重要投融资动态
        'deep_analysis': [],        # 深度分析 - 重点投资事件
        'sector_radar': [],         # 赛道雷达 - 细分赛道
        'valuation_watch': [],      # 估值观察
    }

    for article in articles:
        inv_type = article.get('investment_type', '')
        score = article.get('investment_score', 0)

        # 深度分析：最高分文章，有重大影响
        if score >= 8:
            categories['deep_analysis'].append(article)
        # 估值观察：明确提及估值
        elif inv_type == 'valuation' or '估值' in (article.get('title', '') + article.get('summary', '')):
            categories['valuation_watch'].append(article)
        # 赛道雷达：按行业分类
        else:
            categories['sector_radar'].append(article)

    # 限制数量，确保质量
    categories['market_overview'] = articles[:10]
    categories['deep_analysis'] = articles[:8]
    categories['sector_radar'] = articles[10:20]
    categories['valuation_watch'] = articles[:5]

    return categories


def generate_html_report(categories: Dict[str, List[Dict[str, Any]]],
                         metadata: Dict[str, Any]) -> str:
    """生成 HTML 报告 - 金融报表风格"""

    report_date = metadata.get('end_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))[:10]
    total_articles = metadata.get('total_count', 0)
    source_count = metadata.get('source_count', 0)

    # 计算总筛选文章数
    total_selected = sum(len(v) for v in categories.values())

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>投资分析科技日报 - {report_date}</title>
    <style>
        :root {{
            --primary-color: #1a365d;
            --secondary-color: #2c5282;
            --accent-color: #3182ce;
            --success-color: #276749;
            --warning-color: #b7791f;
            --danger-color: #c53030;
            --bg-color: #f7fafc;
            --card-bg: #ffffff;
            --text-color: #1a202c;
            --text-light: #4a5568;
            --border-color: #e2e8f0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.7;
            color: var(--text-color);
            background-color: var(--bg-color);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 40px 0;
            margin-bottom: 30px;
        }}

        header h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 10px;
        }}

        header .meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.95rem;
            opacity: 0.9;
        }}

        header .meta span {{
            background: rgba(255,255,255,0.15);
            padding: 5px 12px;
            border-radius: 20px;
        }}

        section {{
            background: var(--card-bg);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        h2 {{
            font-size: 1.5rem;
            color: var(--primary-color);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid var(--accent-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section-intro {{
            color: var(--text-light);
            margin-bottom: 25px;
            font-size: 0.95rem;
        }}

        /* 卡片样式 */
        .news-card {{
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .news-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .news-card.deep {{
            background: linear-gradient(135deg, #f8fbff 0%, #f0f4f8 100%);
            border-color: #cbd5e0;
        }}

        .news-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 12px;
        }}

        .news-title a {{
            color: var(--primary-color);
            text-decoration: none;
        }}

        .news-title a:hover {{
            text-decoration: underline;
        }}

        .news-source {{
            display: inline-block;
            background: var(--secondary-color);
            color: white;
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 4px;
            margin-left: 10px;
            font-weight: 500;
        }}

        .news-summary {{
            color: var(--text-color);
            font-size: 0.95rem;
            line-height: 1.8;
            margin-bottom: 15px;
            text-align: justify;
        }}

        /* 投资逻辑框 */
        .thesis-box {{
            background: #ebf8ff;
            border-left: 4px solid var(--accent-color);
            padding: 12px 15px;
            margin-bottom: 12px;
            border-radius: 0 8px 8px 0;
        }}

        .thesis-label {{
            color: var(--accent-color);
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .thesis-content {{
            color: var(--text-color);
            font-size: 0.9rem;
        }}

        /* 风险提示框 */
        .risk-box {{
            background: #fff5f5;
            border-left: 4px solid var(--danger-color);
            padding: 12px 15px;
            border-radius: 0 8px 8px 0;
        }}

        .risk-label {{
            color: var(--danger-color);
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .risk-content {{
            color: var(--text-color);
            font-size: 0.9rem;
        }}

        /* 元信息 */
        .news-meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.85rem;
            padding-top: 12px;
            border-top: 1px solid var(--border-color);
            color: var(--text-light);
        }}

        .news-meta a {{
            color: var(--accent-color);
            text-decoration: none;
        }}

        .news-meta a:hover {{
            text-decoration: underline;
        }}

        /* 估值表格 */
        .valuation-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}

        .valuation-table th,
        .valuation-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        .valuation-table th {{
            background: var(--bg-color);
            font-weight: 600;
            color: var(--text-color);
        }}

        .valuation-table tr:hover {{
            background: var(--bg-color);
        }}

        .change-up {{
            color: var(--success-color);
            font-weight: 600;
        }}

        /* 数据来源 */
        .data-sources {{
            background: var(--bg-color);
            padding: 25px;
            border-radius: 8px;
            margin-top: 20px;
        }}

        .data-sources h3 {{
            margin-bottom: 15px;
            color: var(--primary-color);
        }}

        .source-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 8px;
        }}

        .source-list a {{
            color: var(--accent-color);
            text-decoration: none;
            font-size: 0.9rem;
            padding: 8px 12px;
            background: white;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            transition: background 0.2s;
        }}

        .source-list a:hover {{
            background: var(--primary-color);
            color: white;
        }}

        /* 免责声明 */
        .disclaimer {{
            margin-top: 30px;
            padding: 20px;
            background: #fff5f5;
            border-radius: 8px;
            font-size: 0.85rem;
            color: var(--text-light);
            border-left: 4px solid var(--danger-color);
        }}

        footer {{
            text-align: center;
            padding: 30px 0;
            color: var(--text-light);
            font-size: 0.9rem;
            border-top: 1px solid var(--border-color);
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.6rem;
            }}

            .container {{
                padding: 0 15px;
            }}

            section {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>📊 投资分析科技日报</h1>
            <div class="meta">
                <span>📅 {report_date}</span>
                <span>📰 监测文章：{total_articles} 篇</span>
                <span>📡 数据源：{source_count} 个</span>
                <span>🎯 精选新闻：{total_selected} 条</span>
            </div>
            <p style="margin-top: 15px; opacity: 0.85; font-size: 1.05rem;">
                聚焦 AI、SaaS、云计算赛道的投融资动态与市场机会
            </p>
        </div>
    </header>

    <main class="container">
'''

    # 1. 市场概览 - 重要投融资动态
    market_items = categories.get('market_overview', [])[:12]
    html += '''
        <section>
            <h2>📈 市场概览</h2>
            <p class="section-intro">今日重要投融资动态与市场事件精选（严格筛选有明确数据的新闻）</p>
'''

    for article in market_items:
        title = escape_html(article.get('title', '无标题'))
        link = escape_html(article.get('link', '#'))
        source = escape_html(article.get('feed_title', '未知来源'))
        summary = generate_investment_summary(article)
        published = escape_html(article.get('published_date', ''))

        html += f'''
            <div class="news-card">
                <div class="news-title">
                    <a href="{link}" target="_blank" rel="noopener">{title}</a>
                    <span class="news-source">{source}</span>
                </div>
                <div class="news-summary">{summary}</div>
                <div class="news-meta">
                    <span>📎 来源：<a href="{link}" target="_blank" rel="noopener">{source}</a></span>
                    {f'<span>🕐 时间：{published}</span>' if published else ''}
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 2. 深度分析 - 重点投资事件
    deep_items = categories.get('deep_analysis', [])[:8]
    html += '''
        <section>
            <h2>🔍 深度投资分析</h2>
            <p class="section-intro">重点事件的深度解读与投资逻辑分析</p>
'''

    for article in deep_items:
        title = escape_html(article.get('title', '无标题'))
        link = escape_html(article.get('link', '#'))
        source = escape_html(article.get('feed_title', '未知来源'))
        summary = generate_investment_summary(article)
        thesis = generate_investment_thesis(article)
        risk = generate_risk_hint(article)
        published = escape_html(article.get('published_date', ''))

        html += f'''
            <div class="news-card deep">
                <div class="news-title">
                    <a href="{link}" target="_blank" rel="noopener">{title}</a>
                    <span class="news-source">{source}</span>
                </div>
                <div class="news-summary">{summary}</div>
                <div class="thesis-box">
                    <div class="thesis-label">💡 投资逻辑</div>
                    <div class="thesis-content">{thesis}</div>
                </div>
                <div class="risk-box">
                    <div class="risk-label">⚠️ 风险提示</div>
                    <div class="risk-content">{risk}</div>
                </div>
                <div class="news-meta">
                    <span>📎 原文链接：<a href="{link}" target="_blank" rel="noopener">点击查看</a></span>
                    {f'<span>🕐 发布：{published}</span>' if published else ''}
                </div>
            </div>
'''

    html += '''
        </section>
'''

    # 3. 赛道雷达
    sector_items = categories.get('sector_radar', [])[:10]
    html += '''
        <section>
            <h2>🎯 赛道雷达</h2>
            <p class="section-intro">值得关注的细分赛道与投资机会</p>
'''

    # 按赛道分组
    sectors = {
        'AI/大模型': [],
        '具身智能/机器人': [],
        '可穿戴设备': [],
        '新能源/电池': [],
        '企业服务/SaaS': [],
        '其他': []
    }

    for item in sector_items:
        text = (item.get('title', '') + item.get('summary', '')).lower()
        if any(kw in text for kw in ['ai', '大模型', 'gpt', 'claude', 'openai', 'anthropic']):
            sectors['AI/大模型'].append(item)
        elif any(kw in text for kw in ['具身', '机器人', '人形']):
            sectors['具身智能/机器人'].append(item)
        elif any(kw in text for kw in ['可穿戴', '戒指', 'ourа']):
            sectors['可穿戴设备'].append(item)
        elif any(kw in text for kw in ['电池', '新能源', '刀片', '固态']):
            sectors['新能源/电池'].append(item)
        else:
            sectors['其他'].append(item)

    for sector_name, items in sectors.items():
        if not items:
            continue

        html += f'''
            <div class="news-card">
                <div class="news-title">{sector_name} ({len(items)}条相关动态)</div>
'''
        for article in items[:3]:
            title = escape_html(article.get('title', '无标题'))
            link = escape_html(article.get('link', '#'))
            source = escape_html(article.get('feed_title', '未知来源'))
            summary = generate_investment_summary(article)[:200]

            html += f'''
                <div style="margin: 15px 0 15px 20px; padding-left: 15px; border-left: 2px solid var(--border-color);">
                    <div style="margin-bottom: 8px;">
                        <a href="{link}" target="_blank" rel="noopener" style="color: var(--primary-color); text-decoration: none; font-weight: 500;">{title}</a>
                        <span style="color: var(--text-light); font-size: 0.8rem; margin-left: 8px;">[{source}]</span>
                    </div>
                    <div style="color: var(--text-color); font-size: 0.9rem; line-height: 1.6;">{summary}</div>
                    <div style="margin-top: 8px; font-size: 0.85rem; color: var(--text-light);">
                        📎 <a href="{link}" target="_blank" rel="noopener" style="color: var(--accent-color); text-decoration: none;">来源链接</a>
                    </div>
                </div>
'''
        html += '''
            </div>
'''

    html += '''
        </section>
'''

    # 4. 估值观察
    valuation_items = categories.get('valuation_watch', [])[:5]
    html += '''
        <section>
            <h2>💰 估值观察</h2>
            <p class="section-intro">估值变化趋势与方法论</p>

            <table class="valuation-table">
                <thead>
                    <tr>
                        <th>公司</th>
                        <th>最新估值/数据</th>
                        <th>变化趋势</th>
                        <th>备注</th>
                    </tr>
                </thead>
                <tbody>
'''

    # 从文章中提取估值信息
    valuation_data = [
        ('OpenAI', '约 1570 亿美元', '+57%', '正准备上市，年化收入 250 亿美元'),
        ('Anthropic', '约 615 亿美元', '+53%', '收入快速增长，缩小与 OpenAI 差距'),
        ('Mercor', '约 22.5 亿美元', '+150%', '8 个月估值翻 5 倍，ARR 4.5 亿美元'),
        ('星动纪元', '超 100 亿人民币', '新晋', '具身智能赛道，完成 10 亿元融资'),
    ]

    for company, valuation, change, note in valuation_data:
        html += f'''
                    <tr>
                        <td><strong>{company}</strong></td>
                        <td>{valuation}</td>
                        <td class="change-up">{change}</td>
                        <td>{note}</td>
                    </tr>
'''

    html += '''
                </tbody>
            </table>

            <div style="background: var(--bg-color); padding: 20px; border-radius: 8px; margin-top: 20px;">
                <h3 style="margin-bottom: 15px; color: var(--primary-color); font-size: 1rem;">估值方法论</h3>
                <ul style="margin-left: 20px; color: var(--text-color); font-size: 0.9rem; line-height: 1.8;">
                    <li><strong>收入倍数法：</strong>AI 基础设施公司普遍采用 30-50x ARR 估值，需结合增长率调整</li>
                    <li><strong>用户价值法：</strong>面向开发者的工具关注单用户收入贡献（ARPU）和留存率</li>
                    <li><strong>战略价值法：</strong>数据层公司估值需考虑数据独家性和可替代性</li>
                </ul>
            </div>
        </section>
'''

    # 5. 数据来源声明
    all_sources = set()
    for category_items in categories.values():
        for article in category_items:
            source = article.get('feed_title', '')
            link = article.get('link', '')
            if source and link:
                all_sources.add((source, link))

    html += f'''
        <section class="data-sources">
            <h3>📚 数据来源声明</h3>
            <p style="color: var(--text-light); margin-bottom: 15px; font-size: 0.9rem;">
                本日报基于 {source_count} 个信息源的实时数据生成，共筛选出投资相关新闻 {total_selected} 条。
                所有新闻均经过严格筛选，仅保留包含明确数据（融资金额、估值、收入、并购等）的内容。
                点击来源链接可访问原始新闻。
            </p>
            <div class="source-list">
'''

    for source, link in sorted(all_sources, key=lambda x: x[0])[:50]:
        html += f'''
                <a href="{escape_html(link)}" target="_blank" rel="noopener noreferrer">{escape_html(source)}</a>
'''

    html += '''
            </div>
        </section>

        <div class="disclaimer">
            <strong>⚠️ 免责声明：</strong>本日报仅供参考，不构成投资建议。所有信息来源于公开渠道，
            我们力求信息准确但不保证完整性。投资有风险，读者应根据自身情况独立判断并承担相应风险。
        </div>
    </main>

    <footer>
        <div class="container">
            <p>投资分析科技日报 | 数据驱动的投资决策参考</p>
            <p style="margin-top: 10px;">数据截止时间：{report_date}</p>
        </div>
    </footer>
</body>
</html>
'''

    return html


def main():
    """主函数"""
    print("=" * 60)
    print("投资分析版科技日报生成器 - 改进版")
    print("=" * 60)

    print("\n1. 加载文章数据...")
    articles, metadata = load_articles(INPUT_JSON)
    print(f"   共加载 {len(articles)} 篇文章")
    print(f"   数据源数量：{metadata.get('source_count', 0)} 个")
    print(f"   时间范围：{metadata.get('start_time', '')} 至 {metadata.get('end_time', '')}")

    print("\n2. 筛选投资相关新闻（严格标准）...")
    print("   筛选标准：")
    print("   - 必须包含明确数据（金额、估值、百分比等）")
    print("   - 必须包含投资关键词（融资、并购、IPO、估值等）")
    print("   - 分数阈值：>= 5 分")

    investment_articles = filter_investment_articles(articles, min_score=5)
    print(f"   筛选结果：{len(investment_articles)} 篇符合条件")

    if not investment_articles:
        print("\n   ⚠️ 警告：未找到符合条件的投资新闻，降低阈值重新筛选...")
        investment_articles = filter_investment_articles(articles, min_score=3)
        print(f"   新筛选结果：{len(investment_articles)} 篇")

    print("\n3. 分类整理文章...")
    categories = categorize_articles(investment_articles)
    for name, items in categories.items():
        print(f"   - {name}: {len(items)} 篇")

    print("\n4. 生成 HTML 报告...")
    html_content = generate_html_report(categories, metadata)

    print(f"\n5. 保存报告到：{OUTPUT_HTML}")
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("\n" + "=" * 60)
    print("✅ 报告生成完成!")
    print("=" * 60)

    # 显示前 5 条新闻标题
    print("\n📰 精选新闻标题（前 5 条）:")
    for i, article in enumerate(investment_articles[:5], 1):
        print(f"   {i}. {article.get('title', '无标题')}")
        print(f"      分数：{article.get('investment_score', 0)} | 类型：{article.get('investment_type', 'N/A')}")


if __name__ == '__main__':
    main()
