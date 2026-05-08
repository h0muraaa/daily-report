#!/usr/bin/env python3
"""Generate developer practice daily tech report from JSON news data."""

import json
import re
from datetime import datetime
from html import escape

# Read JSON
with open("./tech-daily/freshrss_24h_compact_20260508_190119.json", "r", encoding="utf-8") as f:
    data = json.load(f)

articles = data.get("articles", [])
print(f"Total articles: {len(articles)}")

# Developer-relevant keywords and patterns
DEV_KEYWORDS = {
    # Tools & frameworks
    "cli", "docker", "kubernetes", "k8s", "git", "github", "vscode", "ide",
    "framework", "library", "sdk", "api", "database", "postgres", "sql", "nosql",
    "react", "vue", "angular", "svelte", "nextjs", "nuxt", "typescript", "javascript",
    "python", "rust", "go", "golang", "java", "kotlin", "swift", "c++", "wasm",
    "tensorflow", "pytorch", "huggingface", "langchain", "llm", "model",
    "serverless", "lambda", "cloud", "aws", "gcp", "azure", "terraform",
    "ci/cd", "pipeline", "deployment", "testing", "benchmark",
    "kernel", "cuda", "gpu", "sparse", "transformer", "vision", "cnn",
    "debug", "debugger", "profiling", "performance", "optimization",
    "coding agent", "codex", "claude code", "gemini cli", "mcp server",
    "open source", "github", "repository", "commit", "pull request",
    "vulnerability", "cve", "security", "exploit", "bug", "patch",
    "architecture", "design pattern", "microservices", "monolith",
    "observability", "monitoring", "logging", "tracing",
}

EXCLUDE_PATTERNS = [
    r"political\s+terrorism",
    r"\bdead\s+yet\b",
    r"decline\s+of\s+OpenAI",
    r"\bslop\b",
    r"i wish i could fast forward",
    r"Heart, full",
    r"^Tweet$",
    r"Another example$",
    r"Yup$",
    r"Sweet!$",
    r"Just gonna leave this here",
    r"\bHR\b.*\bAI\b",
    r"books,\s+even\s+from\s+authors",
    r"Ocean.*rain.*tap\s+water",
]

EXCLUDE_FEEDS = [
    "Dwarkesh Patel",
    "PowerfulJRE",
    "Greg Isenberg",
]

def is_dev_relevant(article):
    """Check if article is relevant to developers."""
    title = article.get("title", "")
    summary = article.get("summary", "")
    feed_title = article.get("feed_title", "")
    text = (title + " " + summary).lower()

    # Exclude non-dev feeds
    if any(feed in feed_title for feed in EXCLUDE_FEEDS):
        return False

    # Exclude patterns
    for pattern in EXCLUDE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE) or re.search(pattern, summary, re.IGNORECASE):
            return False

    # Check for dev keywords
    if any(kw in text for kw in DEV_KEYWORDS):
        return True

    # Specific tech sources are usually dev-relevant
    tech_sources = ["Hugging Face", "Cloud Blog", "LangChain", "NVIDIA AI",
                    "DeepLearning.AI", "Google Gemini", "OpenAI", "GitHub"]
    if any(src in feed_title for src in tech_sources):
        # But still filter out purely social/promotional tweets
        if len(summary) < 50 and ("💬" in summary or "❤️" in summary or "👀" in summary):
            return False
        return True

    return False

def score_article(article):
    """Score article by developer value."""
    score = 0
    title = article.get("title", "")
    summary = article.get("summary", "")
    feed_title = article.get("feed_title", "")
    text = title + " " + summary

    # Length indicates depth
    if len(summary) > 300:
        score += 3
    elif len(summary) > 150:
        score += 2
    elif len(summary) > 80:
        score += 1
    else:
        score -= 2  # Penalize very short content

    # Technical depth signals
    depth_signals = ["CVE-", "benchmark", "kernel", "CUDA", "architecture",
                     "deployment", "pipeline", "performance", "optimization",
                     "debugger", "testing", "open source", "repository"]
    for sig in depth_signals:
        if sig.lower() in text.lower():
            score += 2

    # Tool/framework mentions
    tool_signals = ["CLI", "VS Code", "Docker", "Kubernetes", "GitHub",
                    "LangChain", "Hugging Face", "Codex", "Gemini CLI"]
    for sig in tool_signals:
        if sig.lower() in text.lower():
            score += 1

    # Penalize pure social media engagement metrics
    if "💬0🔄0❤️" in summary or "⚡ Powered by xgo" in summary and len(summary) < 100:
        score -= 3

    # Boost technical blog posts
    if any(src in feed_title for src in ["Cloud Blog", "Hugging Face", "NVIDIA", "DeepLearning.AI"]):
        score += 2

    return score

# Filter and score
filtered = [(a, score_article(a)) for a in articles if is_dev_relevant(a)]
filtered.sort(key=lambda x: x[1], reverse=True)

# Print top candidates for manual review
print("\n=== Top 30 filtered articles ===")
for i, (a, score) in enumerate(filtered[:30]):
    print(f"\n[{score}] {a.get('title', '')[:80]}")
    print(f"    Source: {a.get('feed_title', '')}")
    print(f"    Summary: {a.get('summary', '')[:120]}...")
