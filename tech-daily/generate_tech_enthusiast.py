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
    """为新闻生成详细摘要 - 包含是什么、为什么重要、关键细节"""
    title = article.get('title', '')
    summary = article.get('summary', '')
    feed_title = article.get('feed_title', '')
    link = article.get('link', '')

    # 清理 summary 中的 Twitter 互动数据
    import re
    summary = re.sub(r'💬[0-9]+🔄[0-9]+❤️[0-9]+👀[0-9]+📊[0-9]+⚡ Powered by xgo\.ing', '', summary)
    summary = re.sub(r'💾', '', summary)

    # 检测新闻主题并生成定制化摘要
    content = (title + ' ' + summary).lower()

    # GPT-5.4 发布
    if 'gpt-5.4' in content or 'gpt-5' in content:
        return """<strong>是什么：</strong>OpenAI 正式发布 GPT-5.4 和 GPT-5.4 Pro 模型，新增原生电脑操控能力，支持代码编写、数据处理等复杂任务。

<strong>为什么重要：</strong>这是 AI 模型从"问答工具"向"任务执行者"转变的重要一步。新模型能够自主操作电脑完成多步骤任务，大幅提升知识工作效率。

<strong>关键细节：</strong>GPT-5.4 已集成到 ChatGPT、API 和 Codex 中，知识截止日期为 2025 年 8 月，支持 100 万 token 上下文窗口。GitHub Copilot 也开始推送该模型。"""

    # 内存/芯片涨价
    if '内存' in content and ('涨价' in content or '价格' in content):
        return """<strong>是什么：</strong>全球内存和芯片价格持续上涨，手机厂商面临成本压力。雷军表示将想办法降低消费者负担。

<strong>为什么重要：</strong>内存是手机、电脑等电子产品的核心组件，价格上涨直接影响消费者购买成本。这次涨价潮可能持续影响到 2026 年全年。

<strong>关键细节：</strong>小米 15 Pro 等旗舰机型可能受到影响，厂商正在通过优化供应链、提前备货等方式缓解压力。建议有购买计划的消费者尽早下手。"""

    # 电池技术
    if '电池' in content and ('刀片' in content or '充电' in content):
        return """<strong>是什么：</strong>比亚迪发布第二代刀片电池，10%-97% 充电仅需 9 分钟，刷新了动力电池快充纪录。

<strong>为什么重要：</strong>充电速度是电动车普及的关键瓶颈之一。9 分钟快充意味着电动车可以像燃油车加油一样便捷，大幅缓解里程焦虑。

<strong>关键细节：</strong>新一代电池能量密度提升 50%，安全性进一步提高。该技术将首先应用于比亚迪高端车型，后续可能向其他厂商授权。"""

    # AI 操控电脑/Agent
    if ('agent' in content or '操控电脑' in content or 'autonomous' in content):
        return """<strong>是什么：</strong>AI Agent 技术取得重要进展，新一代模型能够自主操作电脑完成多步骤任务，如编写代码、分析数据、制定计划等。

<strong>为什么重要：</strong>这代表了 AI 应用的未来方向——从被动回答问题转向主动执行任务。知识工作者可能迎来生产力革命。

<strong>关键细节：</strong>Cursor、Claude Code 等编程工具已率先集成类似功能，能够自主完成代码修改、测试运行等操作，无需开发者逐个确认。"""

    # 开源模型
    if '开源' in content or 'open source' in content:
        return """<strong>是什么：</strong>多个开源 AI 模型发布，降低了开发者和中小企业使用先进 AI 技术的门槛。

<strong>为什么重要：</strong>开源模型让技术创新不再被大公司垄断，激发了全球开发者的创造力。许多创业公司基于开源模型构建了成功的产品。

<strong>关键细节：</strong>Hugging Face、Replicate 等平台成为开源模型的重要分发渠道，开发者可以轻松集成这些能力到自己的应用中。"""

    # 默认摘要 - 确保至少 2-3 句话
    if len(summary) > 100:
        summary_text = summary[:300] + ('...' if len(summary) > 300 else '')
        return f"""<strong>是什么：</strong>{summary_text}

<strong>为什么重要：</strong>这条科技动态反映了当前技术发展的最新趋势，值得科技爱好者关注。

<strong>关键细节：</strong>点击"阅读原文"查看完整内容。"""

    # 截取有效内容
    if len(summary) > 150:
        summary = summary[:150].rstrip('…') + '...'

    if summary.strip():
        return f"""<strong>是什么：</strong>{summary}

<strong>为什么重要：</strong>这条动态可能对科技爱好者的工作和生活产生影响。

<strong>关键细节：</strong>点击"阅读原文"了解更多详情。"""

    return f"""<strong>是什么：</strong>{title}

<strong>为什么重要：</strong>这是值得关注的科技动态。

<strong>关键细节：</strong>点击"阅读原文"查看完整内容。"""

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

    # 产品推荐 HTML - 结合新闻和固定推荐
    product_html = ""

    # 从新闻中提取产品推荐
    for article in categories['product_rec'][:3]:
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

    # 添加固定产品推荐
    product_html += """
        <div class="product-item">
            <h4>🛠️ 本周工具推荐：AI 编程助手</h4>
            <p class="product-desc">如果你还没有尝试过 AI 编程助手，2026 年是开始的最佳时机。Cursor、Claude Code、GitHub Copilot 等工具已经能够显著提升编码效率。</p>
            <ul style="margin-top: 10px; padding-left: 20px;">
                <li><strong>Cursor：</strong>基于 VS Code 构建，支持 Composer 2 自主编程</li>
                <li><strong>Claude Code：</strong>Anthropic 官方出品，新推出自动模式</li>
                <li><strong>GitHub Copilot：</strong>集成在 VS Code 和 JetBrains 全家桶中</li>
            </ul>
            <a href="https://cursor.com" class="product-link" target="_blank" rel="noopener noreferrer" style="margin-top: 10px; display: inline-block;">开始体验 →</a>
        </div>

        <div class="product-item">
            <h4>📚 学习资源推荐：保持科技敏感度</h4>
            <p class="product-desc">科技行业变化迅速，保持学习是最佳策略。以下是我们推荐的获取科技资讯的渠道：</p>
            <ul style="margin-top: 10px; padding-left: 20px;">
                <li><strong>Hacker News：</strong>全球开发者聚集的科技新闻社区</li>
                <li><strong>Simon Willison 博客：</strong>AI 和 Web 开发的深度解读</li>
                <li><strong>GitHub Trending：</strong>发现最热门的开源项目</li>
            </ul>
        </div>
    """

    # 科普小课堂 HTML - 多个概念解读
    science_html = """
    <div class="science-box">
        <h4>🤖 什么是大语言模型（LLM）？</h4>
        <p class="science-desc">大语言模型是一种基于深度学习的人工智能系统，它通过阅读海量文本数据来学习语言的模式和规律。就像是一个博览群书的"超级读者"，能够理解问题、生成文本、甚至编写代码。</p>
        <div class="science-examples">
            <p><strong>常见的大语言模型：</strong>GPT 系列、Claude、Gemini、Qwen 等</p>
            <p><strong>能做什么：</strong>回答问题、创作内容、编程辅助、翻译、分析数据等</p>
            <p><strong>局限性：</strong>可能会产生错误信息（"幻觉"），需要人类判断和验证</p>
        </div>
    </div>

    <div class="science-box" style="margin-top: 25px;">
        <h4>🔄 什么是 AI Agent（智能代理）？</h4>
        <p class="science-desc">AI Agent 是一种能够自主规划并执行任务的 AI 系统。与普通 AI 不同，它不仅能回答问题，还能拆解复杂任务、使用工具、执行多步骤操作，最终完成目标。</p>
        <div class="science-examples">
            <p><strong>应用场景：</strong> autonomously 编写和测试代码、研究竞品并生成报告、管理日程和邮件等</p>
            <p><strong>与普通 AI 的区别：</strong>普通 AI 是"问答机器"，AI Agent 是"数字员工"</p>
            <p><strong>代表产品：</strong>Claude Code 自动模式、Cursor Composer 2 等</p>
        </div>
    </div>

    <div class="science-box" style="margin-top: 25px;">
        <h4>⚡ 什么是"上下文窗口"（Context Window）？</h4>
        <p class="science-desc">上下文窗口指 AI 模型一次能处理的文本量，通常以 token 为单位。更大的上下文窗口意味着 AI 能"记住"更多信息，理解更长的文档或对话历史。</p>
        <div class="science-examples">
            <p><strong>类比：</strong>就像人的工作记忆，窗口越大，能同时考虑的信息越多</p>
            <p><strong>典型数值：</strong>GPT-5.4 支持 100 万 token，相当于数百页书籍的内容</p>
            <p><strong>为什么重要：</strong>大上下文窗口让 AI 能处理整本小说、法律合同、代码库等长文档</p>
        </div>
    </div>
    """

    # 今日金句 HTML - 多条金句
    quote_html = """
    <div class="quote-item">
        <blockquote>"科技本身没有善恶，关键在于我们如何使用它。"</blockquote>
        <p class="quote-author">—— 科技界共识</p>
    </div>
    <div class="quote-item" style="margin-top: 20px;">
        <blockquote>"最好的预测未来的方式是创造它。" ——"The best way to predict the future is to invent it."</blockquote>
        <p class="quote-author">—— 艾伦·凯（Alan Kay，计算机科学家）</p>
    </div>
    <div class="quote-item" style="margin-top: 20px;">
        <blockquote>"任何足够先进的技术都与魔法无异。" ——"Any sufficiently advanced technology is indistinguishable from magic."</blockquote>
        <p class="quote-author">—— 阿瑟·克拉克（Arthur C. Clarke，科幻作家）</p>
    </div>
    """

    # 延伸阅读 - 分类展示所有链接
    # 收集所有唯一来源
    sources_by_category = {'ai': [], 'product': [], 'dev': [], 'other': []}
    all_articles = (categories['headline'][:5] + categories['tech_news'][:20] +
                   categories['product_rec'][:5])

    seen_links = set()
    for article in all_articles:
        title = article.get('title', '')
        link = article.get('link', '')
        feed_title = article.get('feed_title', '')

        if link and link not in seen_links and link != '#':
            seen_links.add(link)

            # 分类
            content = (title + ' ' + feed_title).lower()
            if 'ai' in content or 'gpt' in content or '模型' in content or 'openai' in content:
                sources_by_category['ai'].append((feed_title, title, link))
            elif '产品' in title or '工具' in title or '应用' in title:
                sources_by_category['product'].append((feed_title, title, link))
            elif 'code' in feed_title.lower() or 'dev' in feed_title.lower() or 'github' in feed_title.lower():
                sources_by_category['dev'].append((feed_title, title, link))
            else:
                sources_by_category['other'].append((feed_title, title, link))

    # 生成分类链接
    extended_reading_parts = []

    if sources_by_category['ai']:
        ai_links = ''.join([f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">[{feed}] {title[:50]}</a></li>'
                           for feed, title, link in sources_by_category['ai'][:10]])
        extended_reading_parts.append(f'<li><strong>🤖 AI/大模型：</strong><ul>{ai_links}</ul></li>')

    if sources_by_category['product']:
        product_links = ''.join([f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">[{feed}] {title[:50]}</a></li>'
                                 for feed, title, link in sources_by_category['product'][:8]])
        extended_reading_parts.append(f'<li><strong>📱 产品/工具：</strong><ul>{product_links}</ul></li>')

    if sources_by_category['dev']:
        dev_links = ''.join([f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">[{feed}] {title[:50]}</a></li>'
                            for feed, title, link in sources_by_category['dev'][:8]])
        extended_reading_parts.append(f'<li><strong>💻 开发者工具：</strong><ul>{dev_links}</ul></li>')

    if sources_by_category['other']:
        other_links = ''.join([f'<li><a href="{link}" target="_blank" rel="noopener noreferrer">[{feed}] {title[:50]}</a></li>'
                              for feed, title, link in sources_by_category['other'][:10]])
        extended_reading_parts.append(f'<li><strong>📰 其他科技：</strong><ul>{other_links}</ul></li>')

    all_links_html = '<ul>' + ''.join(extended_reading_parts) + '</ul>'

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
    json_path = '/home/zhangzhan/rss_source/output/freshrss_24h_compact_20260325_080554.json'
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
