#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cognition_selftest.py — 进智脊柱地基自测 (520 式：真跑通，非装饰)

验证项：
  1) 反模式库存在且 >=3 条真实种子
  2) 检索注入能命中「一刀切归档」类任务
  3) deliberate() 对「批量归档备份」返回 HOLD（高利害 + 历史命中）
  4) deliberate() 对普通动作(如 read)返回 GO（跳过自省）
  5) 注入块非空

用法：python cognition_selftest.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retrieval_inject import load_patterns, retrieve_patterns, build_injection
from deliberate import Deliberate, CogVerdict

ok = True


def check(name, cond):
    global ok
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {name}")
    if not cond:
        ok = False


def main():
    pats = load_patterns()
    check("anti_patterns >= 3", len(pats) >= 3)

    hits = retrieve_patterns("把标题含备份的全部会话归档")
    check("retrieve 命中归档类反模式",
          any("归档" in p.get("name", "") for p in hits))

    v = Deliberate().check(
        "archive", target="D:/x/备份记忆", plan_text="标题含备份/同步的全部归档")
    check("deliberate HOLD on 批量归档备份", v.status == CogVerdict.HOLD)
    check("HOLD 携带正确替代", bool(v.right))

    v2 = Deliberate().check("read", target="some/file")
    check("deliberate GO on 普通动作", v2.status == CogVerdict.GO)

    inj = build_injection("归档会话清理 标题改名")
    check("注入块非空", inj != "")

    print("\nRESULT:", "ALL_OK" if ok else "HAS_FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
