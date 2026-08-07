#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loop_driver.py — 进智脊柱 v5.4 Loop Driver 交付质量闭环 (闭环自修)

后台自动：候选物 vs 指令逐条比对 → 差异清单 → 调修订器 → 再比对 → 收敛交付。
对齐度阈值三档（国王已确认 2026-08-07）：
  - hard 硬阈值：可量化指令(含数字/显式清单) → 100% 对齐(score==1.0 且零 gap)才收敛，自动。
  - soft 软阈值：半量化 → 关键约束零违反 + 主要意图对齐 >= 0.8 即收敛，每轮留痕。
  - king 国王兜底：模糊指令 → 跑 <=1 轮基础对齐后 needs_king=True，不擅自定稿。
熔断：超过 max_rounds(默认5) 或 check_abort() 返回 True(如 kill-switch) 立即中止交还国王。
每轮候选物留可逆副本；审计链记录差异。

修订器由调用方注入 revise_fn(candidate, gaps) -> new_candidate；本模块只驱动循环与比对。
simple_revise 提供最简演示修订（把 gaps 格式化追加），真实 agent 用自己的 LLM 修订替换。

宣称=实现：见 cognition_selftest.py（auto-fix 三轮内收敛 / 国王兜底 / 硬阈值）。
"""
import os
import re
import shutil
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))


# ---------- 比对器 ----------
def parse_constraints(instruction):
    """把指令拆成约束条目（按中英文标点/换行切分）。"""
    parts = re.split(r"[；;。.\n]+", instruction.strip())
    return [p.strip() for p in parts if p.strip()]


def _is_quantified(constraint):
    """可量化约束：含数字 或 显式全量标记。"""
    if re.search(r"\d", constraint):
        return True
    if any(k in constraint for k in ["全部", "每个", "所有", "每条", "均", "N 条", "N条"]):
        return True
    return False


def _embodies(candidate, constraint):
    """候选物是否体现某约束：约束的关键词(CJK bigram + 拉丁词)多数命中候选物。"""
    toks = re.findall(r"[\u4e00-\u9fff]{2}|[A-Za-z_]+", constraint)
    if not toks:
        return True  # 空约束视为满足
    uniq = set(toks)
    hit = sum(1 for t in uniq if t in candidate)
    return hit >= max(1, len(uniq) * 0.5)


def _is_critical(constraint):
    return any(k in constraint for k in ["必须", "禁止", "不能", "不得", "MUST", "NOT", "不可", "严禁"])


def align(instruction, candidate):
    """比对候选物与指令，返回 {score, satisfied, total, gaps[], critical_violation, quantified}。"""
    cons = parse_constraints(instruction)
    total = len(cons)
    satisfied = 0
    gaps = []
    crit_viol = False
    for c in cons:
        if _embodies(candidate, c):
            satisfied += 1
        else:
            gaps.append(c)
            if _is_critical(c):
                crit_viol = True
    score = (satisfied / total) if total else 1.0
    return {
        "score": score,
        "satisfied": satisfied,
        "total": total,
        "gaps": gaps,
        "critical_violation": crit_viol,
        "quantified": any(_is_quantified(c) for c in cons),
    }


def simple_revise(candidate, gaps):
    """最简演示修订：把未满足约束追加为显式补丁行。真实 agent 用 LLM 修订替换。"""
    patch = "\n".join(f"【待补】{g}" for g in gaps)
    return (candidate + "\n" + patch).strip()


# ---------- 闭环 ----------
def _judge(a, mode):
    if mode == "hard":
        return a["score"] == 1.0 and not a["gaps"] and a["quantified"]
    if mode == "king":
        return False
    # soft
    return (a["score"] >= 0.8) and (not a["critical_violation"])


def run_loop(instruction, candidate, revise_fn=None, mode="soft",
             max_rounds=5, backup_dir=None, check_abort=None):
    """交付质量闭环。
    revise_fn: callable(candidate, gaps) -> new_candidate（缺省用 simple_revise）
    mode: hard | soft | king
    check_abort: callable() -> bool（True 则中止，如 kill-switch）
    返回 dict: {final, rounds, converged, needs_king, last_align, history[], status}
    """
    if revise_fn is None:
        revise_fn = simple_revise
    if backup_dir is None:
        backup_dir = tempfile.mkdtemp(prefix="kaf_loop_")
    os.makedirs(backup_dir, exist_ok=True)

    history = []
    cur = candidate
    for rnd in range(1, max_rounds + 1):
        if check_abort and check_abort():
            return _final(cur, rnd - 1, False, False, align(instruction, cur), history, "aborted")
        a = align(instruction, cur)
        history.append({"round": rnd, "score": round(a["score"], 3), "gaps": a["gaps"]})
        # 备份本轮候选物（可逆副本）
        try:
            with open(os.path.join(backup_dir, f"candidate_r{rnd}.txt"), "w", encoding="utf-8") as f:
                f.write(cur)
        except Exception:
            pass

        if mode == "king":
            # 模糊指令：跑完当前 1 轮即交还国王，不擅自定稿
            return _final(cur, rnd, False, True, a, history, "king_fallback")

        if _judge(a, mode):
            return _final(cur, rnd, True, False, a, history, "converged")

        # 未收敛 → 调修订器
        cur = revise_fn(cur, a["gaps"])

    # 超轮次熔断
    return _final(cur, max_rounds, False, False, align(instruction, cur), history, "max_rounds")


def _final(final, rounds, converged, needs_king, align_res, history, status):
    return {
        "final": final,
        "rounds": rounds,
        "converged": converged,
        "needs_king": needs_king,
        "last_align": align_res,
        "history": history,
        "status": status,
    }


if __name__ == "__main__":
    import json
    instr = "归档所有纯系统备份;保留活会话;不得误归档真实工作对话"
    cand = "归档备份"
    res = run_loop(instr, cand, mode="soft", max_rounds=5)
    print(json.dumps({k: v for k, v in res.items() if k != "final"}, ensure_ascii=False, indent=2))
    print("FINAL CANDIDATE:\n", res["final"])
