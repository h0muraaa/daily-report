#!/usr/bin/env python3
"""arXiv 图片保留策略工具

删除 arxiv-daily/images/ 下超过 N 天的旧图片，让 arXiv 日报的图片最多保留 7 天。

用法:
    python3 scripts/arxiv_prune_images.py --keep-days 7            # 工作流每日调用
    python3 scripts/arxiv_prune_images.py --keep-days 7 --dry-run  # 只看会删哪些

说明:
- 日期取自文件名里的 `paper_<ID>_<YYYYMMDD>.jpg` 后缀，**不依赖文件 mtime**。
  工作流里的 `actions/checkout` 会把所有文件 mtime 刷成当天，`find -mtime +3`
  永远命中不了——这正是图片 5 个月来一张都没删掉的原因。
- 若目录里确实有 .jpg 却一个都解析不出日期，脚本会**报错并返回非 0**，
  而不是静默什么都不删。宁可让工作流红掉，也不要再来一次「静默失效」。
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = "arxiv-daily/images"

# paper_2604.05519_20260412.jpg -> 2026-04-12
FILENAME_DATE_RE = re.compile(r"_(\d{8})\.jpg$", re.IGNORECASE)


def parse_date(name: str) -> str | None:
    """从文件名解析出 YYYY-MM-DD，解析不出来返回 None。"""
    match = FILENAME_DATE_RE.search(name)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return None


def prune(images_dir: Path, keep_days: int, dry_run: bool) -> int:
    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=keep_days)

    jpgs = sorted(p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() == ".jpg")
    if not jpgs:
        print(f"ℹ️  {images_dir} 下没有图片，无需清理")
        return 0

    dated = [(p, parse_date(p.name)) for p in jpgs]
    undated = [p for p, date in dated if date is None]
    if undated:
        print(f"❌ {len(undated)}/{len(jpgs)} 个图片的文件名解析不出日期，例如：")
        for path in undated[:5]:
            print(f"     {path.name}")
        print(f"   预期命名格式: paper_<ID>_<YYYYMMDD>.jpg")
        return 1

    expired = [p for p, date in dated if date < cutoff.isoformat()]
    kept = len(jpgs) - len(expired)

    action = "将删除" if dry_run else "删除"
    print(f"🗓️  今天(UTC) {today}，保留 {keep_days} 天（{cutoff} 及以后）")
    print(f"📦 共 {len(jpgs)} 张，保留 {kept} 张，{action} {len(expired)} 张")

    for path, date in dated:
        if date < cutoff.isoformat():
            if dry_run:
                print(f"  [dry-run] {date}  {path.name}")
            else:
                path.unlink()
                print(f"  🗑️  {date}  {path.name}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="arXiv 图片保留策略工具")
    parser.add_argument("--keep-days", type=int, default=7, help="保留最近多少天（默认 7）")
    parser.add_argument("--dir", default=DEFAULT_DIR, help=f"图片目录（默认 {DEFAULT_DIR}）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不真正删除")
    args = parser.parse_args()

    if args.keep_days < 1:
        print("❌ --keep-days 必须 >= 1")
        return 1

    images_dir = Path(args.dir)
    if not images_dir.is_absolute():
        images_dir = REPO_ROOT / images_dir
    if not images_dir.is_dir():
        print(f"❌ 图片目录不存在: {images_dir}")
        return 1

    return prune(images_dir, args.keep_days, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
