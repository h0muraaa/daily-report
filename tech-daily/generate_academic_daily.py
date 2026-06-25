#!/usr/bin/env python3
"""Generate academic research HTML daily report from JSON news data."""

import json
import re
from html import escape
from datetime import datetime

INPUT_PATH = '/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260625_194225.json'
OUTPUT_PATH = '/home/runner/work/daily-report/daily-report/tech-daily/academic_research.html'

with open(INPUT_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

articles = data.get('articles', [])
export_time = data.get('export_time', '')

# --- Helpers ---
def clean_summary(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Your browser does not support the video tag\.', '', text)
    text = re.sub(r'⚡ Powered by xgo\.ing', '', text)
    text = re.sub(r'🔗 View on Twitter', '', text)
    text = re.sub(r'🔗 View Quoted Tweet', '', text)
    text = re.sub(r'[💬🔄❤️👀📊]\d+', '', text)
    return text.strip()

def extract_arxiv_id(link):
    m = re.search(r'arxiv\.org/abs/(\d+\.\d+)', link)
    return m.group(1) if m else None

def deduplicate(articles):
    seen = {}
    result = []
    for a in articles:
        aid = extract_arxiv_id(a.get('link', ''))
        key = aid if aid else re.sub(r'\W+', '', a.get('title', '').lower())
        if key not in seen:
            seen[key] = True
            result.append(a)
    return result

def find_article(pattern, field='both'):
    """Find first article matching regex in title/summary/link."""
    for a in articles:
        text = ''
        if field in ('title', 'both'):
            text += a.get('title', '') + ' '
        if field in ('summary', 'both'):
            text += a.get('summary', '') + ' '
        if field == 'link':
            text = a.get('link', '')
        if re.search(pattern, text, re.IGNORECASE):
            return a
    return None

# --- Selected articles with curated metadata ---
# Research dynamics
research_items = [
    {
        'key': 'agentworld',
        'finder': lambda: find_article(r'Qwen-AgentWorld|原生语言世界模型|AgentWorld'),
        'display_title': 'Qwen-AgentWorld：原生语言世界模型统一模拟七大 Agent 环境',
        'summary': '阿里巴巴 Qwen 团队发布 Qwen-AgentWorld，提出业内首个「原生语言世界模型」（Language World Model）。与将环境模拟依赖外部沙盒不同，该模型把 MCP、Search、Terminal、SWE、Web、OS、Android 七大 Agent 交互领域统一内化到单一架构中，训练目标不是行为策略而是环境状态转移预测。旗舰版 397B-A17B 在自建的 AgentWorldBench 上达到 58.71 分，超过 GPT-5.4 与 Claude Sonnet 4.6；轻量版 35B-A3B 亦有 56.39 分。这项工作为 Sim-to-Real 迁移与可扩展 Agent 训练提供了新的基础模型范式。',
        'tags': ['世界模型', '智能体', '开源'],
    },
    {
        'key': 'ornith',
        'finder': lambda: find_article(r'Ornith-1\.0'),
        'display_title': 'Ornith-1.0：面向 Agentic Coding 的开源模型家族',
        'summary': '社区发布 Ornith-1.0，一个专注 agentic coding 的开源模型家族，覆盖 9B 到 397B MoE 全尺寸。其训练创新在于用强化学习同时优化「任务脚手架」（scaffold）与最终解决方案，使模型学会如何组织执行流程，而不只是生成代码。在 Terminal-Bench、SWE-Bench 等 Agent 编程基准上，Ornith-1.0 达到当前开源模型的顶尖水平，并全系列以 MIT 协议开源，提供 GGUF 版本支持本地部署。',
        'tags': ['Agent Coding', '开源模型', '强化学习'],
    },
    {
        'key': 'sft_eval',
        'finder': lambda: find_article(r'Supervised Fine-Tuning Fails|Loss收敛不等于模型学会了|SFT评估'),
        'display_title': 'SFT 为何失败：ACL 2026 论文提出样本级评估框架',
        'summary': '腾讯混元与 UNSW 合作、入选 ACL 2026 的论文指出，传统 SFT 评估依赖训练 loss、验证 loss 与 benchmark 准确率等聚合指标，存在严重盲区——即使 loss 收敛，模型仍可能对部分样本「欠学习」。研究提出样本级诊断方法，从逐样本角度识别哪些数据未被真正学会，推动 SFT 评估从「平均分时代」进入「精准评估时代」。',
        'tags': ['SFT 评估', 'ACL 2026', '后训练'],
    },
    {
        'key': 'latentmas',
        'finder': lambda: find_article(r'LatentMAS'),
        'display_title': 'LatentMAS：潜空间多智能体协作被 ICML 2026 接收为 Spotlight',
        'summary': 'LatentMAS 将多智能体协作从人类语言空间推进到潜空间（latent space），让智能体在向量层面直接交换信息、推理与协调，避免文本通信的慢速与信息损失。实验表明，这种潜空间协作在多项多智能体任务上取得更高效的协同效果，为构建大规模、低延迟 Agent 系统提供了新思路。',
        'tags': ['多智能体', 'ICML 2026', '潜空间'],
    },
    {
        'key': 'speecheq',
        'finder': lambda: find_article(r'SpeechEQ'),
        'display_title': 'SpeechEQ：面向社交感知语音对话模型的情商商数基准',
        'summary': 'SpeechEQ 提出面向社交感知语音对话模型的「情商商数」基准。与以往仅在孤立文本或被动声学感知上评估机器情感智能不同，该基准考察模型在多轮对话中处理副语言社交线索的跨模态推理能力。随着语音交互系统日益普及，如何在真实对话中理解情绪、语气与社交语境，正成为语音大模型研究的关键瓶颈。',
        'tags': ['语音对话', '情商基准', 'arXiv'],
    },
    {
        'key': 'oracle',
        'finder': lambda: find_article(r'OracleAnalyser|oracle bone'),
        'display_title': 'OracleAnalyser：用多模态大模型分析甲骨文隐含语义',
        'summary': 'OracleAnalyser 提出基于后训练技术的甲骨文分析推理框架。现有甲骨文研究多聚焦于字形识别，而忽略了语义分析。该工作在 Qwen2.5-VL-3B-Instruct 基础上进行多阶段后训练，使多模态大模型能够理解甲骨文的隐含语义。这项工作展示了多模态大模型在数字人文与考古学中的潜在应用，也为低资源古文字研究提供了新工具。',
        'tags': ['多模态', '数字人文', 'arXiv'],
    },
    {
        'key': 'wan_streamer',
        'finder': lambda: find_article(r'Wan-Streamer'),
        'display_title': 'Wan-Streamer：端到端实时交互基础模型',
        'summary': '阿里通义实验室发布 Wan-Streamer v0.1，一个原生流式、端到端交互基础模型，支持低延迟、全双工音视频交互。该模型将语言、音频与视频同时作为输入与输出，在单一 Transformer 中以交错 token 形式进行联合建模，并采用块状因果注意力机制协调多模态生成顺序。这为实时交互式多模态 AI 系统提供了新的架构参考。',
        'tags': ['多模态', '实时交互', '开源'],
    },
]

# Deep dives
deep_dive_items = [
    {
        'key': 'bcoughbench',
        'finder': lambda: find_article(r'BCoughBench'),
        'display_title': 'BCoughBench：可穿戴场景下呼吸声学基础模型的鲁棒性评估',
        'summary': '现有呼吸声学基础模型主要基于智能手机录音评估，但临床部署日益转向通过人体耦合（body-coupled）可穿戴传感器采集信号，这类传感器会因组织与骨骼衰减高频内容。研究提出 BCoughBench，在 9 项分类任务上评估 5 个基础模型，系统刻画了从智能手机到可穿戴设备迁移时的性能变化。其对模型校准、灵敏度与特异度的分析，为医疗声学 AI 从实验室走向真实临床环境提供了重要的评估框架。',
        'tags': ['医疗 AI', '语音基础模型', 'arXiv'],
    },
    {
        'key': 'crossaccent',
        'finder': lambda: find_article(r'CrossAccent-TTS'),
        'display_title': 'CrossAccent-TTS：跨语言口音强度可控文本转语音',
        'summary': '该研究探讨跨语言文本转语音（TTS）中的口音强度可控性问题。现有基于大语言模型的 TTS 系统虽具备较强的跨语言泛化能力，但对口音特征与强度的显式控制有限，尤其对低资源、音系多样的印度语言支持不足。论文提出 CrossAccent-TTS，通过解耦说话人与口音表征，实现跨语言口音强度连续可控。这项工作对多语言语音合成、低资源语言 TTS 以及口音迁移研究均具有参考价值。',
        'tags': ['语音合成', '跨语言', 'arXiv'],
    },
]

# Resources
resource_items = [
    {
        'key': 'foleyset',
        'finder': lambda: find_article(r'FoleySet'),
        'display_title': 'FoleySet：多层级人工标注拟音音效数据集',
        'summary': 'FoleySet 是一个多层级人工标注的拟音（Foley）音效数据集，覆盖脚步声、衣物摩擦、道具操作等与人物动作同步的音效。相较于现有小规模或合成数据集，FoleySet 为影视后期制作中的数据驱动拟音生成、检索与分类任务提供了更可靠的基准。',
        'category': '数据集与基准',
    },
    {
        'key': 'indiccontext',
        'finder': lambda: find_article(r'IndicContextEval'),
        'display_title': 'IndicContextEval：8 种印度语音频 LLM 上下文利用基准',
        'summary': 'IndicContextEval 是一个覆盖 8 种印度语的音频大语言模型上下文利用评估基准。它通过显式上下文输入测试模型是否真正利用提示中的领域描述或实体列表，还是仅依赖预训练中的参数化知识。该基准对多语言语音理解模型的可解释性与鲁棒性评估具有重要意义。',
        'category': '数据集与基准',
    },
    {
        'key': 'steb',
        'finder': lambda: find_article(r'STEB'),
        'display_title': 'STEB：语音到语音翻译表达性评估基准',
        'summary': 'STEB（Speech-to-Speech Translation Expressiveness Benchmark）是一个面向语音到语音翻译表达性的基准，不仅评估翻译保真度，还评估情感、场景风格与非语言发声的保留程度。由于跨语言目标语音难以同时满足翻译忠实与表达对齐，STEB 采用无参考评估框架，推动更自然、更富表现力的语音翻译研究。',
        'category': '数据集与基准',
    },
]

# Resolve all items
for item in research_items + deep_dive_items + resource_items:
    if item.get('article') is None:
        item['article'] = item['finder']()

# Filter out unresolved items
research_items = [i for i in research_items if i['article']]
deep_dive_items = [i for i in deep_dive_items if i['article']]
resource_items = [i for i in resource_items if i['article']]

# --- HTML generation ---

def make_source_link(a, label=None):
    link = a.get('link', '')
    feed = a.get('feed_title', '')
    text = label if label else (feed if feed else '[原文链接]')
    return f'<a href="{escape(link)}" target="_blank" rel="noopener">{escape(text)}</a>'

def render_news_item(item):
    a = item['article']
    title = escape(item['display_title'])
    summary = escape(item['summary'])
    source = make_source_link(a)
    tags_html = ''.join(f'<span class="tag">{escape(t)}</span>' for t in item.get('tags', []))
    return f'''
            <article class="news-item">
                {tags_html}
                <h3>{title}</h3>
                <p>{summary}</p>
                <p class="source">📎 来源：{source}</p>
            </article>
'''

def render_deep_dive(item):
    a = item['article']
    title = escape(item['display_title'])
    summary = escape(item['summary'])
    source = make_source_link(a)
    background = escape(clean_summary(a.get('summary', ''))[:500])
    tags_html = ''.join(f'<span class="tag">{escape(t)}</span>' for t in item.get('tags', []))
    return f'''
            <article class="news-item">
                {tags_html}
                <h3>{title}</h3>
                <div class="abstract-box">
                    <h4>研究背景</h4>
                    <p>{background}</p>
                </div>
                <p><strong>核心创新：</strong> {summary}</p>
                <p class="source">📎 来源：{source}</p>
            </article>
'''

research_html = ''.join(render_news_item(i) for i in research_items)
deep_html = ''.join(render_deep_dive(i) for i in deep_dive_items)

# Resources grouped by category
resources_by_cat = {}
for i in resource_items:
    cat = i.get('category', '其他')
    resources_by_cat.setdefault(cat, []).append(i)

resources_html = ''
for cat, items in resources_by_cat.items():
    resources_html += f'<article class="news-item"><h3>{escape(cat)}</h3><ul class="highlight-list">'
    for i in items:
        a = i['article']
        resources_html += f'<li><strong>{escape(i["display_title"])}</strong>：{escape(i["summary"])} {make_source_link(a)}</li>'
    resources_html += '</ul></article>'

# Add model/tool resources
model_resources = [
    ("Qwen-AgentWorld", "原生语言世界模型，支持七大 Agent 环境模拟，已开源 397B-A17B 与 35B-A3B 版本。", next((i['article'] for i in research_items if i['key']=='agentworld'), None)),
    ("Ornith-1.0", "专注 agentic coding 的开源模型家族，9B 至 397B MoE，MIT 协议。", next((i['article'] for i in research_items if i['key']=='ornith'), None)),
]
model_resources = [(t, s, a) for t, s, a in model_resources if a]
if model_resources:
    resources_html += '<article class="news-item"><h3>开源模型与工具</h3><ul class="highlight-list">'
    for title, summary, a in model_resources:
        resources_html += f'<li><strong>{escape(title)}</strong>：{escape(summary)} {make_source_link(a)}</li>'
    resources_html += '</ul></article>'

# Trends
TRENDS = [
    ("语言世界模型成为 Agent 训练新基建", "Qwen-AgentWorld 与相关研究共同表明：将环境模拟内化为语言模型的核心能力，可能比在真实环境中强化学习更高效、更可扩展。未来 Agent 研究的焦点可能从「策略优化」转向「环境理解深度」，Sim-to-Real 迁移、世界模型与真实环境对齐将成为关键问题。"),
    ("Agent 编程开源生态持续分化模型与脚手架", "Ornith-1.0 将「任务脚手架」纳入强化学习目标，提示 agentic coding 的竞争维度正在从「谁能写出正确代码」扩展到「谁能组织更优执行流程」。开源模型在参数规模、数据配方与脚手架学习上的快速迭代，正在缩小与闭源顶尖模型的差距。"),
    ("语音与大模型融合进入细粒度评估阶段", "SpeechEQ、CrossAccent-TTS、BCoughBench 等工作显示，语音研究正从「能不能听懂/合成」转向「能不能在真实社交/临床/多语言场景中可靠工作」。情商、口音可控性、可穿戴传感器鲁棒性等细粒度问题，将成为下一代语音大模型的核心评估维度。"),
    ("SFT 评估从聚合指标走向样本级诊断", "腾讯混元的工作揭示：训练 loss 与 benchmark 平均分不足以刻画模型真实学习状态。未来后训练研究需要发展更精细的样本级诊断工具，以识别欠学习样本、优化数据配比并提升模型可靠性。"),
]

trends_html = ''
for idx, (title, text) in enumerate(TRENDS, 1):
    trends_html += f'''
            <div class="trend-box">
                <h4>{idx}. {escape(title)}</h4>
                <p>{escape(text)}</p>
            </div>
'''

# References
all_sources = []
for i in research_items + deep_dive_items + resource_items:
    a = i['article']
    all_sources.append((i['display_title'], a.get('feed_title', ''), a.get('link', '')))

references_html = ''
for title, feed, link in sorted(all_sources, key=lambda x: x[0]):
    if feed and link:
        references_html += f'<li>{escape(title)}. <a href="{escape(link)}" target="_blank" rel="noopener">{escape(feed)}</a></li>'

# Date formatting
try:
    dt = datetime.strptime(export_time, '%Y-%m-%d %H:%M:%S')
    date_str = dt.strftime('%Y年%m月%d日')
    date_short = dt.strftime('%Y-%m-%d')
except Exception:
    date_str = '2026年06月25日'
    date_short = '2026-06-25'

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>科技日报 · 学术研究员版 | {date_short}</title>
    <style>
        :root {{
            --primary: #1a365d;
            --secondary: #2c5282;
            --accent: #3182ce;
            --text: #1a202c;
            --muted: #4a5568;
            --light: #f7fafc;
            --border: #e2e8f0;
            --card-bg: #ffffff;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Helvetica Neue", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            line-height: 1.7;
            color: var(--text);
            background: var(--light);
            padding: 0;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 24px;
        }}

        header {{
            border-bottom: 2px solid var(--primary);
            padding-bottom: 24px;
            margin-bottom: 40px;
        }}

        .edition {{
            font-size: 0.85rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 8px;
        }}

        h1 {{
            font-size: 2.2rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
        }}

        .date {{
            color: var(--muted);
            font-size: 0.95rem;
        }}

        h2 {{
            font-size: 1.5rem;
            color: var(--primary);
            margin: 40px 0 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }}

        h3 {{
            font-size: 1.15rem;
            color: var(--secondary);
            margin: 24px 0 12px;
            line-height: 1.4;
        }}

        .news-item {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}

        .news-item p {{
            margin-bottom: 12px;
        }}

        .source {{
            font-size: 0.9rem;
            color: var(--muted);
        }}

        .source a {{
            color: var(--accent);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s;
        }}

        .source a:hover {{
            border-bottom-color: var(--accent);
        }}

        .abstract-box {{
            background: #edf2f7;
            border-left: 4px solid var(--accent);
            padding: 16px 20px;
            margin: 16px 0;
            border-radius: 0 4px 4px 0;
        }}

        .abstract-box h4 {{
            font-size: 0.95rem;
            color: var(--primary);
            margin-bottom: 8px;
        }}

        .abstract-box p {{
            font-size: 0.95rem;
            color: var(--text);
            margin: 0;
        }}

        .highlight-list {{
            list-style: none;
            padding: 0;
        }}

        .highlight-list li {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 10px;
        }}

        .highlight-list li::before {{
            content: "•";
            position: absolute;
            left: 0;
            color: var(--accent);
            font-weight: bold;
        }}

        .trend-box {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 24px;
            margin-bottom: 16px;
        }}

        .trend-box h4 {{
            color: var(--secondary);
            margin-bottom: 10px;
            font-size: 1.05rem;
        }}

        .references {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 24px;
        }}

        .references ol {{
            padding-left: 20px;
        }}

        .references li {{
            margin-bottom: 10px;
            font-size: 0.95rem;
        }}

        .references a {{
            color: var(--accent);
            text-decoration: none;
        }}

        .tag {{
            display: inline-block;
            font-size: 0.75rem;
            padding: 2px 10px;
            border-radius: 12px;
            background: #ebf8ff;
            color: var(--accent);
            margin-right: 8px;
            margin-bottom: 8px;
            font-weight: 500;
        }}

        footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            color: var(--muted);
            font-size: 0.85rem;
            text-align: center;
        }}

        @media (max-width: 640px) {{
            .container {{
                padding: 24px 16px;
            }}
            h1 {{
                font-size: 1.7rem;
            }}
            h2 {{
                font-size: 1.25rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="edition">学术研究员版 · Academic Research Edition</div>
            <h1>科技日报</h1>
            <div class="date">{date_str} | 基于过去 24 小时 FreshRSS 聚合数据</div>
        </header>

        <section>
            <h2>一、研究动态</h2>
            {research_html}
        </section>

        <section>
            <h2>二、深度论文解读</h2>
            {deep_html}
        </section>

        <section>
            <h2>三、开源资源</h2>
            {resources_html}
        </section>

        <section>
            <h2>四、趋势观察</h2>
            {trends_html}
        </section>

        <section class="references">
            <h2>参考文献</h2>
            <ol>
                {references_html}
            </ol>
        </section>

        <footer>
            <p>本日报由 tech-daily-generator 自动生成 · 角色：学术研究员版 · 数据截至 {export_time}</p>
        </footer>
    </div>
</body>
</html>
"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"✅ Generated: {OUTPUT_PATH}")
print(f"   Research articles: {len(research_items)}")
print(f"   Deep dives: {len(deep_dive_items)}")
print(f"   Resources: {len(resource_items) + len(model_resources)}")
print(f"   References: {len(all_sources)}")
for i in research_items + deep_dive_items + resource_items:
    a = i['article']
    print(f"   - {i['display_title']} [{a.get('feed_title', '')}]")
