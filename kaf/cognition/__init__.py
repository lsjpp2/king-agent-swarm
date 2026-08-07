#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cognition — KAF 进智脊柱 (Cognition Spine) 运行时包

v5.3.1 落地地基三件套：
  ① anti_patterns.jsonl   反模式库（种子来自 Claw 会话清理事件 8f6d42dc）
  ② retrieval_inject.py    检索注入（任务起点拉相关反模式进上下文）
  ⑤ deliberate.py          元认知门控（高利害动作前软刹车自检）

v5.4.2 落地闭环三件套（③④ + Loop Driver 交付质量闭环）：
  ③ experience_distillation.py  经验蒸馏（带置信度累积）
  ④ calibration_engine.py       决策校准引擎
  loop_driver.py                Loop Driver（对齐检验→修订→再检验→收敛）
"""
from .retrieval_inject import load_patterns, retrieve_patterns, build_injection
from .deliberate import Deliberate, CogVerdict, HIGH_STAKES
from .experience_distillation import add_experience, get_high_conf, load_experiences
from .calibration_engine import calibrate, CalibrationReport
from .loop_driver import run_loop, align, simple_revise

__all__ = [
    "load_patterns", "retrieve_patterns", "build_injection",
    "Deliberate", "CogVerdict", "HIGH_STAKES",
    "add_experience", "get_high_conf", "load_experiences",
    "calibrate", "CalibrationReport",
    "run_loop", "align", "simple_revise",
]
