#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取 GitHub 上「多智能体编排 / 蜂群治理 / agent 框架」类仓库真实热度榜 (按 star 排序)。

策略:
- 用多个针对性查询 (topic + 关键词) 覆盖该领域, 合并去重
- 过滤 awesome-list / 教程 / 路线图 / 纯 chatbot demo 等非框架同类项
- 按 star 降序取前 N
输出 JSON 到同目录 top_repos.json
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(OUT_DIR, "top_repos.json")

# 多个查询: 覆盖 multi-agent / swarm / orchestration / agent-framework 等领域
QUERIES = [
    "topic:multi-agent",
    "topic:ai-agents",
    "topic:agent-framework",
    "topic:llm-agent",
    "topic:autonomous-agents",
    "topic:agentic-framework",
    "multi-agent+framework",
    "agent+swarm",
    "agent+orchestration",
    "multi-agent+system",
]

# 非框架 / 非同类项过滤词 (名称或描述命中即排除)
NON_FRAMEWORK = [
    "awesome", "tutorial", "cheat-sheet", "cheatsheet", "roadmap",
    "interview", "book", "course", "bootcamp", "list-of", "learning",
    "examples-only", "demo-only", "paper", "survey", "collection",
    "resource-list", "notes", "guide-only",
]


def is_non_framework(name, desc):
    text = (name + " " + (desc or "")).lower()
    # 排除明显是"列表/教程"的仓库
    for w in NON_FRAMEWORK:
        if w in text:
            return True
    # 排除纯 chatbot 包装 (描述里几乎没有编排/框架语义)
    if ("chatbot" in text or "chat bot" in text) and "framework" not in text and "orchestrat" not in text and "multi-agent" not in text:
        return True
    return False


def github_get(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "kaf-research/1.0",
        "Accept": "application/vnd.github+json",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 403:
                # 可能是速率限制
                print(f"  [WARN] 403 on {url}: {e}", file=sys.stderr)
                time.sleep(3)
                continue
            print(f"  [ERR] {e.code} on {url}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"  [ERR] {e} on {url}", file=sys.stderr)
            time.sleep(2)
    return None


def main():
    seen = {}
    for q in QUERIES:
        url = (f"https://api.github.com/search/repositories"
               f"?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=30")
        print(f"[QUERY] {q}")
        data = github_get(url)
        if not data or "items" not in data:
            print(f"  -> no items", file=sys.stderr)
            continue
        for it in data["items"]:
            fn = it["full_name"]
            if fn in seen:
                # 取较高 star 记录
                if it["stargazers_count"] > seen[fn]["stargazers_count"]:
                    seen[fn] = it
                continue
            seen[fn] = it
        time.sleep(1)  # 降低速率压力

    repos = list(seen.values())
    # 过滤非框架
    filtered = [r for r in repos if not is_non_framework(r["name"], r.get("description") or "")]
    # 排序
    filtered.sort(key=lambda r: r["stargazers_count"], reverse=True)

    print(f"\n[STATS] 原始去重后 {len(repos)} 个, 过滤后 {len(filtered)} 个")
    print("\n=== TOP 25 (按 star) ===")
    for i, r in enumerate(filtered[:25], 1):
        print(f"{i:2d}. {r['stargazers_count']:>7}★  {r['full_name']}")
        if r.get("description"):
            print(f"     {r['description'][:120]}")

    # 保存前 30 供深读
    out = [{
        "rank": i + 1,
        "full_name": r["full_name"],
        "name": r["name"],
        "stars": r["stargazers_count"],
        "forks": r.get("forks_count"),
        "language": r.get("language"),
        "description": r.get("description"),
        "homepage": r.get("homepage"),
        "url": r["html_url"],
        "pushed_at": r.get("pushed_at"),
        "topics": r.get("topics", []),
    } for i, r in enumerate(filtered[:30])]
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved] {OUT_FILE} (top {len(out)})")


if __name__ == "__main__":
    import urllib.parse
    main()
