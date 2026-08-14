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

    # --- v5.4.2 闭环三件套（③④ + Loop Driver）---
    import tempfile as _tf
    import os as _os
    _tmp = _os.path.join(_tf.gettempdir(), "_kaf_cog_selftest_exp.jsonl")
    if _os.path.exists(_tmp):
        _os.remove(_tmp)
    try:
        from experience_distillation import add_experience, get_high_conf
    except ImportError:
        from .experience_distillation import add_experience, get_high_conf
    e1 = add_experience("测试上下文A", "动作", "success", confidence=0.6, source="selftest", path=_tmp)
    check("③蒸馏写入经验(conf>=0.6)", e1["confidence"] >= 0.6)
    check("③高置信检索(0.6<0.7应空)", get_high_conf(min_conf=0.7, path=_tmp) == [])
    add_experience("测试上下文A", "动作", "success", confidence=0.6, source="selftest", path=_tmp)
    check("③复核后置信度累积>=0.7", any(x["confidence"] >= 0.7 for x in get_high_conf(min_conf=0.7, path=_tmp)))

    try:
        from calibration_engine import calibrate
    except ImportError:
        from .calibration_engine import calibrate
    r_ok = calibrate("测试上下文A", "动作", "success", path=_tmp)
    check("④校准无误校准(历史成功)", (not r_ok.miscalibrated) and r_ok.similar_count >= 1)
    add_experience("测试上下文B", "动作", "fail", confidence=0.8, source="selftest", path=_tmp)
    r_mis = calibrate("测试上下文B", "动作", "success", path=_tmp)
    check("④误校准检测(高置信失败但预测成功)", r_mis.miscalibrated)

    try:
        from loop_driver import run_loop
    except ImportError:
        from .loop_driver import run_loop
    instr_hard = "归档 113 条纯系统备份;均经 conversation_search 零命中"
    res_h = run_loop(instr_hard, "归档备份", mode="hard", max_rounds=5)
    check("Loop硬阈值收敛(<=5轮)", res_h["converged"] and res_h["rounds"] <= 5)
    instr_soft = "归档所有纯系统备份;保留活会话;不得误归档真实工作对话"
    res_s = run_loop(instr_soft, "归档备份", mode="soft", max_rounds=5)
    check("Loop软阈值收敛", res_s["converged"])
    res_k = run_loop(instr_soft, "归档备份", mode="king", max_rounds=5)
    check("Loop国王兜底needs_king", res_k["needs_king"] and not res_k["converged"])

    print("\nRESULT:", "ALL_OK" if ok else "HAS_FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
