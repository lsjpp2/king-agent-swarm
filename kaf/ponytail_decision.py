#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAF × Ponytail 融合 — 预执行决策层（L2）

v5.5 核心特性：把 Ponytail 的「预写码决策极简主义」作为 KAF 的第 4 层
（L2 预执行决策约束），与 kaf_gate(L4 执行期硬门禁) + review(L5 多视角审查)
形成完整管线：

    L0 用户意图
    L1 KAF task-classifier（编码任务 vs 内容生产分流）
    L2 [本层] Ponytail 预写码决策（7 级梯，停在第一个成立的台阶）
    L3 KAF 执行（agent 干活）
    L4 KAF kaf_gate 执行期硬门禁（删/移/覆盖前必过）
    L5 KAF review.py 多视角审查（含 economics 视角）
    L6 520 自检 + 审计链

设计原则（来自 Ponytail 官方，已修正口径）：
- 7 级决策梯：need? → exists? → stdlib? → native? → dep? → one-liner? → minimal
- 安全红线：永不删 trust-boundary 校验 / data-loss 处理 / security / accessibility
- 模型感知：思考型模型（如 GPT-5.5）上 Ponytail 反向 → L2 自动 bypass
- 任务分流：仅编码类任务注入；内容生产（推文/生图/报告）不介入

关键约束（避免与 KAF/WorkBuddy 钩子系统冲突）：
本模块是「决策建议」层，由 agent 在编码任务起点调用 `kaf ponytail "<task>"` 获得
7 级梯全貌 + 安全红线，**自行判断停在哪个台阶**。绝不直接挂载 Ponytail 原生
Node.js 钩子（SessionStart/UserPromptSubmit/SubagentStart）——那会与宿主钩子打架
且触发 safe-delete fail-closed。

Usage:
    from ponytail_decision import PonytailDecision
    d = PonytailDecision(model="haiku-4.5")
    out = d.decide("给 React 表单加一个日期选择器")   # 返回 7 级梯决策建议

CLI:
    python ponytail_decision.py "<task>" [--model <m>] [--context <c>]
"""
import sys
import os
import json


# 7 级决策梯（停在第一个成立的台阶）
LADDER = [
    {"level": 1, "name": "need",      "question": "需要存在吗？",       "action": "skip",
     "rule": "不需要则跳过（YAGNI）"},
    {"level": 2, "name": "exists",    "question": "代码库里已有？",     "action": "reuse",
     "rule": "复用，别重写"},
    {"level": 3, "name": "stdlib",    "question": "标准库能做？",       "action": "use_stdlib",
     "rule": "用标准库"},
    {"level": 4, "name": "native",    "question": "原生平台能力？",     "action": "use_native",
     "rule": "用原生（<input type=date> 替代手搓组件，最大削减来源）"},
    {"level": 5, "name": "dep",       "question": "已装依赖能做？",     "action": "use_dep",
     "rule": "用已装依赖"},
    {"level": 6, "name": "oneliner",  "question": "能一行解决？",       "action": "oneliner",
     "rule": "一行解决"},
    {"level": 7, "name": "minimal",   "question": "都不行",             "action": "minimal_impl",
     "rule": "才写最小可行实现"},
]


# 安全红线（永不妥协；对应 Ponytail 官方 safe 100% 底线）
SAFETY_REDLINES = [
    "trust-boundary 校验",
    "data-loss 处理",
    "安全处理（注入/越权/密钥）",
    "无障碍（a11y）",
]


# 思考型模型（Ponytail 在此类模型上成本/延迟反向，L2 自动 bypass）
# 来源：Ponytail 官方基准 — GPT-5.5 上 token/成本反而上升
THINKING_MODELS = {
    "gpt-5.5", "gpt-5.5-mini", "gpt-5.5-nano",
    "o3", "o4", "o4-mini",
    "claude-opus-4.5-thinking", "claude-4-opus-thinking",
    "deepseek-r2-thinking",
}


# 编码任务关键词（task-classifier 分流：仅编码任务注入 L2）
CODING_KEYWORDS = [
    "写", "代码", "实现", "函数", "脚本", "重构", "模块", "类",
    "write", "code", "implement", "function", "script", "refactor", "class",
    "组件", "api", "接口", "bug", "修复", "优化", "逻辑",
]


class PonytailDecision:
    """预执行决策引擎（L2 极简主义决策梯）"""

    def __init__(self, model=None):
        self.model = model

    def applies_to_model(self, model=None):
        """Ponytail 仅对非思考型模型生效（GPT-5.5 等思考型上反向）"""
        m = (model or self.model or "").lower()
        if not m:
            return True  # 未指定模型时默认生效
        return m not in THINKING_MODELS

    def is_coding_task(self, task_text):
        """仅编码类任务注入 L2 预执行决策；内容生产（推文/生图/报告）不介入"""
        text = (task_text or "").lower()
        return any(kw.lower() in text for kw in CODING_KEYWORDS)

    def _redline_violated(self, context=None):
        """检查上下文是否涉及安全红线（若决策是 skip，可能遗漏校验 → HOLD）"""
        ctx = (context or "").lower()
        for rl in SAFETY_REDLINES:
            kw = rl.split()[0]
            if kw in ctx:
                return rl
        return None

    def decide(self, task_text, context=None, model=None):
        """预执行决策：返回 7 级梯停驻建议 + 安全校验。

        返回 dict:
            applicable      bool   是否适用（模型/任务类型分流）
            bypass_reason  str    不适用原因
            reached_level  int    建议落点台阶 (1-7, 0=未适用)
            action         str    skip/reuse/use_stdlib/use_native/use_dep/oneliner/minimal_impl
            question       str    该台阶提问
            rule           str    该台阶规则
            safety_hold    bool   是否触发安全 HOLD
            safety_reason  str
            note           str    人类可读说明
            ladder         list   7 级梯全貌（供 agent 自查）
            redlines       list   安全红线清单
        """
        # 模型分流
        if not self.applies_to_model(model):
            return {
                "applicable": False,
                "bypass_reason": f"模型 {model} 为思考型，Ponytail 在该类模型上成本/延迟反向，L2 自动 bypass",
                "reached_level": 0, "action": None, "question": None, "rule": None,
                "safety_hold": False, "safety_reason": "",
                "note": "思考型模型自行斟酌，不强制走极简梯",
                "ladder": LADDER, "redlines": SAFETY_REDLINES,
            }
        # 任务类型分流
        if not self.is_coding_task(task_text):
            return {
                "applicable": False,
                "bypass_reason": "非编码任务（内容生产/推文/生图/报告等），Ponytail 不介入",
                "reached_level": 0, "action": None, "question": None, "rule": None,
                "safety_hold": False, "safety_reason": "",
                "note": "L2 仅对编码任务生效",
                "ladder": LADDER, "redlines": SAFETY_REDLINES,
            }
        # 走 7 级梯：本层是「建议层」，输出全貌 + 默认落点（L7 minimal 最保守），
        # 由 agent 据上下文前移到第一个成立台阶。永不跳过安全红线。
        decision = {
            "applicable": True,
            "bypass_reason": "",
            "reached_level": 7,
            "action": "minimal_impl",
            "question": LADDER[6]["question"],
            "rule": LADDER[6]["rule"],
            "safety_hold": False,
            "safety_reason": "",
            "note": "编码任务：建议从 L1 逐阶自查，停在第一个成立台阶；安全红线永不妥协",
            "ladder": LADDER,
            "redlines": SAFETY_REDLINES,
        }
        # 安全红线检查（上下文涉及红线关键词且可能 skip 时 HOLD）
        violated = self._redline_violated(context)
        if violated:
            decision["safety_hold"] = True
            decision["safety_reason"] = f"上下文涉及安全红线「{violated}」，decide 阶段不得 skip/遗漏"
        return decision


def main():
    if len(sys.argv) < 2:
        print('Usage: python ponytail_decision.py "<task>" [--model <m>] [--context <c>]')
        return 1
    task = sys.argv[1]
    model = None
    ctx = None
    if "--model" in sys.argv:
        i = sys.argv.index("--model")
        model = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    if "--context" in sys.argv:
        i = sys.argv.index("--context")
        ctx = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    d = PonytailDecision(model=model)
    out = d.decide(task, context=ctx, model=model)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
