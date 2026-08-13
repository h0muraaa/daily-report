#!/usr/bin/env python3
"""Generate academic research HTML daily report for 2026-08-13."""

import json
from html import escape

INPUT_PATH = '/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260813_184409.json'
OUTPUT_PATH = '/home/runner/work/daily-report/daily-report/tech-daily/academic_research.html'

with open(INPUT_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

export_time = data.get('export_time', '')
start_time = data.get('start_time', '')
end_time = data.get('end_time', '')
total_count = data.get('total_count', 0)
source_count = data.get('source_count', 0)


def link(url, text):
    return f'<a href="{escape(url)}" target="_blank" rel="noopener">{escape(text)}</a>'


def src(urls):
    parts = ' · '.join(link(u, t) for u, t in urls)
    return f'<div class="src">📎 来源：{parts}</div>'


# ============ 1. 研究动态 ============
research_items = [
    {
        'tag': '重大突破',
        'title': '价值线性代数 22 年悬案告破：Crouzeix 猜想被 GPT-5.6 自主运行 16 小时证明',
        'body': '折磨数值线性代数界整整 22 年的 Crouzeix 猜想于 2026 年 7 月 30 日被证明，证明者并非职业数学家，而是北京协和医院神经外科博士后兼住院医师 Shanmu Jin。他本科读地质、后获医学博士，无正规高等数学科班背景，其唯一助手是 GPT-5.6——在一次约 16 小时的完全自主运行中解决了这道难题，全程无人干预。验证者名单包含猜想提出者 Michel Crouzeix 本人，以及华盛顿大学应用数学系教授 Alex Townsend 和 Greenbaum，Townsend 此前一年内多次尝试让 GPT 5.6 证明该猜想均告失败。这一事件被普遍视为 AI 辅助数学发现的重要里程碑：AI 不再只是"学习人类已知知识"，而是开始搜索人类尚未找到的解。',
        'src': [('https://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652717902&idx=2&sn=bfec895c922b7afe9d3742cfbb811867', '新智元')],
    },
    {
        'tag': '重大突破',
        'title': 'Claude 一举扫清 2000 阶以下哈达玛矩阵，AI 开始"清空数学待解列表"',
        'body': '量子位报道，Claude 一次性解决了 2000 阶以下所有哈达玛矩阵的存在性问题。哈达玛矩阵（Hadamard matrix）是组合数学与编码理论中的经典对象，其存在性猜想困扰数学界已久。该进展与 Crouzeix 猜想证明同一天出现，被业界解读为"AI 清空数学待解列表"的开端。值得注意的是，好数学家不挑 AI 模型——此类成果更多体现为模型在搜索空间中的系统性探索能力，而非单一厂商的模型优势，这对 AI4Math 研究范式的讨论具有重要意义。',
        'src': [('https://www.qbitai.com/2026/08/472016.html', '量子位')],
    },
    {
        'tag': '模型研究',
        'title': 'Ilya 首个模型曝光：SSI 第一剑劈向持续学习',
        'body': '量子位报道，Ilya Sutskever 创立的安全超级智能公司（Safe Superintelligence, SSI）首个模型曝光，核心研究方向指向"持续学习"（continual learning）。这一选题值得关注：持续学习长期被视为大模型尚未攻克的难题——模型在部署后难以在不遗忘旧知识的前提下持续吸收新知识。若 SSI 在此方向取得突破，将重新定义"训练与部署"的边界，也可能对当前以预训练—后训练—推理三段式为主导的范式产生冲击。',
        'src': [('https://www.qbitai.com/2026/08/471701.html', '量子位')],
    },
    {
        'tag': '复现科学',
        'title': 'Hugging Face 发布 ICML 2026 开放复现报告：复现 2,200 篇论文的经验教训',
        'body': 'Hugging Face 官方博客发布《What We Learned by Reproducing 2,200 papers from ICML》，系统总结了大规模复现顶会论文的实践方法与教训。这是可复现性研究（reproducibility research）领域少有的大规模实证样本：覆盖 ICML 全会议程的 2,200 篇论文，沉淀出代码、数据、实验配置、评估协议等方面的共性痛点。对研究生与科研团队而言，这份报告既是选择"可复现基线"的实用指南，也为会议审稿与开源规范讨论提供了数据支撑。',
        'src': [('https://huggingface.co/blog/icml-2026-open-reproductions', 'Hugging Face Blog')],
    },
    {
        'tag': '安全研究',
        'title': '三大闭源模型的"加密推理思维链"被系统性破解：6708 份会话日志翻出 62 把 API 密钥',
        'body': '一支欧洲研究团队于 8 月 10 日挂出论文，宣称找到方法把 Anthropic、OpenAI、Google 三家旗舰模型的隐藏思考完整读出，并从网上公开的 6,708 份 AI 会话日志中检索出 62 把真实 API 密钥。研究团队强调：底层加密算法本身没有被破解，出问题的是 API 的设计——"加密思维链"的防护边界存在旁路。该工作与前一交易日曝光的 Stolen Thoughts 研究同属"推理轨迹安全"新方向，对推理隐私、防蒸馏与 API 安全设计提出了直接警示。',
        'src': [('https://x.com/xiaohu/status/2087905846475063796', '小互(@imxiaohu)')],
    },
    {
        'tag': '评估方法论',
        'title': 'Arena 发布 AutoEval：用数千万人类对战胜场训练奖励模型，压缩评估周期',
        'body': 'Arena.ai 发布 AutoEval 方法论：利用历史上数千万场真实人类对战数据训练一个奖励模型，使其能够在规模上估计人类偏好，从而"以边界速度"交付评测结果，把模型评估反馈回路从数周压缩到数小时。与 LLM-as-judge 不同，AutoEval 仍是一个 live benchmark——它源自真实世界对战胜场，奖励模型对人类提示与模型响应进行打分。Arena 强调 DeepSeek-V4-Pro（Max）的早期 AutoEval 得分已公布（Code Arena WebDev 约 #8 总榜 / #2 开源），并将在人类实时投票充分后收敛。这一方法论为"无人类即时标注的规模化评估"提供了新思路。',
        'src': [('https://x.com/arena/status/2087646143908135008', 'Arena.ai(@lmarena_ai)')],
    },
    {
        'tag': '顶会论文',
        'title': 'ICML 2026 | InstEmb：让 embedding"瞥见未来"的指令遵循嵌入框架',
        'body': '京东零售技术团队公开其被 ICML 2026 接收的工作 InstEmb（Instruction-Following Embeddings through Glimpses of the Future）。核心思想是让 embedding 不只理解"输入说了什么"，还尽可能理解"模型接下来会如何回答"：在输入后追加一组可学习的 look-ahead tokens，通过 frozen teacher 的输出条件表示进行自蒸馏，使这些 tokens 学到 output-aware semantics；同时以多视图对比学习强化输入语义，最终通过 Dual-Anchor Alignment Pooling（DAAP）显式融合两类语义。该工作为检索、聚类与 RAG 中的指令遵循场景提供了新的表示学习范式。',
        'src': [('https://mp.weixin.qq.com/s?__biz=MzU1MzE2NzIzMg==&mid=2247502482&idx=1&sn=3e27a05db6ceb587711658fdf7b91f56', '京东技术')],
    },
    {
        'tag': '新基准',
        'title': 'IEEE SLT 2026 SmartGlasses Challenge：为可穿戴 egocentric 多说话人语音理解建基准',
        'body': 'arXiv 新作发布 IEEE SLT 2026 SmartGlasses Challenge，聚焦智能眼镜这一可穿戴语音界面的 egocentric 多说话人语音识别与理解。该场景面临动态声学条件、说话人重叠以及由佩戴者为中心录制几何带来的空间模糊性等挑战，现有语音基准难以覆盖。该挑战赛为音频—语言模型（Audio-Language Models）在可穿戴设备上的系统评估提供了标准化任务，是"语音理解从手机走向眼镜"这一趋势的基础设施型工作。',
        'src': [('https://arxiv.org/abs/2608.12034', 'cs.SD updates on arXiv.org')],
    },
]

# ============ 2. 深度论文解读 ============
deep_dive_items = [
    {
        'title': 'Luna-TTS Family Technical Report（arXiv:2608.11593）',
        'lead': '提出基于扩散语言模型（Diffusion-LM）的 TTS 家族，在 100 万小时中英日韩多语言语音上预训练，正面回应 AR codec LM 的三项结构性缺陷。',
        'background': '现代 TTS 由自回归（AR）codec 语言模型主导，其从左到右的解码带来三项结构性代价：延迟随话语长度线性增长、错误沿已提交前缀累积、以及人为施加于 RVQ token 网格上的生成顺序。这些限制对实时交互与长语音生成构成了根本性瓶颈。',
        'innovation': 'Luna-TTS Family 采用扩散语言模型作为解码骨干，避开 AR 顺序强加；模型家族通过对预训练 AR 文本 LLM 的渐进式适配构建，从因果到非因果逐步迁移能力，覆盖中文、英文、日文与韩文四种语言，预训练规模达 100 万小时。',
        'result': '作为系统性的技术报告，该家族展示了扩散式 TTS 在语音质量、说话人相似度与多语言泛化上的竞争力，同时缓解了 AR codec 模型的延迟与误差累积问题，为"非自回归 TTS 能否规模化"提供了正面证据。',
        'significance': '这项工作与同日开源的小红书 dots.tts（连续自回归、跳过离散 token）形成对照，共同表明 TTS 的 tokenization 与解码范式正处于重构期。对语音合成研究者而言，Luna-TTS 提供了 AR codec LM 之外完整、可训练的第三范式参考。',
        'src': [('https://arxiv.org/abs/2608.11593', 'cs.SD updates on arXiv.org')],
    },
    {
        'title': 'Do Text-to-Music Models Really Follow Instructions? A Counterfactual Evaluation（arXiv:2608.11899）',
        'lead': '用匹配反事实评估分离"目标属性出现率"与"指令归因控制"，揭示文本到音乐可控性证据中的系统性高估。',
        'background': '提示属性一致性（prompted attribute agreement）常被当作文本到音乐模型可控性的证据，但其逻辑存在漏洞：请求的属性可能只是该模型输出分布中本来就常见的属性，与是否真正"遵循指令"无关。',
        'innovation': '论文引入匹配反事实评估（matched counterfactual evaluation）：每个测试族包含一个省略评分属性的中性输入，以及两个其余部分匹配、仅交换目标属性的输入。三者通过冻结的本地接口适配器、共享随机种子渲染，从而在控制无关变量的前提下，把"目标属性发生"与"指令归因的控制效应"解耦。',
        'result': '将该框架应用到全局文本到音乐模型上，作者对 key 与 beat grouping 等属性的可控性证据进行了重新检验，发现了传统一致性指标高估控制能力的现象。',
        'significance': '该工作的方法论价值不限于音乐：它提出的反事实评估设计，可推广到图像生成、视频生成与语音合成等一切"以自然语言为控制接口"的生成任务，是可控生成评估方向的重要参考。',
        'src': [('https://arxiv.org/abs/2608.11899', 'cs.SD updates on arXiv.org')],
    },
]

# ============ 3. 开源资源 ============
resource_groups = {
    '开源模型与权重': [
        {
            'title': 'Qwen3.8-2.4T-A95B — Qwen 首次开放 Max 级 2.4T 参数旗舰权重',
            'body': 'Qwen 在 Hugging Face 公开 Qwen3.8-2.4T-A95B：共 2.446T 参数、每 token 激活约 95B、512 个路由专家，原生上下文 262,144 token，可经推理框架扩展至约 1M。这是 Qwen 首次开放 Max 级模型权重；开放权重版仅支持文本输入且思考模式不可关闭，可用 low/medium/xhigh 调节推理强度。BF16 权重约占 4.89TB、213 个 safetensors 分片，SGLang、vLLM 与 TokenSpeed 均已给出部署路径，属多机多卡级工程。',
            'src': [('https://mp.weixin.qq.com/s?__biz=MzkyMzcwMDIyMQ==&mid=2247503230&idx=1&sn=62c545c1ac19cd52a4b98ca131db57c6', '机器之心SOTA模型')],
        },
        {
            'title': 'DeepSeek-V4-Pro 正式版（0813）— 性能超 Opus-4.8，接近 Fable 5',
            'body': 'DeepSeek-V4-Pro 0813 正式版发布，社区实测与官方口径一致：性能超过 Opus-4.8、接近 Fable 5，同时保持极低的 API 价格。该模型此前经历一次"静默发布后撤回"，随后正式 GA。同日 DeepSeek 还宣布 API 于 8 月 17 日起改为峰谷定价，缓存命中的输入价上调约 12 倍、输出价上调约 4.5 倍。对开源研究社区而言，V4-Pro 以更低成本逼近闭源前沿，是"开源/闭源差距"研究的重要样本。',
            'src': [('https://x.com/xiaohu/status/2087916909870358634', '小互(@imxiaohu)'), ('https://x.com/dotey/status/2087893881496985988', '宝玉(@dotey)')],
        },
        {
            'title': 'NVIDIA Nemotron 3.5 Lightning — 30B MoE（3B 激活）Agent 执行模型',
            'body': 'NVIDIA 发布 Nemotron 3.5 Lightning：30B MoE 架构、3B 激活参数，采用 LatentMoE 与 Mamba 混合架构，支持 1M token 上下文，由 Nemotron 3 Ultra 蒸馏而来，定位"高吞吐、高并发的常驻 Agent"执行引擎。生态反馈强调其"易后训练"：多团队在数小时、单机四卡规模下完成领域微调并取得显著提升（如 Harvey 在 Legal Agent Bench 将 agent 表现从 0% 提升至 8.3% 且无回归），Reasonable.io 仅用 4B token 合成数据微调即在机器可校验证明上超越其 50 倍大小的模型。其随权重发布的后训练生态为"小模型 + 持续学习"研究提供了高价值基座。',
            'src': [('https://x.com/NVIDIAAI/status/2087662769512571010', 'NVIDIA AI(@NVIDIAAI)'), ('https://x.com/NVIDIAAI/status/2087657298026246197', 'NVIDIA AI — Reasonable.io 证明')],
        },
        {
            'title': 'WeLM — 微信发布的大语言模型家族：80B (A3B) 与 617B (A23B)',
            'body': '微信团队在 X 上独家发布 WeLM 模型家族，主打"资源效率"（resource efficiency）：80B (A3B) 与 617B (A23B) 两款激活参数占比极低的稀疏模型。值得学术社区关注的是其发布渠道与叙事——微信以 MoE 稀疏化追求更低推理成本，这与当日 Qwen、DeepSeek、xAI 的发布形成"旗舰模型密集发布日"。目前官方细节有限，具体架构与评测待进一步技术报告披露。',
            'src': [('https://x.com/shao__meng/status/2087876422241263649', 'meng shao(@shao__meng)')],
        },
        {
            'title': '小红书开源 dots.tts — 20 亿参数连续自回归语音合成基座',
            'body': '小红书 dots 团队开源 dots.tts：20 亿参数、全连续、端到端自回归 TTS 模型，跳过离散声学 token、直接在连续隐空间中进行自回归生成。在 Seed-TTS-Eval 三个子集上取得最佳平均内容准确度与平均说话人相似度；完整开放六个检查点，覆盖预训练、自纠正对齐、四步/两步/单步低步数生成与 1T1A 双流模式。普通流式模式首包延迟 85.4ms、1T1A 双流模式 54.4ms，训练、推理、微调、蒸馏代码全部 Apache 2.0 开放，并延伸出 dots.tts.edit 的音色/情绪/韵律编辑能力。',
            'src': [('https://mp.weixin.qq.com/s?__biz=Mzg4OTc2MzczNg==&mid=2247496062&idx=1&sn=d4c48926c5d7607f129dfea03699a6c0', '小红书技术REDtech')],
        },
        {
            'title': 'Lightricks 开源 LTX-2.5 — 22B 音画同步生成模型',
            'body': 'Lightricks 开放 LTX-2.5 权重：22B 参数，可根据文本、图像与视频输入生成同步音画。相比 LTX-2.3 更新了扩散视频解码器（替换 VAE 重建阶段，改善人脸、纹理与运动中瑕疵）、定制 Gemma 4 12B 文本编码器与 Prompt Enhancer、原生多镜头、自动时长预测与 4K HDR/RAW 工作流。同时提供面向微调的 Dev 权重与固定 8 步推理的 Distilled 权重，已上线 ModelScope 与 GitHub。对多模态生成研究是可直接复用的音画联合模型。',
            'src': [('https://mp.weixin.qq.com/s?__biz=Mzk3NTc1NTU0Mw==&mid=2247511972&idx=1&sn=df080db0eab815c9bde93b04c343f661', '魔搭ModelScope社区')],
        },
    ],
    '开源框架与工具': [
        {
            'title': 'DeepSeek Harness v0.1 — "Everything is a plugin"的 Agent 元框架（MIT 开源）',
            'body': 'DeepSeek 正式开源 Agent 框架 DeepSeek Harness v0.1（开发者预览版，MIT 协议）。其核心理念是"一切皆插件"：模型、工具、Skills、会话、沙箱、文件系统、循环、编排乃至 UI 全部实现为可自由组合、替换与扩展的插件，底层由 Cordis 元框架驱动。这不再是固定工作流的包装器，而是一套可按需组装的 Agent 底层系统；发布后 1 小时即接近 2 万 star。对 Agent 架构研究而言，它把"Agent 主循环本身可编程"从理念落成了代码。',
            'src': [('https://x.com/deepseek_ai/status/2087887408440164663', 'DeepSeek(@deepseek_ai)'), ('https://www.ifanr.com/1675083', '爱范儿')],
        },
    ],
    '数据集与基准': [
        {
            'title': 'OSSL-v2 — 公版电影片段构成的自托管视频配乐语料库',
            'body': '对话感知视频配乐生成论文（arXiv:2608.11576）发布 OSSL-v2：一个自托管的 34,343 段视频片段、合计 246.4 小时的语料库，全部来自公版（public-domain）电影。其动机是直面该领域长期存在的可复现性鸿沟——既有研究常以 YouTube URL 引用爬取语料，链接失效导致数据难以获取。OSSL-v2 为视频到音乐生成提供了可长期复现的标准化数据基座。',
            'src': [('https://arxiv.org/abs/2608.11576', 'cs.MM updates on arXiv.org')],
        },
    ],
}

# ============ 4. 趋势观察 ============
trend_items = [
    {
        'title': 'AI4Science 进入"搜索未知解"阶段：从学习已知知识转向发现新结构',
        'body': 'Crouzeix 猜想（22 年悬案、GPT-5.6 自主运行 16 小时证明）与 Claude 扫清 2000 阶以下哈达玛矩阵，是 AI 数学能力从"刷已知题库"迈向"搜索人类未解结构"的标志性事件。更深层的信号在于范式转变：AI4S 最值钱的能力正从"记住多少知识"转向"能在多大空间里找到新解"。AlphaFold 代表上一阶段——问题明确、数据充足、专用模型极致求解；而 Crouzeix 这类问题没有现成答案，真正耗时的往往是"决定下一步算什么"。对研究者而言，如何评测与引导模型的开放搜索能力，将成为 AI4Math 的核心课题。',
    },
    {
        'title': '评估方法论走向"对抗与反事实"：AutoEval 与可控性反事实评估并进',
        'body': '今日两条评估新闻指向同一趋势——评测正从"聚合分数"走向"方法论严谨性"。Arena AutoEval 用数千万真实人类对战胜场训练奖励模型，在保持 live benchmark 属性的同时把评估周期从数周压到数小时；而反事实评估论文（text-to-music instruction following）则揭示：目标属性在输出分布中的"自然出现率"可能被误读为"指令控制力"，必须用匹配反事实设计才能分离两者。配合 Hugging Face 对 2,200 篇 ICML 论文的大规模复现报告，可以断言：可复现性、反事实对照与规模化偏好建模将成为下一代评估基础设施的三根支柱。',
    },
    {
        'title': '开源从"模型权重"走向"全栈生态"：权重、Harness、后训练配方同日齐发',
        'body': '8 月 13 日堪称"开源夏季"的集中爆发：Qwen 首次开放 Max 级 2.4T 权重、DeepSeek-V4-Pro 正式版与 Harness 元框架、NVIDIA Nemotron 3.5 Lightning 连同后训练生态、小红书 dots.tts 连同完整训练链路、Lightricks LTX-2.5 连同微调/蒸馏双权重。这不再是单纯的"模型发布"，而是权重—工具—数据—后训练配方的全栈开放：Nemotron 3.5 的多个合作方在数小时内完成领域微调并显著超越基线，证明"开放可复现的高质量基座 + 持续学习"正成为研究的主流工作流，竞争维度从"谁的模型强"转向"谁的后训练生态更顺滑"。',
    },
    {
        'title': '语音生成范式重构：连续自回归与扩散语言模型向 AR codec LM 发起挑战',
        'body': '小红书 dots.tts（连续隐空间自回归、跳过离散 token）与 Luna-TTS Family（扩散语言模型解码、100 万小时预训练）同日发布，形成对主流 AR codec LM 范式的两面夹击：前者质疑"为何要把语音量化成离散 token"，后者质疑"为何要强加从左到右的生成顺序"。两者都指向更低的推理延迟与更强的可控性。叠加此前 WavTokenizer 等连续表征工作，TTS 的 tokenization 与解码范式正进入重构窗口期，值得语音研究者重点跟踪。',
    },
    {
        'title': '持续学习成为下一站：从 Ilya 的 SSI 到常驻 Agent 的后训练',
        'body': 'Ilya 首个模型将 SSI 的第一剑劈向持续学习；NVIDIA Nemotron 3.5 Lightning 的生态叙事则是"小模型 + 频繁后训练"（Trajectory 称"模型每客户、每晚重训"正在成为可能）；Grok 4.6 亦定位"持续工作 Agent"。三个信号交汇指向同一判断：当预训练逼近数据与算力边界，模型价值的增量将来自部署后的持续学习与高频后训练。如何在避免灾难性遗忘的前提下实现可靠的持续积累，很可能决定下一代 Agent 系统的能力上限。',
    },
]

# ============ 参考文献 ============
references = [
    ('新智元 — Crouzeix 猜想被协和住院医师 + GPT-5.6 证明', 'https://mp.weixin.qq.com/s?__biz=MzI3MTA0MTk1MA==&mid=2652717902&idx=2&sn=bfec895c922b7afe9d3742cfbb811867'),
    ('量子位 — Claude 扫清 2000 阶以下哈达玛矩阵', 'https://www.qbitai.com/2026/08/472016.html'),
    ('量子位 — Ilya 首个模型曝光', 'https://www.qbitai.com/2026/08/471701.html'),
    ('Hugging Face Blog — What We Learned by Reproducing 2,200 papers from ICML', 'https://huggingface.co/blog/icml-2026-open-reproductions'),
    ('小互(@imxiaohu) — 三大模型加密推理思维链被破解', 'https://x.com/xiaohu/status/2087905846475063796'),
    ('Arena.ai — AutoEval 方法论', 'https://x.com/arena/status/2087646143908135008'),
    ('京东技术 — ICML 2026 InstEmb', 'https://mp.weixin.qq.com/s?__biz=MzU1MzE2NzIzMg==&mid=2247502482&idx=1&sn=3e27a05db6ceb587711658fdf7b91f56'),
    ('arXiv:2608.12034 — IEEE SLT 2026 SmartGlasses Challenge', 'https://arxiv.org/abs/2608.12034'),
    ('arXiv:2608.11593 — Luna-TTS Family Technical Report', 'https://arxiv.org/abs/2608.11593'),
    ('arXiv:2608.11899 — Counterfactual Evaluation of Text-to-Music', 'https://arxiv.org/abs/2608.11899'),
    ('机器之心SOTA模型 — Qwen 首次开放 2.4T Max 权重', 'https://mp.weixin.qq.com/s?__biz=MzkyMzcwMDIyMQ==&mid=2247503230&idx=1&sn=62c545c1ac19cd52a4b98ca131db57c6'),
    ('小互(@imxiaohu) — DeepSeek 三件大事', 'https://x.com/xiaohu/status/2087916909870358634'),
    ('NVIDIA AI — Nemotron 3.5 Lightning 后训练生态', 'https://x.com/NVIDIAAI/status/2087662769512571010'),
    ('NVIDIA AI — Reasonable.io 用 30B 模型写机器可校验证明', 'https://x.com/NVIDIAAI/status/2087657298026246197'),
    ('meng shao — 微信 WeLM 模型家族', 'https://x.com/shao__meng/status/2087876422241263649'),
    ('小红书技术REDtech — dots.tts 开源', 'https://mp.weixin.qq.com/s?__biz=Mzg4OTc2MzczNg==&mid=2247496062&idx=1&sn=d4c48926c5d7607f129dfea03699a6c0'),
    ('魔搭ModelScope社区 — LTX-2.5 开源', 'https://mp.weixin.qq.com/s?__biz=Mzk3NTc1NTU0Mw==&mid=2247511972&idx=1&sn=df080db0eab815c9bde93b04c343f661'),
    ('DeepSeek(@deepseek_ai) — DeepSeek Harness v0.1', 'https://x.com/deepseek_ai/status/2087887408440164663'),
    ('爱范儿 — DeepSeek Harness 首发体验', 'https://www.ifanr.com/1675083'),
    ('arXiv:2608.11576 — Dialogue-Aware Video-to-Music (OSSL-v2)', 'https://arxiv.org/abs/2608.11576'),
    ('宝玉(@dotey) — DeepSeek Harness 开源', 'https://x.com/dotey/status/2087893881496985988'),
]


def render_item(item):
    tags = f'<span class="tag">{escape(item["tag"])}</span>' if item.get('tag') else ''
    return f'''  <div class="item">
    <h3>{tags}{escape(item["title"])}</h3>
    <p>{escape(item["body"])}</p>
    {src(item["src"])}
  </div>
'''


def render_paper(p):
    return f'''  <div class="paper-block">
    <div class="paper-title">{escape(p["title"])}</div>
    <p class="lead">摘要：{escape(p["lead"])}</p>
    <h4>研究背景</h4>
    <p>{escape(p["background"])}</p>
    <h4>核心创新</h4>
    <p>{escape(p["innovation"])}</p>
    <h4>结果与验证</h4>
    <p>{escape(p["result"])}</p>
    <h4>学术意义</h4>
    <p>{escape(p["significance"])}</p>
    {src(p["src"])}
  </div>
'''


def render_resource_group(title, items):
    inner = '\n'.join(
        f'<li><strong>{escape(i["title"])}</strong>：{escape(i["body"])} {src(i["src"])}</li>'
        for i in items
    )
    return f'''  <div class="item">
    <h3>{escape(title)}</h3>
    <ul class="res-list">{inner}</ul>
  </div>
'''


def render_trend(t, idx):
    return f'''  <div class="trend-item">
    <h3>{idx} {escape(t["title"])}</h3>
    <p>{escape(t["body"])}</p>
  </div>
'''


research_html = '\n'.join(render_item(i) for i in research_items)
deep_html = '\n'.join(render_paper(p) for p in deep_dive_items)
resources_html = '\n'.join(render_resource_group(g, items) for g, items in resource_groups.items())
trends_html = '\n'.join(render_trend(t, f'{"①" if idx==0 else "②" if idx==1 else "③" if idx==2 else "④" if idx==3 else "⑤"}') for idx, t in enumerate(trend_items))

refs_html = '\n'.join(
    f'    <div class="ref-item"><span class="idx">[{i+1}]</span>{link(u, t)}</div>'
    for i, (t, u) in enumerate(references)
)

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>科技日报 · 学术研究员版 — 2026-08-13</title>
<style>
  :root {{
    --primary: #1a4f8b;
    --primary-light: #3b6ea8;
    --accent: #8b1a1a;
    --bg: #ffffff;
    --bg-soft: #f5f7fa;
    --border: #d8dee6;
    --text: #1a1a1a;
    --text-secondary: #4a4a4a;
    --text-muted: #6b7280;
    --code-bg: #f0f2f5;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "Source Serif Pro", "Georgia", "Times New Roman", "Songti SC", "Noto Serif SC", "SimSun", serif;
    color: var(--text);
    background: var(--bg-soft);
    line-height: 1.75;
    font-size: 15.5px;
  }}
  .page {{
    max-width: 860px;
    margin: 0 auto;
    background: var(--bg);
    padding: 48px 56px 64px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  header.article-header {{
    border-bottom: 2px solid var(--primary);
    padding-bottom: 20px;
    margin-bottom: 8px;
  }}
  .kicker {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 10px;
  }}
  h1 {{
    font-size: 26px;
    font-weight: 700;
    color: var(--primary);
    line-height: 1.4;
  }}
  .subtitle {{
    font-size: 14px;
    color: var(--text-secondary);
    margin-top: 8px;
    font-style: italic;
  }}
  .meta {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12.5px;
    color: var(--text-muted);
    margin-top: 12px;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
  }}
  .abstract {{
    background: var(--bg-soft);
    border-left: 3px solid var(--primary-light);
    padding: 14px 18px;
    margin: 20px 0 8px;
    font-size: 14px;
    color: var(--text-secondary);
  }}
  .abstract strong {{ color: var(--primary); }}
  section {{ margin-top: 36px; }}
  h2 {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 17px;
    font-weight: 700;
    color: var(--primary);
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 18px;
    display: flex;
    align-items: baseline;
    gap: 10px;
  }}
  h2 .no {{
    font-family: Georgia, serif;
    font-size: 15px;
    color: var(--text-muted);
    font-weight: 400;
  }}
  .item {{
    margin-bottom: 26px;
    padding-left: 18px;
    border-left: 2px solid #e2e8f0;
    transition: border-color .15s;
  }}
  .item:hover {{ border-left-color: var(--primary-light); }}
  .item h3 {{
    font-size: 15.5px;
    font-weight: 700;
    color: var(--text);
    line-height: 1.5;
    margin-bottom: 6px;
  }}
  .item h3 .tag {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    display: inline-block;
    font-size: 10.5px;
    font-weight: 600;
    color: var(--primary);
    background: #e8eef5;
    border-radius: 3px;
    padding: 1px 7px;
    margin-right: 8px;
    vertical-align: 2px;
    letter-spacing: 0.5px;
  }}
  .item p {{
    color: var(--text-secondary);
    font-size: 14.5px;
    text-align: justify;
  }}
  .src {{
    margin-top: 8px;
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12px;
    color: var(--text-muted);
  }}
  .src a {{
    color: var(--primary-light);
    text-decoration: none;
    border-bottom: 1px dotted var(--primary-light);
  }}
  .src a:hover {{ border-bottom-style: solid; }}

  .paper-block {{
    background: var(--bg-soft);
    border: 1px solid var(--border);
    padding: 20px 24px;
    margin-bottom: 28px;
  }}
  .paper-block .paper-title {{
    font-size: 16px;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 12px;
  }}
  .paper-block h4 {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--accent);
    margin: 14px 0 4px;
    letter-spacing: 1px;
  }}
  .paper-block p {{
    font-size: 14px;
    color: var(--text-secondary);
    text-align: justify;
  }}
  .paper-block .lead {{
    font-style: italic;
    color: var(--text);
  }}

  ul.res-list {{ list-style: none; padding: 0; }}
  ul.res-list li {{
    margin-bottom: 16px;
    color: var(--text-secondary);
    font-size: 14px;
    text-align: justify;
  }}
  ul.res-list li .src {{ margin-top: 4px; }}
  ul.res-list li strong {{ color: var(--text); }}

  ul.trend-list {{ list-style: none; padding-left: 0; }}
  .trend-item {{
    margin-bottom: 22px;
    padding-left: 18px;
    border-left: 2px solid #e2e8f0;
  }}
  .trend-item h3 {{
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 14.5px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 6px;
  }}
  .trend-item p {{
    color: var(--text-secondary);
    font-size: 14px;
    text-align: justify;
  }}

  .refs {{
    columns: 2;
    column-gap: 32px;
    font-size: 13px;
  }}
  .refs .ref-item {{
    break-inside: avoid;
    margin-bottom: 10px;
    color: var(--text-secondary);
  }}
  .refs .ref-item .idx {{
    font-family: "Helvetica Neue", Arial, sans-serif;
    color: var(--accent);
    font-weight: 600;
    margin-right: 4px;
  }}
  .refs a {{
    color: var(--primary-light);
    text-decoration: none;
    word-break: break-all;
  }}
  .refs a:hover {{ text-decoration: underline; }}

  footer {{
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid var(--border);
    font-family: "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 12px;
    color: var(--text-muted);
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }}
  @media (max-width: 640px) {{
    .page {{ padding: 24px 20px 40px; }}
    .refs {{ columns: 1; }}
  }}
</style>
</head>
<body>
<div class="page">

<header class="article-header">
  <div class="kicker">Research Daily Briefing</div>
  <h1>科技日报 · 学术研究员版</h1>
  <div class="subtitle">2026-08-13 · 人工智能与计算机科学领域研究动态综述</div>
  <div class="meta">
    <span>数据窗口：{start_time} — {end_time}</span>
    <span>筛选新闻源：{total_count} 条 / {source_count} 个来源</span>
    <span>角色：Academic Researcher</span>
  </div>
</header>

<div class="abstract">
  <strong>本期导读：</strong>今日最重磅的学术事件是数学界两起 AI 驱动的突破：价值线性代数领域悬而未决 22 年的 Crouzeix 猜想，被一位协和医院神经外科医生借助 GPT-5.6 约 16 小时自主运行证明，验证者包括猜想提出者本人；几乎同时，Claude 一举扫清 2000 阶以下哈达玛矩阵的存在性问题，AI 开始"清空人类数学待解列表"。开源侧迎来密集发布：Qwen 首次开放 2.4T 参数 Max 级旗舰权重、DeepSeek-V4-Pro 正式版与 DeepSeek Harness 元框架、NVIDIA Nemotron 3.5 Lightning、小红书 dots.tts、Lightricks LTX-2.5 同日亮相。评估方法论亦有重要进展：Arena 发布基于数千万真实对战的 AutoEval 奖励模型评估法，Hugging Face 公开复现 2,200 篇 ICML 论文的系统性经验。语音与音频方向 arXiv 新作密集，"连续自回归 + 扩散语言模型"正对主流 AR codec 范式发起挑战。
</div>

<!-- ============ 1. 研究动态 ============ -->
<section>
  <h2><span class="no">§1</span>研究动态</h2>
{research_html}
</section>

<!-- ============ 2. 深度论文解读 ============ -->
<section>
  <h2><span class="no">§2</span>深度论文解读</h2>
{deep_html}
</section>

<!-- ============ 3. 开源资源 ============ -->
<section>
  <h2><span class="no">§3</span>开源资源</h2>
{resources_html}
</section>

<!-- ============ 4. 趋势观察 ============ -->
<section>
  <h2><span class="no">§4</span>趋势观察</h2>
{trends_html}
</section>

<!-- ============ 5. 参考文献 ============ -->
<section>
  <h2><span class="no">§5</span>参考文献</h2>
  <div class="refs">
{refs_html}
  </div>
</section>

<footer>
  <span>科技日报 · 学术研究员版 | 2026-08-13</span>
  <span>由 tech-daily-generator 生成 | 数据源：FreshRSS 24h 聚合 | 数据截至 {export_time}</span>
</footer>

</div>
</body>
</html>
"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"✅ Generated: {OUTPUT_PATH}")
print(f"   研究动态: {len(research_items)} 条")
print(f"   深度解读: {len(deep_dive_items)} 篇")
print(f"   开源资源: {sum(len(v) for v in resource_groups.values())} 项")
print(f"   趋势观察: {len(trend_items)} 条")
print(f"   参考文献: {len(references)} 条")
