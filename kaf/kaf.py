#!/usr/bin/env python3
"""
KAF CLI — King-Agent Framework 命令行工具

Usage:
    kaf init      — 初始化KAF（生成constitution.json + 注册指纹）
    kaf check     — 520自检（可追溯/可恢复/可修复/可进化/已强制）
    kaf verify    — 记忆完整性校验（指纹+drift检测）
    kaf guard     — 打印运行时护栏检查点说明
    kaf honest    — 诚实扫描（检测文档/代码残留的'自动拦截'假话）
    kaf rotate <agent> — 宰相轮值
    kaf status    — 查看集群状态
    kaf route "<task>" — 模型经济学路由：推荐 planner/worker + 成本估算
    kaf review <file>  — 多视角审查：security/correctness/style/economics 叠加
    kaf dispatch "<task>" [target_agent] — 路由落执行：推荐并派发到共享队列
"""
import sys
import os
import json

# 确保能import同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_init():
    """初始化KAF"""
    print("=" * 50)
    print("  KAF Init — King-Agent Framework 初始化")
    print("=" * 50)

    constitution = os.path.join(os.getcwd(), "constitution.json")
    if os.path.exists(constitution):
        print("  ⚠️  constitution.json 已存在，跳过")
    else:
        # 从模板复制
        template = os.path.join(os.path.dirname(__file__), "constitution.json")
        if os.path.exists(template):
            import shutil
            shutil.copy(template, constitution)
            print(f"  ✅ 生成 constitution.json")
        else:
            print("  ❌ 模板不存在，请手动创建 constitution.json")
            return 1

    # 注册记忆指纹
    from memory_integrity import MemoryIntegrity
    mi = MemoryIntegrity()
    for fname in ["META.md", "MEMORY.md"]:
        fp = os.path.join(mi.memory_dir, fname)
        if os.path.exists(fp):
            h = mi.register(fp)
            print(f"  ✅ 注册指纹 {fname}: {h[:16]}...")

    # 生成本地 coordinator.json（gitignored，不提交），使 status/rotate 可用
    coord_file = os.path.join(os.getcwd(), "coordinator.json")
    if not os.path.exists(coord_file):
        coord_tmpl = {
            "version": "5.0",
            "current_coordinator": "king",
            "coordinators": {
                "king": {"title": "国王(人类)", "status": "active"},
            },
            "rotation_history": [],
        }
        with open(coord_file, "w", encoding="utf-8") as f:
            json.dump(coord_tmpl, f, indent=2, ensure_ascii=False)
        print(f"  ✅ 生成 coordinator.json（本地，已 gitignore）")

    print("\n  KAF初始化完成。")
    print("  下一步: kaf check  # 运行520自检")
    return 0


def cmd_check():
    """520自检"""
    from guard520 import Guard520
    guard = Guard520()

    print("=" * 50)
    print("  KAF 520 自检")
    print("=" * 50)

    result = guard.self_check()
    for k in ["traceable", "recoverable", "fixable", "evolvable", "enforced"]:
        v = result.get(k, {})
        status = "✅" if v.get("pass") else "❌"
        print(f"  {status} {k}: {v.get('detail', '')}")

    print(f"\n  总体: {result.get('overall', '?')}")
    return 0 if result.get("overall") == "PASS" else 1


def cmd_verify():
    """记忆完整性校验"""
    from memory_integrity import MemoryIntegrity
    mi = MemoryIntegrity()

    print("=" * 50)
    print("  KAF 记忆完整性校验")
    print("=" * 50)

    result = mi.verify()
    print(f"  {result['summary']}")

    for f in result.get("failed", []):
        print(f"  ❌ {f['file']}: {f['reason']}")

    for f in result.get("missing", []):
        print(f"  ❌ {f['file']}: {f['reason']}")

    for f in result.get("passed", []):
        print(f"  ✅ {f}")

    drift = mi.drift_check()
    if drift["drifted"]:
        print(f"\n  ⚠️  检测到Drift！建议检查记忆文件是否被未授权修改。")
        return 1
    else:
        print(f"\n  ✅ 无Drift，记忆完整。")
        return 0


def cmd_guard():
    """打印运行时护栏检查点说明"""
    print("=" * 50)
    print("  KAF Guard — 运行时护栏检查点")
    print("=" * 50)

    hooks = [
        ("pre:delete", "铁律10：删除前展示清单+用户确认"),
        ("pre:destructive_op", "铁律8：破坏性操作必须有脚本"),
        ("post:write_memory", "铁律9：记忆数字实地核查"),
        ("startup", "记忆完整性：指纹校验"),
    ]

    for event, desc in hooks:
        print(f"  {event:30s} → {desc}")

    print("\n  强制层接入方式：")
    print("  - 有原生 hook 接口的平台：PreToolUse hook 自动调用上述检查点")
    print("  - WorkBuddy 等无 hook 平台（已实测无 hooks.json/hook 字段）：")
    print("    agent 侧强制门禁 kaf_gate.py —— 删/移/覆盖前 MUST 过此门禁并服从 BLOCK")
    print("  参考 adapters/_template.py 实现各平台 register_hook；")
    print("  adapters/workbuddy.py 已写实 agent 侧策略（不再写无人读取的 hooks.json）")
    return 0


def cmd_rotate(agent_name):
    """宰相轮值"""
    coord_file = os.path.join(os.getcwd(), "coordinator.json")
    if not os.path.exists(coord_file):
        print(f"  ❌ coordinator.json 不存在")
        return 1

    with open(coord_file, "r", encoding="utf-8") as f:
        coord = json.load(f)

    if agent_name not in coord.get("coordinators", {}):
        print(f"  ❌ Agent '{agent_name}' 不在注册表中")
        print(f"  已注册: {list(coord.get('coordinators', {}).keys())}")
        return 1

    old = coord["current_coordinator"]
    coord["current_coordinator"] = agent_name
    coord["coordinators"][old]["status"] = "standby"
    coord["coordinators"][agent_name]["status"] = "active"
    coord["rotation_history"].append({
        "agent": agent_name,
        "since": __import__("datetime").datetime.now().isoformat(),
        "reason": "king_command",
        "appointed_by": "king",
        "replaced": old
    })

    with open(coord_file, "w", encoding="utf-8") as f:
        json.dump(coord, f, indent=2, ensure_ascii=False)

    print(f"  ✅ 宰相轮值: {old} → {agent_name}")
    print(f"  {agent_name} 已成为当前宰相（3票）")
    return 0


def cmd_status():
    """查看集群状态"""
    coord_file = os.path.join(os.getcwd(), "coordinator.json")
    if not os.path.exists(coord_file):
        print("  ❌ coordinator.json 不存在，请先 kaf init")
        return 1

    with open(coord_file, "r", encoding="utf-8") as f:
        coord = json.load(f)

    print("=" * 50)
    print("  KAF 集群状态")
    print("=" * 50)
    print(f"  版本: {coord.get('version', '?')}")
    print(f"  当前宰相: {coord.get('current_coordinator', '?')}")
    print(f"\n  Agents:")
    for aid, info in coord.get("coordinators", {}).items():
        status = info.get("status", "?")
        role = info.get("role", "-")
        tier = info.get("cost_tier", "-")
        marker = "👑" if aid == coord.get("current_coordinator") else "  "
        print(f"    {marker} {aid:15s} | {info.get('title',''):28s} | {role:8s} | {tier:8s} | {status}")

    print(f"\n  轮值历史: {len(coord.get('rotation_history', []))} 次")
    return 0


# 历史假话黑名单（曾出现在 KAF 文档/代码里，制造"自动拦截"的虚假宣称）
LIE_PHRASES = [
    "运行时hook拦截",
    "PreToolUse hook执行",
    "护栏通过PreToolUse",
    "写入 ~/.workbuddy/hooks.json",
    "打印hook配置",
    "自动拦截违规操作",
    "hook自动拦截",
]


def cmd_honest():
    """诚实扫描：检测文档/代码中残留的'自动拦截'假话（防宣称=实现回归）"""
    kaf_dir = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(kaf_dir)
    scan_dirs = [kaf_dir]
    for d in ["docs"]:
        p = os.path.join(parent, d)
        if os.path.isdir(p):
            scan_dirs.append(p)

    hits = []
    for base in scan_dirs:
        for root, dirs, files in os.walk(base):
            if ".git" in dirs:
                dirs.remove(".git")
            for fn in files:
                if not fn.endswith((".py", ".md", ".json", ".txt")):
                    continue
                fp = os.path.join(root, fn)
                if os.path.basename(fp) == "kaf.py":
                    continue  # 跳过扫描器自身（含 LIE_PHRASES 定义与说明文本）
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            for ph in LIE_PHRASES:
                                if ph in line:
                                    hits.append((fp, i, ph))
                except Exception:
                    pass

    print("=" * 50)
    print("  KAF 诚实扫描（防'宣称=实现'假话）")
    print("=" * 50)
    if not hits:
        print("  ✅ 未发现残留假话（运行时hook拦截/自动拦截等）")
        return 0
    print(f"  ❌ 发现 {len(hits)} 处疑似假话：")
    for fp, i, ph in hits:
        print(f"    {fp}:{i}  «{ph}»")
    print("\n  => 上述措辞会误导用户以为 KAF 在 hook-less 平台自动拦截；")
    print("     请改为'有原生hook走hook，无hook平台走agent侧强制门禁kaf_gate.py'。")
    return 1


def cmd_route(task_text):
    """模型经济学路由（Economics Router）"""
    from economics_router import EconomicsRouter
    router = EconomicsRouter()
    res = router.route(task_text)
    if "error" in res:
        print(f"  ❌ {res['error']}")
        return 1
    print("=" * 50)
    print("  KAF 经济学路由")
    print("=" * 50)
    print(f"  任务类型: {res['task_type']}")
    print(f"  推荐 Agent: {res['agent']} ({res['platform']})")
    print(f"  角色: {res['role']} | 成本档: {res['cost_tier']}")
    print(f"  相对成本估算: {res['est_relative_cost']}")
    print(f"  理由: {res['reason']}")
    return 0


def cmd_review(file_path, perspectives=None):
    """多视角审查编排（Multi-perspective Review）"""
    from review import MultiReview
    mr = MultiReview(perspectives)
    out = mr.suggest(file_path)
    if "error" in out:
        print(f"  ❌ {out['error']}")
        return 1
    print("=" * 50)
    print("  KAF 多视角审查")
    print("=" * 50)
    print(f"  产物: {out['artifact']}")
    print(f"  审查视角数: {out['review_count']}")
    print(f"  原则: {out['principle']}")
    for t in out["tasks"]:
        print(f"    - {t['perspective']}: {t['focus']}")
    return 0


def cmd_review_commit(findings_path):
    """审查闭环（方向3）：消费 findings.json，BLOCK 结论写回共享铁律/review_findings.md。"""
    from review import MultiReview
    if not os.path.exists(findings_path):
        print(f"  ❌ findings 文件不存在: {findings_path}")
        return 1
    with open(findings_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    mr = MultiReview()
    out = mr.commit(results)
    print("=" * 50)
    print("  KAF 审查闭环 (Review Commit)")
    print("=" * 50)
    print(f"  verdict: {out['verdict']}")
    if out.get("written"):
        print(f"  ✅ BLOCK 发现已写回共享 Field Guide: {mr.REVIEW_FINDINGS}")
    else:
        print(f"  无需写回（verdict={out['verdict']}）")
    return 0


def cmd_dispatch(task_text, target=None):
    """路由落执行（Route → Dispatch）：先 route 推荐，再派发到共享队列。

    v5.2 进化（方向2·路由落执行）：route 只推荐，dispatch 才真正交付。
    """
    from economics_router import EconomicsRouter
    from adapters.workbuddy import WorkBuddyAdapter

    router = EconomicsRouter()
    res = router.route(task_text)
    if "error" in res:
        print(f"  ❌ {res['error']}")
        return 1

    assigned = target or res["agent"]
    adapter = WorkBuddyAdapter()
    r = adapter.dispatch(
        task=task_text,
        target_agent=assigned,
        role=res["role"],
        cost_tier=res["cost_tier"],
        est_cost=res["est_relative_cost"],
    )
    print("=" * 50)
    print("  KAF 路由落执行 (Dispatch)")
    print("=" * 50)
    print(f"  任务类型: {res['task_type']}")
    print(f"  推荐 Agent: {res['agent']} ({res['platform']})  成本档: {res['cost_tier']}")
    print(f"  实际派发至: {assigned}")
    if r.get("success"):
        print(f"  ✅ 已写入共享派发队列: {r['queue_path']}")
        print(f"     票号: {r['ticket']['id']}  状态: {r['ticket']['status']}")
    else:
        print(f"  ❌ 派发失败: {r}")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0

    cmd = sys.argv[1]
    if cmd == "init":
        return cmd_init()
    elif cmd == "check":
        return cmd_check()
    elif cmd == "verify":
        return cmd_verify()
    elif cmd == "guard":
        return cmd_guard()
    elif cmd == "honest":
        return cmd_honest()
    elif cmd == "rotate":
        if len(sys.argv) < 3:
            print("  Usage: kaf rotate <agent_name>")
            return 1
        return cmd_rotate(sys.argv[2])
    elif cmd == "status":
        return cmd_status()
    elif cmd == "route":
        if len(sys.argv) < 3:
            print('  Usage: kaf route "<task>"')
            return 1
        return cmd_route(" ".join(sys.argv[2:]))
    elif cmd == "review":
        if len(sys.argv) < 3:
            print("  Usage: kaf review <file> [perspective...]")
            return 1
        return cmd_review(sys.argv[2], sys.argv[3:] or None)
    elif cmd == "review-commit":
        if len(sys.argv) < 3:
            print("  Usage: kaf review-commit <findings.json>")
            return 1
        return cmd_review_commit(sys.argv[2])
    elif cmd == "dispatch":
        if len(sys.argv) < 3:
            print('  Usage: kaf dispatch "<task>" [target_agent]')
            return 1
        # 允许第二个位置参数指定 target agent
        task = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else None
        # 若 task 含空格，sys.argv[2:] 可能是被拆开的；合并除最后的 target
        if target is not None and len(sys.argv) > 4:
            task = " ".join(sys.argv[2:-1])
            target = sys.argv[-1]
        return cmd_dispatch(task, target)
    else:
        print(f"  Unknown command: {cmd}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
