import json

with open('/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260502_183954.json', 'r') as f:
    data = json.load(f)

articles = data['articles']
print(f"Total articles: {len(articles)}")

# Keywords for investment analysis
investment_keywords = [
    'fund', 'funding', 'raise', 'raised', 'series', 'valuation', 'valued',
    'invest', 'investment', 'investor', 'vc', 'venture', 'capital',
    'ipo', 'acquisition', 'acquire', 'acquired', 'merger', 'bought',
    'revenue', 'profit', 'earnings', 'stock', 'market', 'economy',
    'financ', 'million', 'billion', 'unicorn', 'startup', 'start-up',
    'strategic', 'business model', 'pricing', 'cost', 'expense',
    'sales', 'growth', 'scale', 'scaling', 'runway',
    'deepseek', 'openai', 'anthropic', 'claude', 'gpt', 'agent',
    'compute', 'gpu', 'cloud', 'saas', 'platform'
]

# High-value sources
high_value_sources = [
    'Y Combinator', 'Sequoia', 'a16z', 'Accel', 'Benchmark',
    'TechCrunch', 'The Information', 'Bloomberg', 'Reuters',
    'CNBC', 'Wall Street Journal', 'Financial Times',
    'OpenAI', 'Anthropic', 'Google', 'Microsoft', 'Meta',
    'NVIDIA', 'Apple'
]

scored_articles = []
for article in articles:
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    feed_title = article.get('feed_title', '').lower()
    text = title + ' ' + summary

    score = 0
    for kw in investment_keywords:
        if kw in text:
            score += 1
    for src in high_value_sources:
        if src.lower() in feed_title:
            score += 2

    if score > 0:
        scored_articles.append((score, article))

scored_articles.sort(key=lambda x: x[0], reverse=True)

# Print top 50 scored articles
for score, article in scored_articles[:60]:
    print(f"\n--- Score: {score} ---")
    print(f"Title: {article['title']}")
    print(f"Source: {article['feed_title']}")
    print(f"Summary: {article['summary'][:300]}...")
    print(f"Link: {article['link']}")
