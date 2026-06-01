#!/usr/bin/env python3
"""
CTO洞察版科技日报生成器
"""

import json
import re
from datetime import datetime

# 读取JSON文件
with open('/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260601_211856.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data['articles']
print(f"总新闻数: {len(articles)}")

# 定义CTO相关的关键词和权重
cto_keywords = {
    # 高权重 - 战略级
    'acquisition': 5, 'merger': 5, 'ipo': 5, 'funding': 5, 'investment': 5,
    '独角兽': 5, '融资': 5, '上市': 5, '并购': 5,
    'strategy': 4, 'infrastructure': 4, 'platform': 4, 'ecosystem': 4,
    '战略': 4, '基础设施': 4, '平台': 4, '生态': 4,
    'open source': 3, '开源': 3,
    'agent': 3, 'agents': 3,
    'llm': 3, '大模型': 3, 'foundation model': 3,
    'data center': 3, 'datacenter': 3, '数据中心': 3,
    'gpu': 3, '算力': 3, 'inference': 3,
    'cloud': 3, '云': 3,
    'organization': 3, 'team': 3, 'talent': 3, 'hiring': 3,
    '组织': 3, '团队': 3, '人才': 3, '招聘': 3,
    'regulation': 3, 'policy': 3, '监管': 3, '政策': 3,
    'competition': 3, 'competitor': 3, '竞争': 3,
    'revenue': 3, 'profit': 3, 'business model': 3,
    '收入': 3, '盈利': 3, '商业模式': 3,
    'security': 3, '安全': 3, 'privacy': 3, '隐私': 3,
}

# 定义高价值来源
high_value_sources = {
    'OpenAI', 'Anthropic', 'Google', 'Microsoft', 'NVIDIA',
    'a16z', 'Sequoia Capital', 'Y Combinator',
    'InfoQ', '创业邦', '极客公园', '量子位',
    'The Cloudflare Blog', 'AWS Architecture Blog',
    'Google Developers Blog', 'Microsoft for Developers',
}

# 定义低价值来源（个人日常分享、纯技术教程等）
low_value_patterns = [
    'experiment', 'vase experiment', 'fun ways',
    'just released', 'tutorial', 'how to',
    'celebrat', 'congrats', 'happy birthday',
    'check out my', 'follow me', 'like and',
]

def score_article(article):
    """给每条新闻打CTO相关度分数"""
    score = 0
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    feed_title = article.get('feed_title', '')
    combined = title + ' ' + summary

    # 关键词匹配
    for keyword, weight in cto_keywords.items():
        if keyword.lower() in combined:
            score += weight

    # 来源加分
    for source in high_value_sources:
        if source.lower() in feed_title.lower():
            score += 2

    # 社交媒体一般性内容减分
    for pattern in low_value_patterns:
        if pattern.lower() in combined:
            score -= 2

    # Twitter/X 短内容通常信息密度低，除非有明确关键词
    if 'x.com' in article.get('link', '') and len(summary) < 150:
        score -= 1

    # 标题为纯URL的减分
    if title.startswith('http') or title.startswith('https://t.co'):
        score -= 3

    # arXiv论文默认分数较低（除非有明确的商业应用关键词）
    if 'arxiv' in feed_title.lower():
        score -= 1

    return score

# 给所有新闻打分
scored_articles = []
for article in articles:
    score = score_article(article)
    scored_articles.append((score, article))

# 按分数排序
scored_articles.sort(key=lambda x: x[0], reverse=True)

# 选择分数最高的新闻
selected = []
seen_titles = set()
for score, article in scored_articles:
    if score <= 0:
        continue
    title = article.get('title', '')
    # 去重
    if title in seen_titles:
        continue
    seen_titles.add(title)
    selected.append({
        'score': score,
        'title': article.get('title', ''),
        'link': article.get('link', ''),
        'feed_title': article.get('feed_title', ''),
        'summary': article.get('summary', ''),
    })

# 取前40条
selected = selected[:40]

print(f"\n筛选出 {len(selected)} 条CTO相关新闻:")
for i, s in enumerate(selected):
    print(f"{i+1}. [{s['score']}] [{s['feed_title']}] {s['title'][:70]}")

# 保存精简数据供后续处理
output = {
    'export_time': data['export_time'],
    'selected_count': len(selected),
    'articles': selected
}

with open('/home/runner/work/daily-report/daily-report/tech-daily/selected_cto.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n已保存到 tech-daily/selected_cto.json")
