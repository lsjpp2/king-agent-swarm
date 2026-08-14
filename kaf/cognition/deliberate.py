#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deliberate.py — 进智脊柱⑤ 元认知门控 (deliberate())

高利害动作前自检：「我做过类似的吗？反模式库有命中吗？」
命中 -> 降级为「列清单 + 等你确认」(软刹车)，等同 520 护栏的软刹车。
不硬拦截（520 护栏负责硬拦），不优于国王否决权，不绕过 kaf_gate.py。

宣称=实现：见 cognition_selftest.py（真跑通 HOLD/WARN/GO 三态）。
"""
import os
import sys

try:
    from .retrieval_inject import load_patterns, _tokenize, score
except ImportError:  # 允许作为脚本直接运行
    from retrieval_inject import load_patterns, _tokenize, score

_HERE = os.path.dirname(os.path.abspath(__file__))
AP_PATH = os.path.join(_HERE, "anti_patterns.jsonl")

# 高利害动作集合：命中反模式才值得自省；普通动作跳过以控开销
HIGH_STAKES = {
    "delete", "rm", "rmtree", "mv", "move", "write", "copy",
    "archive", "rename", "batch_write", "publish",
}


class CogVerdict:
    GO = "GO"
    HOLD = "HOLD"
    WARN = "WARN"

    def __init__(self, status, matched=None, message="", wrong="", right=""):
        self.status = status
        self.matched = matched
        self.message = message
        self.wrong = wrong
        self.right = right

    def __repr__(self):
        return f"CogVerdict({self.status}:{self.matched})"


class Deliberate:
    def __init__(self, path=AP_PATH):
        self.patterns = load_patterns(path)

    def check(self, action_type, target="", plan_text="", context_tokens=None):
        at = (action_type or "").lower()
        if at not in HIGH_STAKES:
            return CogVerdict(CogVerdict.GO, None, "非高利害动作，跳过自省")
        hay = f"{at} {target} {plan_text}"
        toks = _tokenize(hay)
        best = None
        best_score = 0
        for p in self.patterns:
            s = score(p, toks)
            if s > best_score:
                best_score = s
                best = p
        if best and best_score > 0:
            sev = best.get("severity", "med")
            if sev == "high":
                return CogVerdict(
                    CogVerdict.HOLD, best.get("name"),
                    f"命中历史反模式 [{best.get('name')}]（severity=high）",
                    wrong=best.get("wrong", ""), right=best.get("right", ""),
                )
            return CogVerdict(
                CogVerdict.WARN, best.get("name"),
                f"注意历史反模式 [{best.get('name')}]",
                wrong=best.get("wrong", ""), right=best.get("right", ""),
            )
        return CogVerdict(CogVerdict.GO, None, "未命中已知反模式")


if __name__ == "__main__":
    at = sys.argv[1] if len(sys.argv) > 1 else "archive"
    tgt = sys.argv[2] if len(sys.argv) > 2 else ""
    plan = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
    v = Deliberate().check(at, tgt, plan)
    print(v, "| wrong:", v.wrong, "| right:", v.right)
