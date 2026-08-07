#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retrieval_inject.py — 进智脊柱② 检索注入 (Retrieval Injection)

任务起点把相关反模式拉进上下文，作为「⚠️ 历史反模式」块注入提示前缀。
与 coordinator.json / progress/ 共享层一致：只读共享、不污染私有记忆。

宣称=实现：见 cognition_selftest.py（真跑通 load/retrieve/build_injection）。
"""
import os
import re
import json
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
AP_PATH = os.path.join(_HERE, "anti_patterns.jsonl")

# 停用词：降低中文短文本噪声
_STOP = set("的 了 和 与 在 是 把 被 对 从 到 一 个 中 全 部 不 无 为 我 你 他 它 这 那 都 就 也 要 会".split())


def load_patterns(path=AP_PATH):
    """读取反模式库（jsonl），逐行容错。"""
    pats = []
    if not os.path.exists(path):
        return pats
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                pats.append(json.loads(line))
            except Exception:
                continue
    return pats


def _tokenize(text):
    """中文按二元语法(bigram)切分 + 拉丁词，提升反模式触发词召回率。
    例：「标题改名」-> [标题, 题改, 改名]；匹配触发词「标题含/改名」可靠命中。"""
    text = re.sub(r"[\s，。、；：！？()（）\[\]【】\"'‘’“”/\\|]+", " ", text or "")
    toks = []
    for seg in re.findall(r"[\u4e00-\u9fff]+|[A-Za-z_]+", text):
        if re.match(r"[A-Za-z_]+", seg):
            if seg not in _STOP:
                toks.append(seg)
        else:  # CJK 二元语法
            if len(seg) == 1:
                if seg not in _STOP:
                    toks.append(seg)
            else:
                for i in range(len(seg) - 1):
                    bg = seg[i:i + 2]
                    if bg not in _STOP:
                        toks.append(bg)
    return toks


def score(pat, toks):
    """反模式与任务描述的命中分：触发词全词命中 +2，子串命中 +1。"""
    s = 0
    hay = " ".join(pat.get("trigger", [])) + " " + pat.get("name", "")
    for t in toks:
        if t in hay:
            s += 2
        else:
            for trig in pat.get("trigger", []):
                if t and t in trig:
                    s += 1
                    break
    return s


def retrieve_patterns(task_desc, k=5, path=AP_PATH):
    """返回与 task_desc 最相关的 top-k 反模式（按命中分降序，仅含 >0 命中）。"""
    pats = load_patterns(path)
    toks = _tokenize(task_desc)
    scored = [(score(p, toks), p) for p in pats]
    scored = [x for x in scored if x[0] > 0]
    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:k]]


def build_injection(task_desc, k=5, path=AP_PATH):
    """生成可直接前缀注入的「⚠️ 历史反模式」块；无命中返回空串。"""
    hits = retrieve_patterns(task_desc, k=k, path=path)
    if not hits:
        return ""
    lines = ["⚠️ 历史反模式（进智脊柱检索注入，软提示非硬拦截）："]
    for p in hits:
        lines.append(
            f"  • [{p.get('severity', '?').upper()}] {p.get('name', '')}: "
            f"{p.get('right', '')}（避免：{p.get('wrong', '')}）"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "归档所有会话备份记忆"
    out = build_injection(task)
    print(out or "（无命中历史反模式）")
