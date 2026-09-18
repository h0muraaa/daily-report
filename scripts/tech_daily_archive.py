#!/usr/bin/env python3
"""科技日报归档工具

把 tech-daily/*.html 归档到 tech-daily/archive/<YYYY-MM-DD>/，并维护
tech-daily/archive/history.json 供主页做历史回溯。

同时把历史入口注入到页面里（纯 HTML，无 JS）：
- 角色选择页 tech-daily/index.html 顶部：「📅 历史日报」折叠列表，点日期跳当天归档。
- 每个归档页 tech-daily/archive/<date>/index.html 顶部：「← 前一天 / 后一天 →」翻页。

用法:
    python3 scripts/tech_daily_archive.py save     --keep 15   # 工作流每日调用
    python3 scripts/tech_daily_archive.py backfill --keep 15   # 从 git 历史回填

说明:
- 归档日期取自报告内容里内嵌的日期（标题优先），而不是运行器当前时间，
  这样生成失败时只会重复归档旧日期，不会把旧内容错标成今天。
- 清理按目录名的日期排序，不依赖文件 mtime（actions/checkout 会把 mtime 刷成当天，
  `find -mtime` 类逻辑在 CI 中不可靠）。
- 两个入口都由本脚本按标签 <!-- history-nav:start/end --> 生成，不依赖客户端 fetch，
  因此断网/禁用 JS 也能跳转；标签丢失时会告警并尝试重新插入，不会静默失效。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR_NAME = "archive"
INDEX_NAME = "index.html"
HISTORY_NAME = "history.json"

ROLES = (
    "cto_insight",
    "developer_practice",
    "tech_enthusiast",
    "investment_analysis",
    "academic_research",
    "user_research",
)

# 历史日报标题格式不统一，两种写法都要能解析：
#   科技日报 - CTO洞察版 | 2026-06-09
#   科技日报 - CTO洞察版 | 2026年6月8日
DATE_PATTERNS = (
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),
    re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"),
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DATE_DIR_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
CARD_RE = re.compile(r'[ \t]*<article class="card">.*?</article>\n?', re.DOTALL)
CARD_HREF_RE = re.compile(r'href="\./([A-Za-z0-9_]+)\.html"')

# 历史导航块的标签：脚本靠它做幂等替换；缺了会尝试重新插入而不是静默跳过。
NAV_START = "<!-- history-nav:start -->"
NAV_END = "<!-- history-nav:end -->"
HISTORY_NAV_RE = re.compile(re.escape(NAV_START) + r".*?" + re.escape(NAV_END), re.DOTALL)
TITLE_ANCHOR = "<h1>科技日报</h1>"

BANNER_STYLE = """
        .archive-banner {
            text-align: center;
            margin-top: 12px;
            font-size: 1rem;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
            letter-spacing: 0.5px;
        }

        .archive-back {
            display: block;
            width: fit-content;
            margin: 40px auto 0;
            padding: 10px 24px;
            color: white;
            text-decoration: none;
            background: rgba(255, 255, 255, 0.18);
            border-radius: 20px;
            transition: background 0.2s;
        }

        .archive-back:hover { background: rgba(255, 255, 255, 0.3); }
"""


def parse_date(text: str) -> str | None:
    """从一段文本中解析出 YYYY-MM-DD，解析不出来返回 None。"""
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        year, month, day = (int(g) for g in match.groups())
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def extract_date(html: str) -> str | None:
    """先从 <title> 里找日期，找不到再全文兜底。"""
    title_match = TITLE_RE.search(html)
    if title_match:
        date = parse_date(title_match.group(1))
        if date:
            return date
    return parse_date(html)


def fallback_date() -> str:
    """内容里没有日期时的兜底：运行器的 UTC 日期（与 CI 提交日期一致）。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def pick_report_date(contents: dict[str, str]) -> str:
    """多个角色文件取出现次数最多的日期，避免个别文件内容陈旧导致偏移。"""
    dates = [d for d in (extract_date(c) for c in contents.values()) if d]
    if not dates:
        return fallback_date()
    return Counter(dates).most_common(1)[0][0]


def list_dates(archive_dir: Path) -> list[str]:
    """列出已归档的日期目录，降序（最新在前）。"""
    if not archive_dir.is_dir():
        return []
    return sorted(
        (p.name for p in archive_dir.iterdir() if p.is_dir() and DATE_DIR_RE.fullmatch(p.name)),
        reverse=True,
    )


def _short_date(date: str) -> str:
    """2026-09-17 -> 09-17"""
    return date[5:]


def render_history_nav(dates: list[str], current: str | None, prefix: str) -> str:
    """角色选择页顶部的「历史日报」入口：折叠列表 + 日期链接。"""
    chips = []
    for date in dates:
        label = _short_date(date)
        if date == current:
            chips.append(f'<span class="history-chip current">{label}</span>')
        else:
            chips.append(f'<a class="history-chip" href="{prefix}{date}/index.html">{label}</a>')

    return (
        f"{NAV_START}\n"
        f'            <nav class="history-nav">\n'
        f'                <details class="history-details">\n'
        f'                    <summary>📅 历史日报（{len(dates)} 天）</summary>\n'
        f'                    <div class="history-dates">\n'
        f'                        {" ".join(chips)}\n'
        f"                    </div>\n"
        f"                </details>\n"
        f"            </nav>\n"
        f"            {NAV_END}"
    )


def render_archive_nav(dates: list[str], date: str, prefix: str) -> str:
    """归档页顶部的「前一天 / 后一天」翻页入口。dates 为降序（最新在前）。"""
    older = newer = None
    if date in dates:
        index = dates.index(date)
        if index + 1 < len(dates):
            older = dates[index + 1]
        if index > 0:
            newer = dates[index - 1]

    left = (
        f'<a class="history-step" href="{prefix}{older}/index.html">← 前一天</a>'
        if older
        else '<span class="history-step disabled">← 已是最早</span>'
    )
    right = (
        f'<a class="history-step" href="{prefix}{newer}/index.html">后一天 →</a>'
        if newer
        else '<span class="history-step disabled">已是最新 →</span>'
    )

    return (
        f"{NAV_START}\n"
        f'            <nav class="history-nav">\n'
        f'                <div class="history-links">\n'
        f"                    {left}\n"
        f"                    {right}\n"
        f"                </div>\n"
        f"            </nav>\n"
        f"            {NAV_END}"
    )


def build_date_index(template: str, date: str, available: set[str], dates: list[str]) -> str:
    """基于当前的角色选择页生成某个归档日期的 index.html。

    只保留当天真实存在的角色卡片，并注入日期横幅、翻页导航与返回主页链接。
    """
    dropped: list[str] = []

    def keep_card(match: re.Match) -> str:
        card = match.group(0)
        href = CARD_HREF_RE.search(card)
        if href and href.group(1) not in available:
            dropped.append(href.group(1))
            return ""
        return card

    html = CARD_RE.sub(keep_card, template)

    nav = render_archive_nav(dates, date, "../")
    if HISTORY_NAV_RE.search(html):
        html = HISTORY_NAV_RE.sub(lambda _: nav, html, count=1)
    else:
        print("  ⚠️  未找到 history-nav 标签，归档页没有前一天/后一天导航")

    banner = f'<p class="archive-banner">📅 {date} · 历史归档</p>'
    if TITLE_ANCHOR in html:
        html = html.replace(TITLE_ANCHOR, f"{TITLE_ANCHOR}\n                {banner}", 1)
    else:
        print("  ⚠️  未找到 <h1>科技日报</h1> 锚点，跳过日期横幅注入")

    if "</style>" in html:
        html = html.replace("</style>", f"{BANNER_STYLE}    </style>", 1)

    back_link = '<a href="../../../index.html" class="archive-back">← 返回主页</a>\n\n        '
    if "<footer>" in html:
        html = html.replace("<footer>", f"{back_link}<footer>", 1)
    else:
        print("  ⚠️  未找到 <footer> 锚点，跳过返回链接注入")

    if dropped:
        print(f"  ℹ️  当天缺失角色，已从选择页移除: {', '.join(sorted(dropped))}")

    return html


def write_roles(archive_dir: Path, date: str, contents: dict[str, str]) -> None:
    date_dir = archive_dir / date
    date_dir.mkdir(parents=True, exist_ok=True)
    for role, html in contents.items():
        (date_dir / f"{role}.html").write_text(html, encoding="utf-8")


def sync_current_nav(source_dir: Path, template: str | None, dates: list[str]) -> str | None:
    """把「历史日报」入口写回角色选择页，并返回更新后的模板文本。

    必须在生成归档页之前调用 —— 归档页是从这份模板派生的，标签要先进去。
    """
    if template is None or not dates:
        return template

    nav = render_history_nav(dates, dates[0], "./archive/")
    if HISTORY_NAV_RE.search(template):
        updated = HISTORY_NAV_RE.sub(lambda _: nav, template, count=1)
    elif TITLE_ANCHOR in template:
        updated = template.replace(TITLE_ANCHOR, f"{TITLE_ANCHOR}\n            {nav}", 1)
        print("  ℹ️  角色选择页还没有 history-nav 标签，已插入到标题下方")
    else:
        print(f"  ⚠️  角色选择页缺少 {TITLE_ANCHOR} 锚点，历史日报入口未写入")
        return template

    if updated != template:
        (source_dir / INDEX_NAME).write_text(updated, encoding="utf-8")
    return updated


def refresh_indexes(archive_dir: Path, template: str | None, dates: list[str]) -> None:
    """按当前日期列表重新生成每个归档日的 index.html（含翻页导航）。"""
    if template is None:
        return
    for date in dates:
        date_dir = archive_dir / date
        if not date_dir.is_dir():
            continue
        available = {p.stem for p in date_dir.glob("*.html") if p.stem in ROLES}
        (date_dir / INDEX_NAME).write_text(
            build_date_index(template, date, available, dates), encoding="utf-8"
        )


def prune(archive_dir: Path, keep: int) -> list[str]:
    removed = []
    for date in list_dates(archive_dir)[keep:]:
        shutil.rmtree(archive_dir / date)
        removed.append(date)
    return removed


def write_history(archive_dir: Path) -> list[str]:
    dates = list_dates(archive_dir)
    payload = {"dates": dates}
    history_path = archive_dir / HISTORY_NAME
    # dates 未变则不动文件，避免每天产生无意义的 git 变更
    if history_path.is_file():
        try:
            if json.loads(history_path.read_text(encoding="utf-8")) == payload:
                return dates
        except json.JSONDecodeError:
            pass
    archive_dir.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return dates


def read_template(source_dir: Path) -> str | None:
    template_path = source_dir / INDEX_NAME
    if not template_path.is_file():
        print(f"  ⚠️  未找到角色选择页模板 {template_path}，归档目录将没有 index.html")
        return None
    return template_path.read_text(encoding="utf-8")


def load_current_reports(source_dir: Path) -> dict[str, str]:
    """读取当前 tech-daily 下最新一期的角色 HTML。"""
    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in sorted(source_dir.glob("*.html"))
        if path.name != INDEX_NAME and path.stem in ROLES
    }


def git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args), cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout


def collect_from_history(source_dir: Path, want: int) -> dict[str, dict[str, str]]:
    """从 git 历史里按日期由新到旧收集归档内容，攒够 want 个日期为止。"""
    rel = source_dir.relative_to(REPO_ROOT).as_posix()
    paths = [f"{rel}/{role}.html" for role in ROLES]
    commits = git("log", "--all", "--format=%H", "--", *paths).split()

    collected: dict[str, dict[str, str]] = {}
    for commit in commits:
        contents = {}
        for role in ROLES:
            result = subprocess.run(
                ("git", "show", f"{commit}:{rel}/{role}.html"),
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                contents[role] = result.stdout
        if not contents:
            continue

        date = pick_report_date(contents)
        if date in collected:
            continue
        collected[date] = contents
        print(f"  ✓ {date}  ({len(contents)} 个角色, {commit[:8]})")

        if len(collected) >= want:
            break

    return collected


def cmd_save(args: argparse.Namespace) -> int:
    source_dir = Path(args.src).resolve()
    archive_dir = source_dir / ARCHIVE_DIR_NAME

    contents = load_current_reports(source_dir)
    if not contents:
        print(f"⚠️  {source_dir} 下没有找到角色 HTML，跳过归档")
        return 0

    date = pick_report_date(contents)
    print(f"📦 归档 {date}（{len(contents)} 个角色）→ {archive_dir / date}")
    write_roles(archive_dir, date, contents)

    for removed in prune(archive_dir, args.keep):
        print(f"  🗑️  清理超过 {args.keep} 天的归档: {removed}")

    dates = write_history(archive_dir)
    # 先补当前页的入口（拿到带标签的模板），再据此生成归档页的翻页导航
    template = sync_current_nav(source_dir, read_template(source_dir), dates)
    refresh_indexes(archive_dir, template, dates)
    print(f"✅ 归档完成，当前共 {len(dates)} 天: {', '.join(dates)}")
    return 0


def cmd_backfill(args: argparse.Namespace) -> int:
    source_dir = Path(args.src).resolve()
    archive_dir = source_dir / ARCHIVE_DIR_NAME
    template = read_template(source_dir)

    print(f"🔍 从 git 历史回填最近 {args.keep} 天到 {archive_dir}")
    collected = collect_from_history(source_dir, args.keep)
    if not collected:
        print("⚠️  git 历史里没有找到可回填的科技日报")
        return 1

    for date, contents in collected.items():
        write_roles(archive_dir, date, contents)

    for removed in prune(archive_dir, args.keep):
        print(f"  🗑️  清理超过 {args.keep} 天的归档: {removed}")

    dates = write_history(archive_dir)
    template = sync_current_nav(source_dir, template, dates)
    refresh_indexes(archive_dir, template, dates)
    print(f"✅ 回填完成，当前共 {len(dates)} 天: {', '.join(dates)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="科技日报归档工具")
    parser.add_argument("mode", choices=("save", "backfill"), help="save=归档当前报告, backfill=从 git 历史回填")
    parser.add_argument("--keep", type=int, default=15, help="保留最近多少天（默认 15）")
    parser.add_argument("--src", default="tech-daily", help="日报目录（默认 tech-daily）")
    args = parser.parse_args()

    if args.keep < 1:
        print("❌ --keep 必须 >= 1")
        return 1

    try:
        return cmd_save(args) if args.mode == "save" else cmd_backfill(args)
    except subprocess.CalledProcessError as exc:
        print(f"❌ git 命令失败: {exc.stderr or exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
