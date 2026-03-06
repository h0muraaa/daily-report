#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
科技爱好者版科技日报生成器
根据 RSS 新闻数据生成面向科技爱好者的 HTML 日报
"""

import json
from datetime import datetime
from pathlib import Path

# 读取新闻数据
def load_articles(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('articles', [])

# 筛选科技爱好者感兴趣的新闻
def filter_tech_enthusiast_articles(articles):
    """
    从科技爱好者视角筛选新闻：
    - 通俗科普
    - 生活影响
    - 趣味性
    - 产品创新
    - AI 工具和应用
    """
    filtered = []

    # 关键词匹配（科技爱好者感兴趣的主题）
    tech_keywords = [
        'AI', 'GPT', '模型', '大模型', '生成式', 'gemini', 'claude',
        '产品', '应用', '软件', '工具', '功能', '发布', '上线',
        '电池', '充电', '手机', 'Mac', 'Apple', '内存',
        '机器人', '自动驾驶', '游戏', '视频', '代码', '编程',
        '开源', 'GitHub', 'Cursor', '第三方', '订阅',
        '涨价', '内存', '存储', '屏幕', '显示器',
        '语音', '输入', '翻译', '识别',
    ]

    # 排除关键词（过于专业或无聊的内容）
    exclude_keywords = [
        'status', 'reply', '@', 'follow', 'RT',
        '💬', '🔄', '❤️', '👀', '📊',  # Twitter 互动数据
    ]

    for article in articles:
        title = article.get('title', '')
        summary = article.get('summary', '')
        feed_title = article.get('feed_title', '')
        link = article.get('link', '')

        # 跳过纯 Twitter 互动内容
        if 'status' in link and len(title) < 20:
            continue

        # 检查是否包含科技关键词
        title_lower = title.lower() + summary.lower()
        has_tech_keyword = any(kw.lower() in title_lower for kw in tech_keywords)

        # 排除过于琐碎的内容
        if len(title) < 10 and len(summary) < 30:
            continue

        # 排除纯表情或无意义内容
        if title in ['https://t.co/esoFDuXD70', 'https://t.co/Ha3eaZwg6C']:
            continue

        if has_tech_keyword or feed_title in ['爱范儿', 'The Keyword', 'Simon Willison\'s Weblog',
                                               'GitHub(@github)', 'OpenAI Developers(@OpenAIDevs)',
                                               'Replicate(@replicate)', 'Y Combinator(@ycombinator)']:
            filtered.append(article)

    return filtered

# 生成新闻摘要（2-3 句话）
def generate_summary(article):
    """为新闻生成简洁摘要"""
    title = article.get('title', '')
    summary = article.get('summary', '')

    # 清理 summary 中的 Twitter 互动数据
    import re
    summary = re.sub(r'💬[0-9]+🔄[0-9]+❤️[0-9]+👀[0-9]+📊[0-9]+⚡ Powered by xgo\.ing', '', summary)
    summary = re.sub(r'💾', '', summary)

    # 截取有效内容
    if len(summary) > 200:
        summary = summary[:200].rstrip('…') + '...'

    return summary.strip() if summary.strip() else title

# 判断新闻重要性
def get_importance_level(article):
    """判断新闻的重要程度"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    feed_title = article.get('feed_title', '')

    # 头条级别：重大产品发布、重要更新
    headline_keywords = ['GPT-5.4', 'gpt-5.4', 'OpenAI', '发布', '正式发布', '上线',
                         '头条', '早报', '重磅', '大招']

    if any(kw in title or kw in summary for kw in headline_keywords):
        return 'headline'

    # 重要级别：产品更新、价格变化、新功能
    important_keywords = ['涨价', '降价', '新功能', '更新', '推出', '发布',
                         '电池', '内存', 'Mac', 'iPhone', '手机']

    if any(kw in title for kw in important_keywords):
        return 'important'

    return 'normal'

# 分类新闻
def categorize_articles(articles):
    """将新闻分类到不同板块"""
    categories = {
        'headline': [],      # 今日头条
        'tech_news': [],     # 科技新鲜事
        'product_rec': [],   # 产品推荐
        'science': [],       # 科普小课堂
        'quote': [],         # 今日金句
    }

    for article in articles:
        importance = get_importance_level(article)
        title = article.get('title', '')
        summary = article.get('summary', '')

        if importance == 'headline' and len(categories['headline']) < 5:
            categories['headline'].append(article)
        elif '产品' in title or '应用' in title or '工具' in title or '软件' in title:
            categories['product_rec'].append(article)
        elif any(kw in title for kw in ['是什么', '科普', '解读', '概念', '解释']):
            categories['science'].append(article)
        elif len(title) < 50 and ('quote' in summary.lower() or '说' in summary):
            categories['quote'].append(article)
        else:
            categories['tech_news'].append(article)

    return categories

# 生成 HTML
def generate_html(categories, date_str):
    """生成完整的 HTML 文档"""

    # 今日头条 HTML
    headline_html = ""
    for i, article in enumerate(categories['headline'][:5], 1):
        title = article.get('title', '')
        link = article.get('link', '')
        feed_title = article.get('feed_title', '')
        summary = generate_summary(article)

        headline_html += f'''
        <div class="news-item headline-news">
            <div class="news-number">{i}</div>
            <div class="news-content">
                <h3><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h3>
                <p class="news-summary">{summary}</p>
                <div class="news-meta">
                    <span class="source">来源：{feed_title}</span>
                    <a href="{link}" class="source-link" target="_blank" rel="noopener noreferrer">阅读原文 →</a>
                </div>
            </div>
        </div>
        '''

    # 科技新鲜事 HTML
    tech_news_html = ""
    for article in categories['tech_news'][:15]:
        title = article.get('title', '')
        link = article.get('link', '')
        feed_title = article.get('feed_title', '')
        summary = generate_summary(article)

        # 提取有趣事实
        interesting_point = ""
        if '电池' in title or '充电' in title:
            interesting_point = "💡 有趣事实：现代锂电池技术正在不断突破，充电速度越来越快！"
        elif '内存' in title or '涨价' in title:
            interesting_point = "💡 有趣事实：全球芯片短缺影响了几乎所有电子产品的价格和供应。"
        elif 'AI' in title or 'GPT' in title or '模型' in title:
            interesting_point = "💡 有趣事实：AI 模型正在改变我们工作、学习和创造内容的方式。"
        elif '机器人' in title:
            interesting_point = "💡 有趣事实：机器人技术正从工厂走向家庭，成为日常生活的一部分。"

        tech_news_html += f'''
        <div class="news-item">
            <h4><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h4>
            <p class="news-summary">{summary}</p>
            {f'<p class="interesting-point">{interesting_point}</p>' if interesting_point else ''}
            <div class="news-meta">
                <span class="source">来源：<a href="{link}" target="_blank" rel="noopener noreferrer">{feed_title}</a></span>
            </div>
        </div>
        '''

    # 产品推荐 HTML
    product_html = ""
    for article in categories['product_rec'][:5]:
        title = article.get('title', '')
        link = article.get('link', '')
        feed_title = article.get('feed_title', '')
        summary = generate_summary(article)

        product_html += f'''
        <div class="product-item">
            <h4><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h4>
            <p class="product-desc">{summary}</p>
            <a href="{link}" class="product-link" target="_blank" rel="noopener noreferrer">了解更多 →</a>
        </div>
        '''

    # 如果没有产品推荐，从科技新闻中选取
    if not product_html.strip():
        product_html = """
        <div class="product-item">
            <h4>📱 今日推荐：保持对科技的好奇心</h4>
            <p class="product-desc">科技日新月异，保持学习和探索的热情是最好的"产品"。关注前沿科技动态，尝试新工具，让科技为你的生活增添色彩。</p>
        </div>
        """

    # 科普小课堂 HTML
    science_html = """
    <div class="science-item">
        <h4>🤖 什么是大语言模型（LLM）？</h4>
        <p class="science-desc">大语言模型是一种基于深度学习的人工智能系统，它通过阅读海量文本数据来学习语言的模式和规律。就像是一个博览群书的"超级读者"，能够理解问题、生成文本、甚至编写代码。</p>
        <div class="science-examples">
            <p><strong>常见的大语言模型：</strong>GPT 系列、Claude、Gemini 等</p>
            <p><strong>能做什么：</strong>回答问题、创作内容、编程辅助、翻译、分析数据等</p>
            <p><strong>局限性：</strong>可能会产生错误信息，需要人类判断和验证</p>
        </div>
    </div>
    """

    # 今日金句 HTML
    quote_html = """
    <div class="quote-item">
        <blockquote>"科技本身没有善恶，关键在于我们如何使用它。"</blockquote>
        <p class="quote-author">—— 科技界共识</p>
    </div>
    """

    # 延伸阅读 - 所有链接汇总
    all_links_html = ""
    all_articles = (categories['headline'][:5] + categories['tech_news'][:15] +
                   categories['product_rec'][:5])

    for article in all_articles:
        title = article.get('title', '')
        link = article.get('link', '')
        feed_title = article.get('feed_title', '')

        all_links_html += f'''
        <li><a href="{link}" target="_blank" rel="noopener noreferrer">[{feed_title}] {title}</a></li>
        '''

    # 完整 HTML 模板
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>科技日报 - 科技爱好者版 - {date_str}</title>
    <style>
        :root {{
            --primary-color: #6366f1;
            --secondary-color: #8b5cf6;
            --accent-color: #06b6d4;
            --background: #f8fafc;
            --card-bg: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        .header {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }}

        .header .date {{
            color: var(--text-secondary);
            font-size: 1.1em;
        }}

        .header .emoji {{
            font-size: 3em;
            margin-bottom: 15px;
        }}

        .section {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .section-title {{
            font-size: 1.8em;
            color: var(--text-primary);
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--primary-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .news-item {{
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 12px;
            background: var(--background);
            border-left: 4px solid var(--primary-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .news-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(99, 102, 241, 0.15);
        }}

        .headline-news {{
            border-left-width: 6px;
            border-left-color: var(--warning);
        }}

        .news-number {{
            display: inline-block;
            width: 30px;
            height: 30px;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .news-content h3 {{
            font-size: 1.3em;
            margin-bottom: 10px;
        }}

        .news-content h3 a {{
            color: var(--text-primary);
            text-decoration: none;
            transition: color 0.2s;
        }}

        .news-content h3 a:hover {{
            color: var(--primary-color);
        }}

        .news-summary {{
            color: var(--text-secondary);
            margin-bottom: 15px;
            line-height: 1.8;
        }}

        .news-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: var(--text-secondary);
        }}

        .source-link {{
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }}

        .source-link:hover {{
            text-decoration: underline;
        }}

        .interesting-point {{
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(99, 102, 241, 0.1));
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 0.95em;
            color: var(--text-secondary);
            margin-top: 10px;
        }}

        .product-item {{
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 12px;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.05), rgba(6, 182, 212, 0.05));
            border: 1px solid var(--border-color);
        }}

        .product-item h4 {{
            font-size: 1.2em;
            margin-bottom: 10px;
        }}

        .product-item h4 a {{
            color: var(--text-primary);
            text-decoration: none;
        }}

        .product-item h4 a:hover {{
            color: var(--primary-color);
        }}

        .product-desc {{
            color: var(--text-secondary);
            margin-bottom: 15px;
        }}

        .product-link {{
            display: inline-block;
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 500;
        }}

        .science-item {{
            padding: 25px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
            border-radius: 12px;
            border: 2px dashed var(--primary-color);
        }}

        .science-item h4 {{
            font-size: 1.3em;
            margin-bottom: 15px;
            color: var(--text-primary);
        }}

        .science-desc {{
            color: var(--text-secondary);
            margin-bottom: 15px;
            line-height: 1.8;
        }}

        .science-examples {{
            background: var(--card-bg);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }}

        .science-examples p {{
            margin-bottom: 10px;
            color: var(--text-secondary);
        }}

        .quote-item {{
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
            border-radius: 12px;
        }}

        blockquote {{
            font-size: 1.5em;
            font-style: italic;
            color: var(--text-primary);
            margin-bottom: 15px;
            line-height: 1.6;
        }}

        .quote-author {{
            color: var(--text-secondary);
            font-size: 1em;
        }}

        .links-section {{
            background: var(--card-bg);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .links-section h3 {{
            font-size: 1.5em;
            margin-bottom: 20px;
            color: var(--text-primary);
        }}

        .links-section ul {{
            list-style: none;
        }}

        .links-section li {{
            padding: 10px 0;
            border-bottom: 1px solid var(--border-color);
        }}

        .links-section li:last-child {{
            border-bottom: none;
        }}

        .links-section a {{
            color: var(--primary-color);
            text-decoration: none;
            transition: color 0.2s;
        }}

        .links-section a:hover {{
            color: var(--secondary-color);
            text-decoration: underline;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: rgba(255,255,255,0.9);
            font-size: 0.9em;
        }}

        a {{
            color: var(--primary-color);
            text-decoration: none;
        }}

        @media (max-width: 600px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .section {{
                padding: 20px;
            }}

            .news-meta {{
                flex-direction: column;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="emoji">🚀📱💻</div>
            <h1>科技日报 · 科技爱好者版</h1>
            <p class="date">{date_str}</p>
            <p style="margin-top: 15px; color: var(--text-secondary);">
                用好奇心的眼睛看世界，让科技点亮生活 ✨
            </p>
        </header>

        <!-- 今日头条 -->
        <section class="section">
            <h2 class="section-title">📰 今日头条</h2>
            {headline_html}
        </section>

        <!-- 科技新鲜事 -->
        <section class="section">
            <h2 class="section-title">🔬 科技新鲜事</h2>
            {tech_news_html}
        </section>

        <!-- 产品推荐 -->
        <section class="section">
            <h2 class="section-title">🎁 值得试试</h2>
            {product_html}
        </section>

        <!-- 科普小课堂 -->
        <section class="section">
            <h2 class="section-title">📚 科普小课堂</h2>
            {science_html}
        </section>

        <!-- 今日金句 -->
        <section class="section">
            <h2 class="section-title">💬 今日金句</h2>
            {quote_html}
        </section>

        <!-- 延伸阅读 -->
        <section class="links-section">
            <h3>📖 延伸阅读 | 所有新闻来源</h3>
            <ul>
                {all_links_html}
            </ul>
        </section>

        <footer class="footer">
            <p>Generated with ❤️ by Tech Daily Generator</p>
            <p>科技爱好者版 | 保持好奇 · 探索未知</p>
        </footer>
    </div>
</body>
</html>'''

    return html_template

# 主函数
def main():
    # 配置路径
    json_path = '/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260306_094011.json'
    output_path = '/home/zhangzhan/rss_source/tech-daily-output/tech-daily/tech_enthusiast.html'

    # 确保输出目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # 加载文章
    print(f"正在加载文章数据...")
    articles = load_articles(json_path)
    print(f"共加载 {len(articles)} 篇文章")

    # 筛选文章
    print(f"正在筛选科技爱好者感兴趣的新闻...")
    filtered = filter_tech_enthusiast_articles(articles)
    print(f"筛选后剩余 {len(filtered)} 篇")

    # 分类
    print(f"正在分类文章...")
    categories = categorize_articles(filtered)
    print(f"分类结果：头条 {len(categories['headline'])}, 科技新闻 {len(categories['tech_news'])}, "
          f"产品推荐 {len(categories['product_rec'])}")

    # 生成日期字符串
    date_str = datetime.now().strftime('%Y 年 %m 月 %d 日')

    # 生成 HTML
    print(f"正在生成 HTML 日报...")
    html = generate_html(categories, date_str)

    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n✅ 科技日报已生成：{output_path}")

if __name__ == '__main__':
    main()
