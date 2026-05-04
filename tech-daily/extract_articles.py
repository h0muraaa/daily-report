import json

with open('/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260502_183954.json', 'r') as f:
    data = json.load(f)

articles = data['articles']

# Extract key articles for investment analysis
key_titles = [
    'Deepseek V4 May Disrupt',
    'OpenAI Misses Targets',
    'Council Mode for comparing equity research',
    'AI isn\'t the first tech cycle',
    'This is what it looks like when AI meets Wall Street',
    '详解 DeepSeek V4',
    'LABUBU冰箱二手价格',
    'Council Mode',
    '2026 05 02 HackerNews',
    '今天起，ChatGPT合体OpenClaw',
    '这套题，GPT-5.5、Opus 4.7',
    'We created OpenShell',
    'Most teams celebrate',
    'Receptionist robotics',
    '95% sure robotics',
    'Laguna XS',
    'Bring your work into Codex',
    'X 产品负责人 Nikita Bier',
    'Apple 官方APP惊现Claude',
    '为了省 $25',
    'gpt-5.5 和 codex',
    'Our CEO @jerryjliu0',
    'Notice: there\'s a bug',
    'How much compute should we buy',
    'GoFundMe CPTO',
    'Software for Agents',
    'Elon vs. OpenAI Trial',
    'Berkshire is sitting',
    "Meta's DAUs",
    'We made a browser',
    'A lot of work around AI',
    'Elon vs. OpenAI',
    'We\'ll take it',
    'NEW: "-latest" model aliases',
    'Introducing Response Caching',
    'Satya Nadella',
    'meng shao',
    'HackerNews',
    'Tom Huang',
    'NVIDIA AI',
    'Genspark',
    'Marc Andreessen',
    'Palantir',
    'openai 现在的战术',
    '[AINews] AI Engineer',
    'BioMysteryBench',
    'Science Blog',
    'Someone threw a molotov',
    'Aadit Sheth',
    'Palantir paying',
    'Fact: I could be rich',
]

for article in articles:
    title = article.get('title', '')
    for kt in key_titles:
        if kt.lower() in title.lower():
            print(f"\n{'='*60}")
            print(f"Title: {title}")
            print(f"Source: {article.get('feed_title', '')}")
            print(f"Link: {article.get('link', '')}")
            print(f"Summary: {article.get('summary', '')}")
            break
