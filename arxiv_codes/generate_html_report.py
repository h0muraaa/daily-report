#!/usr/bin/env python3
"""
生成 arXiv 日报 HTML 页面（横屏单栏布局版）

特性：
- 展示最新的 12 篇论文（不限制日期）
- 每行一篇论文，共12行（单卡片全宽布局）
- 横屏图片优化显示
- 使用论文原始摘要
"""

import json
import re
from datetime import datetime
import os

# 使用相对路径或环境变量
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', './arxiv-daily-output')
PROCESSED_JSON = os.path.join(OUTPUT_DIR, "papers_processed.json")
HTML_OUTPUT = os.path.join(OUTPUT_DIR, "arxiv-daily", "index.html")


def clean_summary(text):
    """清理摘要格式"""
    if not text:
        return ""

    # 去除 Markdown 星号（**粗体**、*斜体*）
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^(Summary:|摘要：|摘要:)', '', text, flags=re.IGNORECASE)

    return text.strip()


def generate_html():
    """生成 HTML 日报"""
    if not os.path.exists(PROCESSED_JSON):
        print(f"错误: 找不到 {PROCESSED_JSON}")
        return False

    with open(PROCESSED_JSON, 'r', encoding='utf-8') as f:
        all_papers = json.load(f)

    # 只选择已完成的论文（有图片文件存在的）
    papers = []
    for p in all_papers:
        image_path = p.get('image', '')
        if image_path:
            # 转换为完整路径并检查文件是否存在
            full_path = os.path.join(OUTPUT_DIR, 'arxiv-daily', image_path)
            if os.path.exists(full_path) or os.path.exists(full_path.replace('.png', '.jpg')):
                papers.append(p)

    if not papers:
        print(f"没有已完成的论文，跳过生成")
        return False

    # 按处理日期排序，去重保留每篇论文最新版本，取最新的 12 篇
    papers.sort(key=lambda x: x.get('processed_date', ''), reverse=True)

    # 去重：保留每篇论文（按 arxiv_id）的最新版本
    seen_ids = set()
    unique_papers = []
    for p in papers:
        arxiv_id = p.get('arxiv_id', '').replace('v1', '')
        if arxiv_id and arxiv_id not in seen_ids:
            seen_ids.add(arxiv_id)
            unique_papers.append(p)

    papers = unique_papers[:12]

    today = datetime.now().strftime('%Y-%m-%d')

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>arXiv Audio & Speech 论文日报 - {today}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header p {{ opacity: 0.9; font-size: 1.1em; }}
        .archive-link {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .archive-link a {{
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            background: rgba(255,255,255,0.2);
            border-radius: 8px;
            transition: background 0.2s;
        }}
        .archive-link a:hover {{ background: rgba(255,255,255,0.3); }}

        /* 单栏列表布局 */
        .papers-list {{
            display: flex;
            flex-direction: column;
            gap: 24px;
            margin-bottom: 40px;
        }}

        .paper-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            transition: transform 0.2s;
        }}
        .paper-card:hover {{ transform: translateY(-2px); }}

        .paper-header {{
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 16px;
        }}
        .paper-number {{
            flex-shrink: 0;
            display: inline-block;
            background: #667eea;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            text-align: center;
            line-height: 40px;
            font-weight: bold;
            font-size: 1em;
        }}
        .paper-title {{
            flex: 1;
            font-size: 1.3em;
            color: #333;
            line-height: 1.4;
        }}
        .paper-title a {{
            color: #333;
            text-decoration: none;
            transition: color 0.2s;
        }}
        .paper-title a:hover {{ color: #667eea; }}

        .paper-authors {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 12px;
            padding-left: 56px;
        }}

        .paper-summary {{
            color: #444;
            font-size: 0.95em;
            line-height: 1.7;
            margin-bottom: 16px;
            padding: 16px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .paper-infographic {{
            text-align: center;
            margin-top: 16px;
            padding-top: 16px;
            border-top: 1px solid #eee;
        }}
        .paper-infographic img {{
            max-width: 100%;
            max-height: 400px;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }}
        .original-link {{
            display: inline-block;
            margin-top: 12px;
            color: #667eea;
            text-decoration: none;
            font-size: 0.9em;
        }}
        .original-link:hover {{ text-decoration: underline; }}

        footer {{
            text-align: center;
            color: white;
            opacity: 0.8;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>arXiv Audio & Speech 论文日报</h1>
            <p>EESS.AS 类别 · {today} · 共 {len(papers)} 篇</p>
        </header>

        <div class="archive-link">
            <a href="archive/">📚 历史归档</a>
        </div>

        <div class="papers-list">
'''

    for idx, paper in enumerate(papers, 1):
        authors = paper.get('authors', [])
        authors_str = ', '.join(authors[:3])
        if len(authors) > 3:
            authors_str += f" 等{len(authors)}人"

        # 使用原始摘要
        summary = clean_summary(paper.get('abstract', ''))

        # 图片路径改为 .jpg
        image_path = paper.get('image', '')
        if image_path.endswith('.png'):
            image_path = image_path[:-4] + '.jpg'

        # 使用PDF URL（优先pdf_url字段，否则从abs_url构造）
        if 'pdf_url' in paper:
            pdf_url = paper['pdf_url']
        else:
            pdf_url = paper.get('abs_url', '').replace('/abs/', '/pdf/') + '.pdf'

        html_content += f'''
        <div class="paper-card">
            <div class="paper-header">
                <span class="paper-number">{idx}</span>
                <h2 class="paper-title">
                    <a href="{pdf_url}" target="_blank">{paper['title']}</a>
                </h2>
            </div>
            <p class="paper-authors">{authors_str}</p>
            <div class="paper-summary">{summary}</div>
            <div class="paper-infographic">
                <img src="{image_path}" alt="论文信息图" loading="lazy">
                <br>
                <a href="{pdf_url}" class="original-link" target="_blank">📄 查看原文</a>
            </div>
        </div>
'''

    html_content += f'''
        </div>

        <footer>
            <p>数据来源: arXiv EESS.AS · 生成时间: {today}</p>
            <p>使用 NotebookLM 自动生成信息图表</p>
        </footer>
    </div>
</body>
</html>
'''

    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML 日报已生成: {HTML_OUTPUT}")
    print(f"包含论文数: {len(papers)} 篇")
    return True


if __name__ == '__main__':
    generate_html()
