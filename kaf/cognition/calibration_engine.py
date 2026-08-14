#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calibration_engine.py — 进智脊柱④ 决策校准引擎 (Calibration)

相似决策比对历史 outcome/confidence，标注本次是否误校准(miscalibration)。
依赖 experience_distillation 的经验库。

宣称=实现：见 cognition_selftest.py（真跑通 误校准检测 / 校准通过）。
"""
import os

try:
    from .experience_distillation import load_experiences, _ctx_key
except ImportError:  # 允许作为脚本直接运行
    from experience_distillation import load_experiences, _ctx_key

_HERE = os.path.dirname(os.path.abspath(__file__))


class CalibrationReport:
    def __init__(self, similar_count, success_rate, miscalibrated, message, history=None):
        self.similar_count = similar_count
        self.success_rate = success_rate
        self.miscalibrated = miscalibrated
        self.message = message
        self.history = history or []

    def __repr__(self):
        return (f"CalibrationReport(similar={self.similar_count}, "
                f"rate={self.success_rate:.2f}, miscalib={self.miscalibrated})")


def calibrate(context, action, predicted_outcome, path=None):
    """比对历史相似决策，标注误校准。
    - 历史相似决策高置信且 outcome=fail，但本次预测 success → 误校准警告
    - 历史相似决策成功率高(>=0.8) 但本次预测 fail → 误校准提示(保守复核)
    - 无相似历史 → 无法校准，提示谨慎
    """
    if path is None:
        path = os.path.join(_HERE, "experience.jsonl")
    hist = load_experiences(path)
    key = _ctx_key(context)
    sim = [e for e in hist if e.get("ctx_key") == key]
    if not sim:
        return CalibrationReport(0, 0.0, False,
                                 "无相似历史经验，无法校准（保持谨慎）")
    n = len(sim)
    succ = sum(1 for e in sim if e.get("outcome") == "success")
    rate = succ / n

    high_fail = any(e.get("outcome") == "fail" and e.get("confidence", 0) >= 0.7
                    for e in sim)
    if high_fail and predicted_outcome == "success":
        return CalibrationReport(n, rate, True,
                                 "⚠️ 误校准：历史相似决策高置信失败，但本次预测成功，请复核",
                                 sim)
    if rate >= 0.8 and predicted_outcome == "fail":
        return CalibrationReport(n, rate, True,
                                 "⚠️ 误校准：历史相似决策成功率高，本次预测失败，请复核",
                                 sim)
    return CalibrationReport(n, rate, False,
                             f"校准通过：相似 {n} 条，成功率 {rate:.2f}", sim)


if __name__ == "__main__":
    r = calibrate("归档前的分类", "一刀切归档", "success")
    print(r)
