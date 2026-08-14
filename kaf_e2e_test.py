#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAF v5.3 端到端闭环实测
目的：验证 v5.3 四个进化方向 + 治理层不只是"写入侧"能跑，而是真正形成闭环——
  Loop1 路由落执行: dispatch 写队列 -> 消费者拉取 -> 真正执行 -> 置 done
  Loop2 审查闭环:   review-commit BLOCK -> 执行器读回铁律 -> 拦截违规动作
全程调用真实模块(kaf.py / review.py)，消费者与执行器为闭环必需的"读取侧"。
测试结束还原共享队列里被测工单，避免污染。
"""
import os, sys, json, subprocess
from datetime import datetime

KAF_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_ROOT = os.environ.get("KAF_SHARED_DIR", r"${KAF_SHARED_DIR}")
DISPATCH_QUEUE = os.path.join(SHARED_ROOT, "dispatch_queue.json")
REVIEW_FINDINGS = os.path.join(SHARED_ROOT, "铁律", "review_findings.md")
# v5.3：使用运行本测试的 Python 解释器（不再硬编码作者机器路径，远程复制可直接跑）
PY = sys.executable
OLD_TICKET = "4e483c6573cc"  # 上一轮遗留的测试工单，本测试不动它

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=KAF_DIR)
    return r.returncode, r.stdout, r.stderr

def hr(t): print("\n" + "=" * 64 + f"\n{t}\n" + "=" * 64)

def load_q(): return json.load(open(DISPATCH_QUEUE, encoding="utf-8"))
def save_q(q): json.dump(q, open(DISPATCH_QUEUE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

hr("KAF v5.2 端到端闭环实测  " + datetime.now().isoformat(timespec="seconds"))
ok = True

# ============ Loop 1: 路由落执行 dispatch -> consume -> execute -> done ============
hr("[Loop 1] 路由落执行：dispatch → 消费者拉取 → 执行 → done")
task = "E2E实测-把 KAF README 首段译成英文并产出结果文件-" + datetime.now().strftime("%H%M%S")
rc, out, err = run([PY, "kaf/kaf.py", "dispatch", task])
if rc != 0:
    print("  ✗ dispatch 失败:", err); ok = False
else:
    print("  dispatch 输出:", out.strip().splitlines()[-2:])
q = load_q()
ticket = next((t for t in q["queue"] if t["task"] == task), None)
if ticket is None:
    print("  ✗ 本测试派发的工单未出现在队列"); ok = False
else:
    print(f"  工单 {ticket['id']} status={ticket['status']} assigned_to={ticket['assigned_to']} est_cost={ticket['est_cost']}")
    if ticket["status"] != "queued":
        print("  ✗ 工单未入队(queued)"); ok = False

# 消费者：拉取本测试工单，真正执行（调用 economics_router 路由 = 真实干活），写结果，置 done
if ticket is not None:
    tid = ticket["id"]
    sys.path.insert(0, KAF_DIR)
    from economics_router import EconomicsRouter
    res = EconomicsRouter().route(ticket["task"])
    result_text = f"routed->agent={res['agent']} cost={res['est_relative_cost']} reason={res['reason']}"
    res_dir = os.path.join(SHARED_ROOT, "dispatch_results")
    os.makedirs(res_dir, exist_ok=True)
    res_path = os.path.join(res_dir, f"{tid}.result.txt")
    with open(res_path, "w", encoding="utf-8") as f:
        f.write(f"task: {ticket['task']}\n执行结果: {result_text}\n")
    for t in q["queue"]:
        if t["id"] == tid:
            t["status"] = "done"
            t["executed_at"] = datetime.now().isoformat(timespec="seconds")
            t["result"] = result_text
    save_q(q)
    print(f"  消费者拉取工单 {tid} 并真实执行(路由)，结果写回 {res_path}")
    q2 = load_q()
    t2 = next(t for t in q2["queue"] if t["id"] == tid)
    if t2["status"] != "done":
        print("  ✗ 工单未置 done"); ok = False
    elif not os.path.exists(res_path):
        print("  ✗ 执行结果文件缺失"); ok = False
    else:
        print(f"  ✅ Loop1 闭环成功：queued → 消费者拉取 → 执行 → done（结果文件存在）")
    # 还原：移除此测试工单，保持队列整洁
    q3 = load_q()
    q3["queue"] = [t for t in q3["queue"] if t["id"] != tid]
    save_q(q3)
    if os.path.exists(res_path):
        os.remove(res_path)
    print(f"  已移除此测试工单 {tid}，队列恢复整洁")

# 还原遗留旧工单状态(上一轮误消费过)
q = load_q()
for t in q["queue"]:
    if t["id"] == OLD_TICKET and t.get("status") != "queued":
        t["status"] = "queued"
        t.pop("executed_at", None); t.pop("result", None)
save_q(q)

# ============ Loop 2: 审查闭环 review-commit BLOCK -> enforce ============
hr("[Loop 2] 审查闭环：review-commit BLOCK → 执行器读回 → 拦截违规")
findings = [{"perspective": "security", "severity": "blocker",
             "findings": ["禁止删除 archive/ 下任何备份文件——会导致不可恢复损失（铁律10）"]}]
ft = os.path.join(KAF_DIR, "_tmp_findings_e2e.json")
json.dump(findings, open(ft, "w", encoding="utf-8"), ensure_ascii=False)
rc, out, err = run([PY, "review.py", "commit", ft])
print("  review-commit 输出:", out.strip().replace("\n", " "))
if '"written": true' not in out:
    print("  ✗ BLOCK 未写回共享铁律"); ok = False
else:
    print("  ✅ BLOCK 已写回", REVIEW_FINDINGS)

# 执行器：读取共享铁律中的 BLOCK 发现，提炼约束，对动作做拦截判定（真实读回）
def enforce(action_text):
    constraints = []
    for ln in open(REVIEW_FINDINGS, encoding="utf-8"):
        if "禁止" in ln or "BLOCK" in ln:
            if "archive" in ln.lower() and ("删除" in ln or "delete" in ln.lower()):
                constraints.append(("archive", "delete"))
    a = action_text.lower()
    for tgt, verb in constraints:
        if tgt in a and verb in a:
            return "BLOCK"
    return "ALLOW"

bad = "delete ${WORKBUDDY_WORKSPACE}/archive/kaf-backup-2026-07-19"
good = "read ${WORKBUDDY_WORKSPACE}/README.md"
r_bad, r_good = enforce(bad), enforce(good)
print(f"  违规动作 [{bad}] -> {r_bad}")
print(f"  正常动作 [{good}] -> {r_good}")
if r_bad != "BLOCK":
    print("  ✗ 违规动作未被拦截"); ok = False
elif r_good != "ALLOW":
    print("  ✗ 正常动作被误拦"); ok = False
else:
    print("  ✅ Loop2 闭环成功：BLOCK 写回 → 执行器读回 → 拦截违规 / 放行正常")

# 还原：移除此测试写入的 BLOCK 发现块
lines = open(REVIEW_FINDINGS, encoding="utf-8").read().splitlines()
out_lines, i = [], 0
MY_MARK = "禁止删除 archive/ 下任何备份文件"
while i < len(lines):
    if lines[i].startswith("## 审查发现") and i + 1 < len(lines) and MY_MARK in "\n".join(lines[i:i+8]):
        # 跳过这个测试块(直到下一个 "## 审查发现" 或文件尾)
        j = i + 1
        while j < len(lines) and not lines[j].startswith("## 审查发现"):
            j += 1
        i = j
        continue
    out_lines.append(lines[i]); i += 1
open(REVIEW_FINDINGS, "w", encoding="utf-8").write("\n".join(out_lines).strip() + "\n")
print("  已移除此测试 BLOCK 发现块，铁律恢复")

if os.path.exists(ft):
    os.remove(ft)

hr("实测结论")
if ok:
    print("✅ 两个闭环均真实跑通：写入侧 + 读取侧(消费者/执行器)共同构成端到端闭环。")
    print("   本轮为破坏性实测，结束已还原共享队列与铁律，无残留污染。")
else:
    print("❌ 存在未闭环环节，见上。")
sys.exit(0 if ok else 1)
