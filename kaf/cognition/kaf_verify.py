#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
KAF v5.7 · P0-3 交付验收门禁 (verification-before-completion)
================================================================
对标：obra/superpowers 的 `verification-before-completion` skill ——
"Ensure it's actually fixed"，并继承 `systematic-debugging` 的 Iron Law：
**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST**。

KAF 实证教训（AP031，2026-10-06）：交付了一个 `start_silent.vbs` 就说「已修复，
你双击即可」，自己从未运行 —— 里面同时存在三处致命缺陷（pythonw 下 print()
静默杀进程 / fso 未 Set 编译报错 / 中文路径 ANSI 乱码），**任一存在双击都不会启动**。

本脚本把「交付前验收」变成**会失败的命令**：
  无实跑证据 → exit 2；证据是空/占位/推测措辞 → exit 2。

用法
----
  python kaf_verify.py --claim "后端已启动" --evidence-cmd "netstat -ano | findstr :8787"
  python kaf_verify.py --claim "API 返回真实数据" --evidence-file out.txt
  python kaf_verify.py --claim "..." --evidence-cmd "..." --expect "LISTENING"
  python kaf_verify.py --list                       # 查看历史验收记录

判定规则
--------
  1. 必须提供 --evidence-cmd 或 --evidence-file（二者至少其一）
  2. 命令退出码必须为 0；输出必须非空（去掉空白后 > 0 字符）
  3. 输出不得只含推测措辞（应该/可能/大概/should/maybe/probably）
  4. 若给 --expect，输出必须包含该子串
  5. PASS 才允许对国王说「已修复」；FAIL 必须说明缺什么

通过的结果写入 `.verify_log.jsonl`（可审计，含时间戳与证据摘要）。
"""
import os
import sys
import json
import argparse
import subprocess
import datetime

_HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(_HERE, ".verify_log.jsonl")

SPECULATIVE = ["应该", "可能", "大概", "也许", "估计", "似乎是",
               "should", "maybe", "probably", "likely", "presumably"]
PLACEHOLDER_OK = ["ok", "okay", "done", "完成", "好了", "没问题"]


def _append_log(rec):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _judge(out, rc, expect):
    """返回 (ok, reason)。"""
    if rc != 0:
        return False, "证据命令退出码 %d（非 0）" % rc
    s = (out or "").strip()
    if not s:
        return False, "证据输出为空 —— 「跑完就算」不算验证"
    low = s.lower()
    if len(s) < 8 and low in PLACEHOLDER_OK:
        return False, "证据是占位措辞（%r），不是实跑输出" % s[:20]
    if any(w in low for w in SPECULATIVE) and len(s) < 40:
        return False, "证据含推测措辞且过短，不是实测结果"
    if expect and expect not in s:
        return False, "证据输出未包含期望子串 %r" % expect
    return True, ""


def cmd_list(a):
    if not os.path.exists(LOG_PATH):
        print("（无验收记录）")
        return 0
    n = 0
    for ln in open(LOG_PATH, "r", encoding="utf-8"):
        s = ln.strip()
        if not s:
            continue
        try:
            r = json.loads(s)
        except Exception:
            continue
        n += 1
        print("[%s] %s | %s" % (r.get("ts", "?")[:19],
                                r.get("verdict", "?"),
                                (r.get("claim") or "")[:60]))
    print("\n共 %d 条" % n)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="KAF 交付验收门禁（无实跑证据不许说「已修复」）")
    ap.add_argument("--claim", help="你打算主张什么（如「后端已启动」）")
    ap.add_argument("--evidence-cmd", help="实跑验证命令（stdout 作为证据）")
    ap.add_argument("--evidence-file", help="证据文件路径（已有输出）")
    ap.add_argument("--expect", help="证据中必须包含的子串")
    ap.add_argument("--list", action="store_true", help="查看历史验收记录")
    a = ap.parse_args()

    if a.list:
        return cmd_list(a)

    if not a.claim:
        print("FATAL: 必须 --claim 说明你打算主张什么", file=sys.stderr)
        return 2
    if not a.evidence_cmd and not a.evidence_file:
        print("FAIL: 主张「%s」但未提供任何实跑证据。" % a.claim)
        print("      用法：--evidence-cmd \"<命令>\" 或 --evidence-file <路径>")
        print("      规则：交付前必须实跑并看到预期结果（AP031）")
        _append_log({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                     "claim": a.claim, "verdict": "FAIL",
                     "reason": "no evidence provided"})
        return 2

    if a.evidence_cmd:
        try:
            p = subprocess.run(a.evidence_cmd, shell=True, capture_output=True,
                               text=True, timeout=60)
            out, rc = (p.stdout or "") + (p.stderr or ""), p.returncode
        except Exception as e:
            print("FAIL: 证据命令执行异常：%s" % e)
            _append_log({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                         "claim": a.claim, "verdict": "FAIL",
                         "reason": "cmd exception: %s" % e})
            return 2
        src = "cmd"
    else:
        if not os.path.exists(a.evidence_file):
            print("FAIL: 证据文件不存在 -> %s" % a.evidence_file)
            _append_log({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                         "claim": a.claim, "verdict": "FAIL",
                         "reason": "evidence file missing"})
            return 2
        out = open(a.evidence_file, "r", encoding="utf-8", errors="replace").read()
        rc = 0
        src = "file"

    ok, reason = _judge(out, rc, a.expect)
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    preview = (out or "").strip().replace("\n", " | ")[:160]

    if ok:
        print("PASS: %s" % a.claim)
        print("证据来源：%s" % src)
        print("证据摘要：%s" % preview)
        _append_log({"ts": ts, "claim": a.claim, "verdict": "PASS",
                     "source": src, "preview": preview})
        return 0
    print("FAIL: %s —— %s" % (a.claim, reason))
    print("证据摘要：%s" % preview)
    print("=> 不许对国王说「已修复」。先补实跑证据，或明确告知「我无法验证」及自检路径。")
    _append_log({"ts": ts, "claim": a.claim, "verdict": "FAIL",
                 "source": src, "reason": reason, "preview": preview})
    return 2


if __name__ == "__main__":
    sys.exit(main())
