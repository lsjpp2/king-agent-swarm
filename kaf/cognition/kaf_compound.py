#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
KAF v5.7 · P0-2 会话收尾蒸馏器 (compound)
============================================
对标：EveryInc/compound-engineering-plugin 六步循环的第 6 步 `/ce-compound`
—— 它把经验写进 `docs/solutions/`，**下一轮 brainstorm/plan 必读**，作者原话
"That return arrow is the whole point"。

KAF 原状：distill 是**可选的**（想起来才跑）→ 实证联动率曾 **0%**。
本脚本把它变成**循环里的一步**：跑完就打时间戳，`kaf_bootstrap.py`
下次启动会检查这个时间戳，超时即告警（陈旧检测形成闭环）。

子命令
------
  run      --log <日志路径> [--out <报告>] [--commit]
           挖候选经验（半自动，只出清单不自动灌库）+ 生成收尾报告
           **不加 --commit 则不更新时间戳**（避免"跑了但没真沉淀"就消掉告警）
  record   --context .. --action .. [--outcome success] [--confidence 0.8] [--source ..]
           单条经验入账（接 experience_distillation.add_experience，判重幂等）
  status   显示上次收尾时间与陈旧状态

设计原则
--------
  * **半自动而非全自动**：自动把日志噪声灌进经验库会造成污染（AP031 类）。
    挖出的候选必须人工审后再 record。
  * **只有 --commit 才消告警**：强制"真沉淀"才算数。
  * 无硬编码本机路径，日志/报告路径均由参数传入（可公开发布）。

用法
----
  python kaf_compound.py run --log <当日日志.md> --commit
  python kaf_compound.py record --context "沙箱 git push 报 CONNECT 502" \
         --action "git -c http.proxy= -c https.proxy= push" --confidence 0.95
  python kaf_compound.py status
"""
import os
import sys
import json
import argparse
import datetime
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

_spec = importlib.util.spec_from_file_location(
    "experience_distillation", os.path.join(_HERE, "experience_distillation.py"))
ED = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ED)

EXP_PATH = os.path.join(_HERE, "experience.jsonl")
STATE_PATH = os.path.join(_HERE, ".spine_state.json")

MINE_KEYS = ["根因", "真因", "破法", "实证", "坑", "错误", "修复", "失败", "解决",
             "教训", "注意", "铁律", "⚠️", "★", "→", "WARNING", "root cause"]


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


def save_state(d):
    old = load_state()
    old.update(d)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(old, f, ensure_ascii=False, indent=2)


def cmd_status(a):
    st = load_state()
    last = st.get("last_compound")
    print("上次收尾蒸馏：%s" % (last or "（从未执行）"))
    if last:
        try:
            t0 = datetime.datetime.fromisoformat(last)
            d = (datetime.datetime.now() - t0).total_seconds() / 86400.0
            print("距今：%.2f 天" % d)
            print("状态：%s" % ("✅ 新鲜" if d <= 1 else "⚠️ 已陈旧，需跑 `run --commit`"))
        except Exception:
            print("（时间戳解析失败）")
    print("累计收尾次数：%s" % st.get("compound_count", 0))
    print("经验库：%d 条" % len(_read_jsonl(EXP_PATH)))


def cmd_run(a):
    if not os.path.exists(a.log):
        print("FATAL: 日志不存在 -> %s" % a.log, file=sys.stderr)
        return 2
    text = open(a.log, "r", encoding="utf-8", errors="replace").read()
    cands = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s:
            continue
        if not any(k in s for k in MINE_KEYS):
            continue
        body = s.lstrip("-*>#| ").strip()
        if len(body) < 20:
            continue
        cands.append({
            "context": body[:80],
            "action": body,
            "outcome": "success",
            "confidence": 0.5,
            "source": "compound-mine %s" % os.path.basename(a.log),
            "_raw": body[:200],
        })

    before = len(_read_jsonl(EXP_PATH))
    print("== 收尾蒸馏 ==")
    print("日志：%s (%d B)" % (a.log, len(text.encode("utf-8"))))
    print("候选：**%d** 条（半自动，需人工审后再 record，勿批量灌）" % len(cands))
    print()
    for c in cands[:15]:
        print("  • %s" % c["_raw"][:110])
    if len(cands) > 15:
        print("  ...(共 %d 条)" % len(cands))

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            for c in cands:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print("\n候选已写入：%s" % a.out)

    if a.commit:
        st = load_state()
        save_state({
            "last_compound": datetime.datetime.now().isoformat(timespec="seconds"),
            "compound_count": st.get("compound_count", 0) + 1,
            "last_candidates": len(cands),
            "last_log": os.path.basename(a.log),
        })
        print("\n✅ 已打时间戳（陈旧告警解除）· 累计收尾 %d 次" %
              (st.get("compound_count", 0) + 1))
    else:
        print("\n⚠️ 未加 --commit：时间戳未更新，下次 bootstrap 仍会告警。"
              "\n   只有真的沉淀了（record 过）才应加 --commit。")
    print("经验库：%d → %d 条" % (before, len(_read_jsonl(EXP_PATH))))
    return 0


def cmd_record(a):
    exps = _read_jsonl(EXP_PATH)
    have = {e["ctx_key"] for e in exps}
    if ED._ctx_key(a.context) in have:
        print("⚠️ 已存在同类经验（ctx_key 命中），跳过以避免重复行。")
        print("   如需提升置信度，请直接编辑 experience.jsonl 的 confidence 字段。")
        for e in ED.get_by_context(a.context):
            print("   现有：conf=%s reviews=%s" % (e.get("confidence"), e.get("reviews")))
        return 0
    ED.add_experience(a.context, a.action, a.outcome,
                      confidence=a.confidence, source=a.source)
    print("✅ 已入账：%s" % a.context[:60])
    print("   经验库现 %d 条" % len(_read_jsonl(EXP_PATH)))
    print("   提示：确认沉淀后跑 `run --log <日志> --commit` 打时间戳。")
    return 0


def main():
    ap = argparse.ArgumentParser(description="KAF 会话收尾蒸馏器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="挖候选 + 打时间戳")
    r.add_argument("--log", required=True)
    r.add_argument("--out")
    r.add_argument("--commit", action="store_true",
                   help="确认真沉淀后才更新时间戳（消告警）")
    r.set_defaults(fn=cmd_run)

    rc = sub.add_parser("record", help="单条经验入账（判重幂等）")
    rc.add_argument("--context", required=True)
    rc.add_argument("--action", required=True)
    rc.add_argument("--outcome", default="success",
                    choices=["success", "fail", "partial"])
    rc.add_argument("--confidence", type=float, default=0.8)
    rc.add_argument("--source", default="")
    rc.set_defaults(fn=cmd_record)

    sub.add_parser("status", help="上次收尾与陈旧状态").set_defaults(fn=cmd_status)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
