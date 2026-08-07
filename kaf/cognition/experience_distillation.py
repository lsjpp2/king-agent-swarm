#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
experience_distillation.py — 进智脊柱③ 经验蒸馏 (Distillation)

任务收尾把一次决策/操作压成结构化经验
{context, action, outcome, confidence}，写入经验库 experience.jsonl。
置信度随复核次数累积（同类 context 每次 +0.1，封顶 1.0）；低置信不注入防噪声。
与反模式库对齐：只读共享、不污染私有记忆。

宣称=实现：见 cognition_selftest.py（真跑通 add/累积/get_high_conf）。
"""
import os
import json
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))
EXP_PATH = os.path.join(_HERE, "experience.jsonl")


def _ctx_key(context):
    """相似聚合键：归一去空白小写后 md5 前 12 位。"""
    s = "".join(str(context).lower().split())
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:12]


def load_experiences(path=EXP_PATH):
    exps = []
    if not os.path.exists(path):
        return exps
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                exps.append(json.loads(line))
            except Exception:
                continue
    return exps


def add_experience(context, action, outcome, confidence=0.5, source="", path=EXP_PATH):
    """新增一条经验；同类 context 已存在则按复核累积置信度(每次 +0.1，封顶 1.0)。
    返回写入的经验 dict。outcome ∈ {success, fail, partial}。"""
    exps = load_experiences(path)
    key = _ctx_key(context)
    base = confidence
    for e in exps:
        if e.get("ctx_key") == key:
            base = min(1.0, max(base, e.get("confidence", 0.5)) + 0.1)
    exp = {
        "ctx_key": key,
        "context": context,
        "action": action,
        "outcome": outcome,
        "confidence": round(base, 3),
        "reviews": 1,
        "source": source,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(exp, ensure_ascii=False) + "\n")
    return exp


def get_high_conf(min_conf=0.7, path=EXP_PATH):
    """返回置信度 >= min_conf 的高置信经验（供检索注入复用，防噪声）。"""
    return [e for e in load_experiences(path) if e.get("confidence", 0) >= min_conf]


def get_by_context(context, path=EXP_PATH):
    key = _ctx_key(context)
    return [e for e in load_experiences(path) if e.get("ctx_key") == key]


if __name__ == "__main__":
    e = add_experience("归档前的分类", "逐条核查+conversation_search实锤",
                       "success", confidence=0.6, source="8f6d42dc复盘")
    print("added:", e)
    print("high_conf(>=0.7):", get_high_conf())
