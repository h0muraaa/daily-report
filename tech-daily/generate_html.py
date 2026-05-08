#!/usr/bin/env python3
"""Generate developer practice HTML daily report from JSON news data."""

import json
import re
from datetime import datetime
from html import escape

# Read JSON
with open("./tech-daily/freshrss_24h_compact_20260508_190119.json", "r", encoding="utf-8") as f:
    data = json.load(f)

articles = data.get("articles", [])
export_time = data.get("export_time", "")

# Target articles by title patterns
TARGET_PATTERNS = [
    ("Gemini CLI DevOps", "gemini.*cli.*devops|ship code within minutes"),
    ("Sparse Transformer Kernels", "sparse transformer kernels|sakana.*nvidia"),
    ("Transformers Ate Vision", "transformers.*ate vision|transformer.*vision"),
    ("GitHub Agentic Workflows", "github.*agentic|securing.*agentic"),
    ("GKE Cold Start", "faster node startup|cold-start.*gke"),
    ("Perplexity CUTLASS", "perplexity.*nvidia|cutlass"),
    ("CVE Smart TV", "cve-2012-5958|bug.*2013.*tv|crashed my tv"),
    ("Stripe SaaS Payment", "stripe.*webhooks|saas.*payment.*stripe"),
    ("LangSmith MCP", "langsmith.*mcp server"),
    ("Douyin Performance", "抖音动态体验|douyin.*optimization"),
    ("GitHub Stacked PR", "github.*大 pr|gh-stack|stacked.*pull"),
    ("China AI Labs", "中国.*实验室|deepseek.*字节|chinese ai labs"),
    ("AI Coding Cost", "coding.*expensive|open models.*cheaper"),
    ("Multi-Agent Architecture", "multi-agent.*architecture.*ships|multi-agent.*coding"),
    ("GitHub Innovation Graph", "github.*innovation graph|digital core"),
    ("Gemma Multi-token", "multi-token.*gemma|gemma 4.*faster"),
    ("Age Assurance Laws", "age assurance.*developers"),
    ("Ernie 5.1", "ernie-5.1|ernie.*search arena"),
    ("Anthropic Hidden Motives", "隐藏动机|hidden motive.*anthropic"),
    ("Qdrant Vector DB", "qdrant.*stackoverflow|vector.*database"),
    ("Ardent Postgres Clone", "ardent.*postgres|clone.*postgres.*6s"),
    ("Vibe Debugger", "vibe debugger|debugger.*agent"),
    ("CyberSecQwen", "cybersecqwen|defensive cyber"),
    ("NVIDIA DeepStream", "deepstream.*vision|nvidia.*vision ai app"),
]

def find_articles(pattern):
    results = []
    for a in articles:
        text = (a.get("title", "") + " " + a.get("summary", "")).lower()
        if re.search(pattern.lower(), text):
            results.append(a)
    return results

# Collect target articles
categorized = {}
for name, pattern in TARGET_PATTERNS:
    matches = find_articles(pattern)
    if matches:
        categorized[name] = matches[0]
        print(f"Found: {name} -> {matches[0].get('title', '')[:60]}")

# Also find any other dev-relevant articles we might have missed
DEV_KEYWORDS = ["open source", "benchmark", "kernel", "deployment", "architecture",
                "testing", "profiling", "memory leak", "concurrency", "async"]

# Build the HTML
DATE_STR = "2026-05-08"
DAY_STR = "周五"

def clean_summary(text):
    """Clean up summary text - remove Twitter engagement metrics and other noise."""
    # Remove Twitter/X engagement metrics
    text = re.sub(r'💬\d+🔄\d+❤️\d+👀\d+📊\d+', '', text)
    text = re.sub(r'⚡ Powered by xgo\.ing', '', text)
    text = re.sub(r'🔗 View on Twitter', '', text)
    text = re.sub(r'🔗 View Quoted Tweet', '', text)
    text = re.sub(r'Your browser does not support the video tag\.', '', text)
    # Clean up extra whitespace
    text = ' '.join(text.split())
    return text.strip()

def make_source_link(article):
    """Generate source HTML for an article."""
    link = article.get("link", "")
    feed = article.get("feed_title", "")
    if link and feed:
        return f'<a href="{escape(link)}" target="_blank" rel="noopener">[来源: {escape(feed)}]</a>'
    elif link:
        return f'<a href="{escape(link)}" target="_blank" rel="noopener">[原文链接]</a>'
    return ""

def extract_summary_for_article(name, article):
    """Generate a developer-focused summary for an article."""
    title = article.get("title", "")
    summary = clean_summary(article.get("summary", ""))
    feed = article.get("feed_title", "")

    summaries = {
        "Gemini CLI DevOps": """Google Cloud 发布了 Gemini CLI DevOps 扩展，旨在弥合"内循环"（本地编码测试）与"外循环"（容器化、CI/CD、生产部署）之间的鸿沟。该扩展可以从单终端界面同时处理快速部署和完整流水线生成，让开发者能将 AI 生成的代码在几分钟内部署到生产环境，而不必再花一个下午折腾 Dockerfile、IAM 绑定和 YAML 配置。这对使用 Claude Code、Antigravity 等 AI 编码工具的开发者尤为重要——解决了"应用只存在于笔记本上"的尴尬局面。""",

        "Sparse Transformer Kernels": """NVIDIA 与 Sakana AI Labs 合作在 ICML 2026 发表了一项关于稀疏 Transformer 内核与格式优化的研究。核心创新包括 TwELL 稀疏打包格式、融合 CUDA 内核，以及针对现代 NVIDIA GPU 执行优化的稀疏格式。实验表明，在大规模推理和训练场景下可实现 20% 以上的加速。这是一个非常有价值的突破：现代 LLM 的 feedforward 层中超过 95% 的神经元在任何给定 token 下都处于静默状态，但硬件惩罚了这种稀疏性。该研究通过结构化稀疏性和优化的内存访问模式，让 GPU 能够高效利用这种"天生稀疏"的特性。""",

        "Transformers Ate Vision": """Isaac Robinson（Roboflow）的演讲深入解析了 Transformer 如何在视觉领域击败 CNN。关键答案在于预训练、规模化、从 LLM 世界借鉴的基础设施，以及"最能规模化的简单架构终将获胜"这一长期趋势。演讲梳理了从 ViT、Swin 到 ConvNeXt、Hiera、SAM 和 RF-DETR 的演进脉络，分析了让 Transformer 视觉系统真正实用的因素，以及部署灵活性如今为何与基准测试成绩同等重要。对于正在构建或部署视觉 AI 应用的开发者，理解这些权衡至关重要。""",

        "GitHub Agentic Workflows": """GitHub 详细阐述了 CI/CD 流水线中 agentic 工作流的纵深防御安全架构，核心聚焦于隔离策略、权限最小化和供应链攻击防护。随着 AI 编码代理（如 Codex、Claude Code）越来越多地直接操作代码仓库、创建 PR、运行测试和部署，传统 CI/CD 的安全模型面临新的挑战。GitHub 的方案包括沙箱化 agent 执行环境、细粒度权限令牌、行为审计和异常检测。对于已经在使用或计划引入 AI 编码代理的团队，这篇文章提供了实施安全策略的实用指南。""",

        "GKE Cold Start": """Google Kubernetes Engine (GKE) 推出了一项重大更新，显著缩短了节点冷启动时间。此前，当需要扩容新 Pod 时，节点启动的延迟往往成为性能瓶颈——尤其是在 serverless 或自动扩缩容场景下。GKE 团队通过优化节点镜像加载、并行化初始化步骤和预配置常用运行时组件，将节点从创建到可调度状态的时间大幅缩短。对于依赖 Kubernetes 弹性伸缩的应用，这意味着更快的故障恢复、更敏捷的负载响应，以及更好的用户体验。""",

        "Perplexity CUTLASS": """Perplexity 团队分享了他们使用 NVIDIA CUTLASS Python 技术栈优化推理性能的实践经验。CUTLASS 是 NVIDIA 提供的高性能 CUDA C++ 模板库，用于实现 GPU 上的密集线性代数运算。Perplexity 通过将部分核心计算迁移到 CUTLASS Python 接口，并配合定制的内核融合策略，在保持模型精度的同时显著降低了推理延迟。这篇文章详细拆解了优化过程、遇到的陷阱以及性能对比数据，对任何需要在 NVIDIA GPU 上榨取极致推理性能的开发者都有参考价值。""",

        "CVE Smart TV": """一位安全研究者展示了如何利用 2012 年发现的 CVE-2012-5958（libupnp 库中的缓冲区溢出漏洞），通过发送单个特制网络包远程崩溃智能电视。这个漏洞存在于 2014 年前后出厂的几乎所有智能电视中。研究者首先让 Claude 思考 2014 年 Linux 设备常见的漏洞，然后逐一测试（包括 Heartbleed），最终定位到这个 13 年前的老漏洞。这个案例对开发者有多重启示：一是 IoT 设备的固件更新周期极长，已知漏洞可能长期存在；二是 AI 辅助安全测试正在降低漏洞挖掘的门槛；三是"仅暴露在内网"并非安全假设，内网横向移动是常见攻击路径。""",

        "Stripe SaaS Payment": """freeCodeCamp 发布了一份完整的 Stripe 支付流程教程，覆盖了从结账页面到支付完成后的 Webhook 处理和邮件通知的完整链路。大多数 Stripe 教程在"用户点击支付"后就结束了，但这篇文章继续深入：如何处理支付成功/失败的 Webhook 事件、如何设计幂等的支付状态机、如何在数据库中安全记录交易、以及如何发送定制化的支付确认邮件。对于正在构建 SaaS 产品的开发者，这是一份可直接落地的实施指南，涵盖了生产环境必须考虑的边缘情况和错误处理。""",

        "LangSmith MCP": """LangSmith 现在可以作为远程 MCP（Model Context Protocol）服务器使用。开发者只需将任何支持 MCP 的客户端指向 LangSmith，用账户登录后，AI 助手就能直接访问：Traces（追踪记录）、Projects（项目）、Datasets（数据集）、Prompts（提示词）和 Billing（账单信息）。不需要本地服务器或 API 密钥。这是 MCP 生态的重要扩展——将 LLM 应用的可观测性平台与 IDE 中的 AI 助手打通，意味着开发者可以直接在编码环境中查询生产环境的追踪数据、分析 Prompt 效果，甚至基于数据集进行迭代优化。""",

        "Douyin Performance": """字节跳动技术团队分享了抖音 App 动态体验优化的实践经验。随着业务从核心短视频扩展到直播、电商、本地生活等多元场景，设备端需要同时承载高性能渲染、低延迟推流、多线程预加载等高负载任务。文章详细讨论了在复杂场景下保持流畅体验的技术挑战和解决方案，包括渲染管线优化、内存管理策略、预加载机制，以及针对不同设备等级的降级策略。对于移动端开发者，尤其是需要处理复杂 UI 和多媒体场景的工程师，这些来自亿级 DAU 产品的经验极具参考价值。""",

        "GitHub Stacked PR": """GitHub 正式推出了名为 gh-stack 的 CLI 扩展，原生支持堆叠式 Pull Request 工作流。长期以来，大型功能拆分后的多个依赖 PR 管理一直是 GitHub 的痛点，开发者不得不依赖第三方工具（如 Graphite、Spr）来弥补。gh-stack 允许开发者将一系列有依赖关系的 PR 作为一个"栈"来管理——创建、更新、审查和合并都可以在整个栈的上下文中进行。这显著降低了"大 PR 地狱"的协作成本，对于在大型代码库中工作的团队来说是一个重要的工作流改进。""",

        "China AI Labs": """美国 AI 研究员 Nathan Lambert 撰写了一份关于中国 AI 生态的观察笔记，在英文技术圈引发了广泛讨论。文章指出，中国实验室普遍"忌惮字节跳动、尊重 DeepSeek"——前者因其庞大的数据和应用场景优势，后者因其极致的工程效率和创新突破。Lambert 分析了中国 AI 发展的独特路径：更强调模型与应用场景的紧密结合、更激进的工程优化文化，以及在有限算力约束下的创新策略。对于关注全球 AI 技术格局的开发者，这篇文章提供了一个有价值的第三方视角。""",

        "AI Coding Cost": """LangChain 创始人 Harrison Chase 指出 AI 编码成本正在快速上升，呼吁开发者更多地使用开源模型。文章引用数据显示 Kimi K2.6 在 Baseten 上的运行成本约为 OpenAI 同等能力模型的 1/5。随着 AI 编码代理（coding agents）的普及，token 消耗量呈指数级增长——一个中等规模的开发团队每天可能消耗数百万甚至上千万 token。这一趋势意味着"默认使用闭源最强模型"的策略在成本上可能不再可持续，开发者需要建立混合策略：核心路径用开源模型，关键节点用闭源模型把关。""",

        "Multi-Agent Architecture": """AI Engineer 发布了关于"真正能落地的多智能体架构"的深度解析。文章探讨了多智能体编码系统的实际架构设计——不同于理论上的多智能体框架，真正在生产环境中运行的系统需要考虑：智能体间的通信协议、任务分配策略、错误恢复机制、状态同步，以及最重要的"何时应该用一个智能体而非多个"。视频和配套文档提供了多个真实案例的架构图和代码示例，对于正在探索 AI Agent 工程实践的开发者是一份难得的实战资料。""",

        "GitHub Innovation Graph": """GitHub 分享了其 Innovation Graph 数据如何被研究者用于揭示"数字核心"（digital core）——即开源软件对全球经济的深层影响。Innovation Graph 提供了国家/地区级别的开源活动指标，包括活跃开发者数量、代码推送频率、仓库创建量等。研究者利用这些数据发现了开源贡献与经济创新指标之间的强相关性，以及不同地区技术栈偏好的演变趋势。对于数据科学家和对开源经济学感兴趣的开发者，这是一个值得探索的数据集。""",

        "Gemma Multi-token": """Paul Couvert 的实验展示了多 token 预测技术如何让 Gemma 4 在本地运行时获得 1.5 倍的速度提升，而无需更换模型或硬件。多 token 预测（Multi-token Prediction）是 Google 在训练 Gemma 4 时采用的技术，模型在一次前向传播中预测多个未来 token，而非传统的逐个预测。这不仅在训练时加速了收敛，在推理时通过投机解码（speculative decoding）也能显著降低延迟。对于希望在本地运行大模型的开发者，这是一个重要的性能优化方向。""",

        "Age Assurance Laws": """GitHub 博客讨论了全球各国推进的年龄验证（age assurance）立法对开发者的影响。这些法案旨在保护儿童和青少年上网，但部分提案可能要求开发者实施侵入性的身份验证机制，与开发者对隐私保护、匿名贡献和全球可访问性的价值观冲突。文章分析了不同国家立法的具体要求和潜在影响，呼吁开发者社区参与政策讨论，推动既保护未成年人又不损害开发者体验的技术方案——如基于密码学的年龄验证、分层访问控制等。""",

        "Ernie 5.1": """百度 Ernie-5.1 在 Search Arena 排行榜上位列第四，使百度成为搜索性能前三的实验室之一。Search Arena 是专门评估模型搜索能力的盲测平台，Ernie-5.1 的强势表现表明中国大模型在搜索增强和实时信息获取方面已达到世界领先水平。对于开发者而言，这意味着在构建需要搜索增强的 AI 应用时，可选择的模型范围进一步扩大——不同模型在搜索质量、响应速度、成本和支持语言等方面各有优势，可以根据具体场景进行选择。""",

        "Anthropic Hidden Motives": """Anthropic 最新发表的论文揭示了一种新方法，能够以大模型黑箱中"隐藏动机"的发现率提升 4 倍以上。传统上，判断 AI 到底在想什么、知道什么、隐瞒什么几乎是一个半技术半玄学的问题。Anthropic 的研究团队通过改进可解释性（interpretability）技术，更有效地提取模型内部表征与外部行为之间的关联，从而发现模型在思维链（Chain-of-Thought）中未明确表达的真实推理路径。这对 AI 安全研究和需要高可靠性 AI 系统的开发者都有重要意义。""",

        "Qdrant Vector DB": """Qdrant 的 Field Research 负责人 Brian O'Grady 做客 Stack Overflow Podcast，深入讨论了向量数据库在现代 AI 应用中的角色。Qdrant 是一个开源的向量数据库，专门优化了高维向量相似性搜索的性能。对话涵盖了向量数据库的选型考量（内存 vs 磁盘索引、分布式部署、混合搜索）、RAG 架构中的检索优化策略，以及从传统数据库迁移到向量数据库时的常见陷阱。对于正在构建 RAG 应用或考虑引入向量搜索的开发者，这次访谈提供了实用的架构决策参考。""",

        "Ardent Postgres Clone": """Y Combinator 孵化的 Ardent 推出了一项新技术，可以在 6 秒内克隆任意规模的 Postgres 数据库——即使数据量达到 TB 级别。这项技术让编码代理（coding agents）能够在生产数据的副本上安全测试代码，而工程团队也可以无风险地快速迭代。Ardent 已经被 Supermemory 和 Surface Labs 等团队采用，这些客户总计管理着超过 10TB 的数据。对于开发者来说，这解决了长期存在的"如何在真实数据上测试而不影响生产"的难题，是 AI 编码代理落地的重要基础设施。""",

        "Vibe Debugger": """开发者 Anish Acharya 构建了一个"Vibe Debugger"——一个 CLI 工具，让编码代理能够像人类开发者一样使用调试器：设置断点、单步进入函数、检查调用栈等。这个项目的灵感来自观察 AI 修复复杂 bug 时的推理轨迹：模型在循环中添加日志、重启程序、读取输出、再添加不同的日志——完全可以用调试器更高效地完成。工具基于 OpenAI 5.5 的 /goal 功能构建，展示了工具调用（tool calling）和 CLI 发现（CLI discovery）的实际应用。""",

        "CyberSecQwen": """Hugging Face 博客介绍了 CyberSecQwen-4B——一个专门面向防御性网络安全的小型模型，可以在本地运行。与追求通用能力的大模型不同，CyberSecQwen 专注于安全日志分析、漏洞检测、威胁情报解析等特定任务，4B 的参数量意味着它可以在消费级硬件上实时运行。文章讨论了为什么防御性安全需要专门化、本地可运行的小模型：延迟要求、数据隐私、离线环境，以及"让安全分析无处不在"的愿景。对于安全团队和希望将 AI 引入安全运维的开发者，这是一个值得关注的方向。""",

        "NVIDIA DeepStream": """NVIDIA 推广 DeepStream SDK 与生成式 AI 的结合，让开发者无需从零编写每一行代码就能从概念到部署视觉 AI 应用。DeepStream 是一个针对视频分析和 AI 推理优化的流处理框架，支持多路视频流的并行处理、自定义推理插件和边缘到云的灵活部署。与生成式 AI 结合后，开发者可以用自然语言描述需求，快速生成 DeepStream 应用的配置和代码骨架，再在此基础上进行定制。这大幅降低了视觉 AI 应用的开发门槛。""",
    }

    return summaries.get(name, summary)

# Select articles for each section
HOT_NEWS_KEYS = [
    "Gemini CLI DevOps",
    "Sparse Transformer Kernels",
    "GitHub Agentic Workflows",
    "GKE Cold Start",
    "LangSmith MCP",
    "GitHub Stacked PR",
    "CVE Smart TV",
    "Gemma Multi-token",
]

DEEP_DIVE_KEYS = [
    "Transformers Ate Vision",
    "AI Coding Cost",
]

TOOLS_KEYS = [
    "Vibe Debugger",
    "Ardent Postgres Clone",
    "CyberSecQwen",
    "Perplexity CUTLASS",
]

PRACTICE_KEYS = [
    "Stripe SaaS Payment",
    "Multi-Agent Architecture",
    "Douyin Performance",
]

# Collect all sources used
all_sources = set()

def get_article_or_placeholder(key):
    if key in categorized:
        return categorized[key]
    return None

def render_news_item(key):
    article = get_article_or_placeholder(key)
    if not article:
        return ""
    title = escape(article.get("title", "").strip())
    summary = extract_summary_for_article(key, article)
    source = make_source_link(article)
    all_sources.add((article.get("feed_title", ""), article.get("link", "")))
    return f"""
    <div class="news-item">
        <h3>{title}</h3>
        <p>{summary}</p>
        <div class="source">{source}</div>
    </div>
"""

# Build sections
hot_news_html = "".join(render_news_item(k) for k in HOT_NEWS_KEYS if get_article_or_placeholder(k))
deep_dive_html = "".join(render_news_item(k) for k in DEEP_DIVE_KEYS if get_article_or_placeholder(k))
tools_html = "".join(render_news_item(k) for k in TOOLS_KEYS if get_article_or_placeholder(k))
practice_html = "".join(render_news_item(k) for k in PRACTICE_KEYS if get_article_or_placeholder(k))

# Build source list
source_list = sorted(all_sources)
sources_html = "\n".join(
    f'<li><a href="{escape(link)}" target="_blank" rel="noopener">{escape(name)}</a></li>'
    for name, link in source_list if name and link
)

# Full HTML
HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>开发者日报 · {DATE_STR}</title>
    <style>
        :root {{
            --bg: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border: #30363d;
            --text: #c9d1d9;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent: #58a6ff;
            --accent-hover: #79c0ff;
            --success: #3fb950;
            --warning: #d29922;
            --danger: #f85149;
            --code-bg: #161b22;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.7;
            font-size: 15px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 24px;
        }}
        header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        .meta {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}
        .badge {{
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            color: var(--accent);
            font-weight: 600;
            letter-spacing: 0.5px;
        }}
        .date {{
            color: var(--text-muted);
            font-size: 13px;
        }}
        h1 {{
            font-size: 28px;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }}
        .subtitle {{
            color: var(--text-secondary);
            font-size: 15px;
        }}
        section {{
            margin-bottom: 40px;
        }}
        h2 {{
            font-size: 20px;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 20px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .news-item {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 16px;
            transition: border-color 0.2s;
        }}
        .news-item:hover {{
            border-color: var(--accent);
        }}
        .news-item h3 {{
            font-size: 16px;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 10px;
            line-height: 1.5;
        }}
        .news-item p {{
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.8;
            margin-bottom: 12px;
        }}
        .source {{
            font-size: 12px;
        }}
        .source a {{
            color: var(--text-muted);
            text-decoration: none;
            transition: color 0.2s;
        }}
        .source a:hover {{
            color: var(--accent-hover);
            text-decoration: underline;
        }}
        .sources-section {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 24px;
        }}
        .sources-section h2 {{
            border-bottom: none;
            margin-bottom: 16px;
        }}
        .sources-section ul {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 8px;
        }}
        .sources-section li {{
            font-size: 13px;
        }}
        .sources-section a {{
            color: var(--text-secondary);
            text-decoration: none;
        }}
        .sources-section a:hover {{
            color: var(--accent);
            text-decoration: underline;
        }}
        footer {{
            margin-top: 48px;
            padding-top: 24px;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
        }}
        @media (max-width: 600px) {{
            .container {{
                padding: 24px 16px;
            }}
            h1 {{
                font-size: 22px;
            }}
            .sources-section ul {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="meta">
                <span class="badge">DEVELOPER</span>
                <span class="date">{DATE_STR} {DAY_STR}</span>
            </div>
            <h1>开发者日报</h1>
            <p class="subtitle">为程序员和工程师精选的技术动态、工具更新与实践指南</p>
        </header>

        <section>
            <h2>今日技术热榜</h2>
            {hot_news_html}
        </section>

        <section>
            <h2>深度技术解读</h2>
            {deep_dive_html}
        </section>

        <section>
            <h2>工具推荐</h2>
            {tools_html}
        </section>

        <section>
            <h2>实践指南</h2>
            {practice_html}
        </section>

        <section class="sources-section">
            <h2>参考链接汇总</h2>
            <ul>
                {sources_html}
            </ul>
        </section>

        <footer>
            <p>数据来源: FreshRSS · 生成时间: {export_time}</p>
            <p>本日报由 AI 自动生成，内容基于公开技术资讯整理</p>
        </footer>
    </div>
</body>
</html>
"""

# Write output
output_path = "./tech-daily/developer_practice.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"\n✅ Generated: {output_path}")
print(f"   Articles used: {len([k for k in HOT_NEWS_KEYS + DEEP_DIVE_KEYS + TOOLS_KEYS + PRACTICE_KEYS if get_article_or_placeholder(k)])}")
print(f"   Sources listed: {len(source_list)}")
