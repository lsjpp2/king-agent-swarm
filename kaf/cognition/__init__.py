#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cognition — KAF 进智脊柱 (Cognition Spine) 运行时包

v5.3.1 落地地基三件套：
  ① anti_patterns.jsonl   反模式库（种子来自 Claw 会话清理事件 8f6d42dc）
  ② retrieval_inject.py    检索注入（任务起点拉相关反模式进上下文）
  ⑤ deliberate.py          元认知门控（高利害动作前软刹车自检）

③④ + Loop Driver 为 v5.4 代码范畴（本包预留接口，尚未实现）。
"""
from .retrieval_inject import load_patterns, retrieve_patterns, build_injection
from .deliberate import Deliberate, CogVerdict, HIGH_STAKES

__all__ = [
    "load_patterns", "retrieve_patterns", "build_injection",
    "Deliberate", "CogVerdict", "HIGH_STAKES",
]
