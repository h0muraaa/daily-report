#!/usr/bin/env python3
"""Filter tech news JSON for investment-relevant articles."""
import json
import re
from pathlib import Path

INPUT = Path("/home/runner/work/daily-report/daily-report/tech-daily/freshrss_24h_compact_20260708_190152.json")
OUTPUT = Path("/home/runner/work/daily-report/daily-report/.claude/skills/tech-daily-generator/investment_candidates.json")

# Positive keywords: funding, M&A, IPO, earnings, market moves, business model
POSITIVE = [
    r"\bfunding\b", r"\bfinanc\w+", r"\braised\b", r"\bseries\s+[a-z]\b", r"\bvaluation\b",
    r"\bacquir\w+", r"\bmerger\b", r"\bipo\b", r"\bpublic\b", r"\bearnings\b", r"\brevenue\b",
    r"\barr\b", r"\bprofit\b", r"\bloss\b", r"\bquarter\b", r"\bgrowth\b", r"\binvest\w+",
    r"\bvc\b", r"\bventure\b", r"\bcapital\b", r"\bprivate\s+equity\b", r"\bbuyout\b",
    r"\bstock\b", r"\bshare\b", r"\bmarket\s+cap\b", r"\btrading\b", r"\bnasdaq\b", r"\bnyse\b",
    r"\bbillion\b", r"\bmillion\b", r"\$\d+", r"\bpriced\b", r"\bsubscription\b",
    r"\bcommercial\b", r"\benterprise\b", r"\bcustomer\b", r"\bpartnership\b", r"\bdeal\b",
    r"\blayoff\b", r"\bworkforce\b", r"\bexpansion\b", r"\bscale\b", r"\bgm\b", r"\bmargin\b"
]

# Negative keywords: pure tutorials, code details, personal posts
NEGATIVE = [
    r"\btutorial\b", r"\bhow\s+to\b", r"\bguide\b", r"\bstep[-\s]by[-\s]step\b", r"\bcoding\b",
    r"\bcode\b", r"\bgit\b", r"\bgithub\b", r"\bdeveloper\b", r"\bapi\b", r"\bsdk\b",
    r"\bhiring\b", r"\bjob\b", r"\bcareer\b", r"\bresume\b", r"\bpodcast\b", r"\blivestream\b",
    r"\bgiveaway\b", r"\bsocks\b", r"\btshirt\b", r"\bfree\s+tee\b"
]

pos_re = [re.compile(p, re.I) for p in POSITIVE]
neg_re = [re.compile(p, re.I) for p in NEGATIVE]

with INPUT.open("r", encoding="utf-8") as f:
    data = json.load(f)

articles = data.get("articles", [])
scored = []
for a in articles:
    text = " ".join([a.get("title", ""), a.get("summary", ""), a.get("feed_title", "")])
    pos_score = sum(1 for r in pos_re if r.search(text))
    neg_score = sum(1 for r in neg_re if r.search(text))
    if pos_score > 0 and neg_score < 3:
        scored.append({
            "title": a.get("title", ""),
            "link": a.get("link", ""),
            "feed_title": a.get("feed_title", ""),
            "author": a.get("author", ""),
            "summary": a.get("summary", ""),
            "score": pos_score - neg_score * 0.5
        })

scored.sort(key=lambda x: x["score"], reverse=True)
selected = scored[:40]

with OUTPUT.open("w", encoding="utf-8") as f:
    json.dump(selected, f, ensure_ascii=False, indent=2)

print(f"Total articles: {len(articles)}")
print(f"Candidates: {len(scored)}")
print(f"Selected top {len(selected)} saved to {OUTPUT}")
