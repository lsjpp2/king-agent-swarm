#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kaf_gate.py — KAF 强制门禁 (Mandatory Gate)

在任何 删除/移动/覆盖 操作前 MUST 运行本门禁。
- BLOCK  → 退出码 1，操作须停止，展示清单后获用户明确确认+理由方可 --confirmed 重跑
- WARN   → 退出码 0，提醒但未拦
- OK     → 退出码 0，放行

这是 KAF 在「无 OS/客户端 hook 接口」平台（如 WorkBuddy 桌面端）上的
真实强制层：agent 侧强制。平台不提供 PreToolUse 钩子，则由 agent 自己
在每次破坏性操作前调用本门禁并服从其结果。

每次调用都会写入 kaf_gate_audit.log（带时间戳/结果/理由），供 enforced 自核查
验证门禁"近期真在跑"，而非仅文件存在（杜绝"文件在但从不调用"的装饰强制）。

Usage:
    python kaf_gate.py check --op delete --target "D:/x/y"
    python kaf_gate.py check --op delete --target "D:/x/y" --confirmed --reason "清理已推送的临时克隆"
    python kaf_gate.py check --op move  --target "D:/a" --script "move.py" --verified --confirmed --reason "..."
    python kaf_gate.py check --op write  --target "MEMORY.md" --content "新内容..."
"""
import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guard520 import Guard520, GuardResult
from memory_integrity import MemoryIntegrity

AUDIT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kaf_gate_audit.log")
DESTRUCTIVE = {"delete", "rm", "rmtree", "mv", "copy", "write"}


def audit(op, target, status, confirmed, reason):
    """每次门禁调用留痕，供 enforced 自核查验证"真在跑"。"""
    try:
        with open(AUDIT_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] op={op} target={target} result={status} confirmed={confirmed} reason={reason}\n")
    except Exception:
        pass


def main():
    p = argparse.ArgumentParser(description="KAF 强制门禁")
    p.add_argument("action", choices=["check"], help="门禁动作")
    p.add_argument("--op", required=True,
                   choices=["delete", "rm", "move", "mv", "write", "copy", "rmtree"],
                   help="操作类型")
    p.add_argument("--target", default="", help="目标路径")
    p.add_argument("--script", default="", help="破坏性操作的脚本路径(铁律8)")
    p.add_argument("--verified", action="store_true", help="操作已验证(铁律8)")
    p.add_argument("--confirmed", action="store_true", help="已展示清单并获用户确认(铁律10)")
    p.add_argument("--reason", default="", help="操作理由(铁律12：确认删除/移动/覆盖须可追溯)")
    p.add_argument("--content", default="", help="write 操作的新内容(用于520保护检查)")
    p.add_argument("--constitution", default=None, help="constitution.json 路径")
    args = p.parse_args()

    # 归一化别名：move→mv, rm/rmtree→delete，确保破坏性判定一致（修 move 绕过门禁的 bug）
    op = {"move": "mv", "rm": "delete", "rmtree": "delete"}.get(args.op, args.op)

    guard = Guard520(args.constitution) if args.constitution else Guard520()

    action = {
        "type": op,
        "target": args.target,
        "script": args.script or None,
        "verified": args.verified,
        "user_confirmed": args.confirmed,
    }

    # --- write 操作：520 记忆保护(防止删除受保护段落) ---
    if op == "write" and args.target and args.content:
        mi = MemoryIntegrity()
        if not mi.protect_write(args.target, args.content):
            print("BLOCK: 520保护检查未通过 — 受保护内容(520规则/铁律)将被删除，禁止写入")
            print("=> 如需修改受保护段落，须先取得国王(人类)明确授权。")
            audit(op, args.target, "BLOCK", args.confirmed, args.reason)
            return 1
        print("OK: write 通过 520 记忆保护检查")
        audit(op, args.target, "OK", args.confirmed, args.reason)
        return 0

    # --- 确认类破坏性操作 MUST 提供理由(铁律12 可追溯，杜绝提权删除无说明) ---
    if args.confirmed and op in DESTRUCTIVE and not args.reason:
        print("BLOCK: 铁律12违规 — 确认删除/移动/覆盖须提供 --reason 说明理由(可追溯)")
        print("=> 例：--reason \"清理已推送的临时克隆，可从GitHub HEAD a10083a 还原\"")
        audit(op, args.target, "BLOCK", args.confirmed, "(missing reason)")
        return 1

    # --- 删除类：pre_delete (列清单 + 确认) ---
    if op in ("delete", "rm", "rmtree"):
        r = guard.pre_delete(action)
    else:
        # mv/copy 等：pre_execute (铁律8：须有脚本+已验证)
        r = guard.pre_execute(action)

    if r.status == GuardResult.BLOCK:
        print(f"BLOCK: {r.message}")
        items = r.data.get("items", [])
        for it in items[:30]:
            sz = it.get("size", "?")
            note = it.get("note", "")
            print(f"  - {it.get('path')}  ({sz} bytes) {note}")
        print("\n=> 操作被拦截。须向用户展示上述清单并取得明确确认+理由后，")
        print("   再加 --confirmed --reason 重跑本门禁方可通过。绝不可绕过。")
        audit(op, args.target, "BLOCK", args.confirmed, args.reason)
        return 1
    elif r.status == GuardResult.WARN:
        print(f"WARN: {r.message}")
        audit(op, args.target, "WARN", args.confirmed, args.reason)
        return 0
    else:
        msg = r.message or "放行"
        print(f"OK: {msg}")
        audit(op, args.target, "OK", args.confirmed, args.reason)
        return 0


if __name__ == "__main__":
    sys.exit(main())
