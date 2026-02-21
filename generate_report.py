#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科技日报生成器 - 生成5个版本的日报
"""

import json
import os
from datetime import datetime

# 读取数据源
data_file = "/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260222_070006.json"
output_dir = "/home/zhangzhan/rss_source/tech-daily-output/tech-daily"

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data['articles']
print(f"总文章数: {len(articles)}")

# 为每个版本筛选文章
def filter_articles_for_role(articles, role_keywords, min_count=20):
    """根据角色关键词筛选文章"""
    filtered = []
    for a in articles:
        text = f"{a.get('title', '')} {a.get('summary', '')} {a.get('feed_title', '')}".lower()
        score = sum(1 for kw in role_keywords if kw.lower() in text)
        if score > 0 or len(filtered) < min_count:
            filtered.append(a)
    return filtered[:max(min_count, len(filtered))]

# 定义各角色的关键词
role_keywords = {
    'cto': ['startup', 'ai', 'venture', 'funding', 'series', 'million', 'billion', 'acquisition', 'enterprise', 'strategy', 'trend', 'market', 'growth', 'ycombinator', 'yc'],
    'dev': ['github', 'code', 'api', 'framework', 'library', 'tool', 'vscode', 'python', 'javascript', 'rust', 'go', 'release', 'version', 'developer'],
    'techie': ['product', 'launch', 'review', 'gadget', 'phone', 'laptop', 'app', 'feature', 'update', 'new', 'cool', 'fun'],
    'investor': ['funding', 'valuation', 'ipo', 'acquisition', 'series', 'million', 'billion', 'vc', 'investor', 'market', 'stock', 'crypto', 'bitcoin'],
    'academic': ['paper', 'research', 'arxiv', 'study', 'model', 'llm', 'ai', 'ml', 'dataset', 'benchmark', 'university', 'lab']
}

# 筛选文章
for role, keywords in role_keywords.items():
    filtered = filter_articles_for_role(articles, keywords, 30)
    print(f"{role}: 筛选出 {len(filtered)} 篇文章")

print("\n数据准备完成，可以开始生成HTML")
