#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
KAF v5.7 · P0-1 会话启动注入器 (bootstrap)
============================================
对标：obra/superpowers 的 SessionStart hook —— 它把 `using-superpowers` bootstrap
在**会话启动时注入，并在 compaction 之后再注入一次**，从不依赖 agent 记得去调用。

KAF 的教训（2026-10-07 实证）：反模式库 34 条、经验库 44 条，但
**10-06 全天零调用、联动率曾 0%** —— 库再全，没有自动触发就是坟场。

本脚本把「检索注入」从「agent 记得才做」变成「一条命令必产出」，
并可被任意平台的 hook 直接调用（stdout 即注入内容）。

产出三段：
  1. 脊柱体检（条数 / 联动率 / 上次蒸馏距今）
  2. **陈旧告警**（联动率 <80% 或 上次 compound 超过阈值 → 醒目标记）
  3. 历史反模式注入块（接 retrieval_inject.build_injection）

用法
----
  python kaf_bootstrap.py --task "git push 失败 排查网络"
  python kaf_bootstrap.py --task "删除残留目录" --json     # 机器可读
  python kaf_bootstrap.py --task "..." --strict            # 有告警则 exit 2（供 hook/CI 阻断）

平台接入（5 行）
----------------
  Claude Code / Codex: SessionStart hook 调本脚本，stdout 前缀注入
  WorkBuddy 等无 hook 平台: 由 agent 在任务起点强制调用（见 SKILL.md §0）
"""
import os
import sys
import json
import argparse
import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)  # 子包目录最高优先（AP: sys.path 根目录高于子包）

import retrieval_inject as RI  # noqa: E402
import experience_distillation as ED  # noqa: E402

AP_PATH = os.path.join(_HERE, "anti_patterns.jsonl")
EXP_PATH = os.path.join(_HERE, "experience.jsonl")
STATE_PATH = os.path.join(_HERE, ".spine_state.json")

LINK_RATE_MIN = 0.80      # 联动率阈值
STALE_DAYS = 1            # 上次 compound 超过 N 天即告警


def _read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if s:
                try:
                    out.append(json.loads(s))
                except Exception:
                    pass
    return out


def load_state():
    if not os.path.exists(STATE_PATH):
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def link_rate(aps, exps):
    """反模式→经验 联动率：按 right 前 32 字精确匹配经验 action。"""
    if not aps:
        return 0.0, []
    acts = ["".join((e.get("action", "") or "").split()) for e in exps]
    hit, miss = 0, []
    for o in aps:
        core = "".join((o.get("right", "") or "").split())[:32]
        if core and any(core in a for a in acts):
            hit += 1
        else:
            miss.append(o.get("id", "?"))
    return hit / len(aps), miss


def main():
    ap = argparse.ArgumentParser(description="KAF 会话启动注入器")
    ap.add_argument("--task", default="", help="当前任务描述（用于反模式检索）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    ap.add_argument("--strict", action="store_true",
                    help="存在告警时 exit 2（供 hook/CI 阻断）")
    a = ap.parse_args()

    aps = _read_jsonl(AP_PATH)
    exps = _read_jsonl(EXP_PATH)
    rate, miss = link_rate(aps, exps)
    state = load_state()

    # 上次 compound 距今
    stale_days = None
    last = state.get("last_compound")
    if last:
        try:
            t0 = datetime.datetime.fromisoformat(last)
            stale_days = (datetime.datetime.now() - t0).total_seconds() / 86400.0
        except Exception:
            stale_days = None

    warn = []
    if rate < LINK_RATE_MIN:
        warn.append("联动率 %.0f%% < %.0f%%：%d 条反模式未转成经验，跑 `kaf_compound.py` 补" %
                    (rate * 100, LINK_RATE_MIN * 100, len(miss)))
    if stale_days is None:
        warn.append("从未执行过收尾蒸馏（无 %s），跑 `python kaf_compound.py`" %
                    os.path.basename(STATE_PATH))
    elif stale_days > STALE_DAYS:
        warn.append("距上次收尾蒸馏已 %.1f 天（阈值 %d 天），跑 `python kaf_compound.py`" %
                    (stale_days, STALE_DAYS))

    inj = RI.build_injection(a.task, k=5) if a.task else ""

    if a.json:
        print(json.dumps({
            "anti_patterns": len(aps),
            "experiences": len(exps),
            "link_rate": round(rate, 4),
            "unlinked": miss,
            "last_compound": last,
            "stale_days": (round(stale_days, 2) if stale_days is not None else None),
            "warnings": warn,
            "injection": inj,
        }, ensure_ascii=False, indent=2))
        return 2 if (warn and a.strict) else 0

    # 人类可读（三段）
    print("=== KAF 进智脊柱 · 启动注入 ===")
    print("反模式 %d 条 · 经验 %d 条 · 联动率 %.0f%%" % (len(aps), len(exps), rate * 100))
    print("上次收尾蒸馏：%s" % (last or "（从未）"))
    print()
    if warn:
        print("!! 告警（必做未完成）")
        for w in warn:
            print("   - %s" % w)
        print()
    else:
        print("脊柱状态正常")
        print()
    if inj:
        print(inj)
    elif a.task:
        print("（本次任务未命中历史反模式；库语料仍偏斜时检索不到≠没风险）")
    return 2 if (warn and a.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
