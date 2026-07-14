#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kaf_gate.py — KAF 强制门禁 (Mandatory Gate)

在任何 删除/移动/覆盖 操作前 MUST 运行本门禁。
- BLOCK  → 退出码 1，操作须停止，展示清单后获用户明确确认方可 --confirmed 重跑
- WARN   → 退出码 0，提醒但未拦
- OK     → 退出码 0，放行

这是 KAF 在「无 OS/客户端 hook 接口」平台（如 WorkBuddy 桌面端）上的
真实强制层：agent 侧强制。平台不提供 PreToolUse 钩子，则由 agent 自己
在每次破坏性操作前调用本门禁并服从其结果——这正是 Platform Adapter 对
无钩子环境的诚实适配，而非降级。

Usage:
    python kaf_gate.py check --op delete --target "D:/x/y"
    python kaf_gate.py check --op delete --target "D:/x/y" --confirmed
    python kaf_gate.py check --op move  --target "D:/a" --script "move.py" --verified
    python kaf_gate.py check --op write  --target "MEMORY.md" --content "新内容..."
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guard520 import Guard520, GuardResult
from memory_integrity import MemoryIntegrity


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
    p.add_argument("--content", default="", help="write 操作的新内容(用于520保护检查)")
    p.add_argument("--constitution", default=None, help="constitution.json 路径")
    args = p.parse_args()

    guard = Guard520(args.constitution) if args.constitution else Guard520()

    action = {
        "type": args.op,
        "target": args.target,
        "script": args.script or None,
        "verified": args.verified,
        "user_confirmed": args.confirmed,
    }

    # --- write 操作：520 记忆保护(防止删除受保护段落) ---
    if args.op == "write" and args.target and args.content:
        mi = MemoryIntegrity()
        if not mi.protect_write(args.target, args.content):
            print("BLOCK: 520保护检查未通过 — 受保护内容(520规则/铁律)将被删除，禁止写入")
            print("=> 如需修改受保护段落，须先取得国王(人类)明确授权。")
            return 1
        print("OK: write 通过 520 记忆保护检查")
        return 0

    # --- 删除类：pre_delete (列清单 + 确认) ---
    if args.op in ("delete", "rm", "rmtree"):
        r = guard.pre_delete(action)
    else:
        # move/copy 等：pre_execute (铁律8：须有脚本+已验证)
        r = guard.pre_execute(action)

    if r.status == GuardResult.BLOCK:
        print(f"BLOCK: {r.message}")
        items = r.data.get("items", [])
        for it in items[:30]:
            sz = it.get("size", "?")
            note = it.get("note", "")
            print(f"  - {it.get('path')}  ({sz} bytes) {note}")
        print("\n=> 操作被拦截。须向用户展示上述清单并取得明确确认后，")
        print("   再加 --confirmed 重跑本门禁方可通过。绝不可绕过。")
        return 1
    elif r.status == GuardResult.WARN:
        print(f"WARN: {r.message}")
        return 0
    else:
        print(f"OK: {r.message}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
