"""KAF DeepSeek Harness Adapter — 把 KAF 治理层挂载到 DeepSeek Harness (dsh)。

装载依据（来自 deepseek-ai/deepseek-harness @ master，149k★ / MIT / dsh 0.1.0-rc.7）：
- 核心范式 "Everything is a Plugin"，运行时由 Cordis 驱动：插件向共享 ctx 贡献
  services / typed events / reversible effects；无特权核心，注册即效应，卸载可回退。
- 能力接缝(seam) = Service Definition + Service Provider + Consumer 三者齐备。
- 工具执行流水线（docs/subsystems/tools.md）：
    tools/pre-execute (allow|deny|ask 瀑布)
      → ToolGuard (单调拒绝，只缩权不翻盘)
      → tools/execute (around-dispatch，仅可换 signal)
      → tools/post-execute (accept|block)
      → tools/result (不可变权威结果)
- agent/* 与 tools/* 是 live 拦截点；agent/pre-step 决定模型看到什么。
- 会话日志(ctx.sessions) append-only SessionEvent；不变式「模型可见 ⟺ 已记录」。
- ctx.llm 路由：每调用按 provider+model 路由，llm/stream 瀑布可拦截/短路，按适配器实例隔离。
- ctx.subagents：子代理委派（spawn/fork/acp/codex/claude-code/dsh-sdk 多 provider）。
- ctx.sandbox：landlock-run 沙箱后端，消费者在 spawn 前包裹 argv。

关键对齐结论：
- dsh 拥有**原生事件瀑布**作为一等拦截点，因此 KAF 的强制层在 dsh 上应做成
  **原生监听者插件**（native_event），而非 WorkBuddy 平台的 agent 侧门禁。
- 本适配器把 KAF 的 520 护栏 / 治理层 / 经济学路由 / 记忆完整性 接到 dsh 的接缝上：
    * kaf_gate  → dsh tools/pre-execute 监听者（破坏性操作前 MUST 过 KAF 门禁）
    * Governance.evaluate() → 更重的 tools/pre-execute + agent/pre-step 监听者（策略即代码/急停/审计归因）
    * economics_router → ctx.llm 路由建议器（frontier/balanced/economy → provider+model）
    * memory_integrity → 保护 dsh 的 cordis.patch.yml / 会话日志不被覆盖
    * coordinator 状态 → 映射到 dsh 的 agent registry（ctx.agents）

本文件是「装载」的产物：它让 KAF 能以一个 dsh 插件的形式存在，在 dsh 的
tools/* 与 agent/* 瀑布中强制 KAF 治理。
"""

import json
import os
import sys

KAF_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_kaf_path():
    """把 kaf/ 加入 sys.path，使 KAF 的治理模块可被本适配器懒加载。"""
    if KAF_DIR not in sys.path:
        sys.path.insert(0, KAF_DIR)


# dsh 原生事件 → KAF 事件的映射（dsh 事件瀑布名 → KAF 治理关注点）
DSH_EVENT_MAP = {
    "tools/pre-execute": "pre:execute",      # 工具执行前：KAF 门禁 + 治理
    "agent/pre-step": "pre:step",            # 模型可见前：KAF 治理 + 进智检索注入
    "tools/post-execute": "post:execute",    # 工具执行后：结果审计
    "agent/turn-stopping": "turn:stopping",  # 回合结束前：可熔断
    "session/event": "session:log",          # 会话日志：不可变审计
}


class DeepSeekHarnessAdapter:
    """KAF 平台适配器：DeepSeek Harness (dsh) 实现。"""

    platform_name = "deepseek_harness"

    def __init__(self, harness_home=None, shared_dir=None):
        # dsh harness home（Cordis 配置、profile、bundles 落地处）
        self.harness_home = harness_home or os.environ.get(
            "DSH_HOME", os.path.join(os.path.expanduser("~"), ".dsh")
        )
        # KAF 共享根（共享账本 / 派发队列 / 治理审计链）
        self.shared_dir = shared_dir or os.environ.get(
            "KAF_SHARED_DIR", os.path.join(KAF_DIR, "shared")
        )
        os.makedirs(self.shared_dir, exist_ok=True)
        # KAF 宪法（治理真相源）
        self.constitution_path = os.path.join(KAF_DIR, "constitution.json")

    # ── PlatformAdapter 接口实现 ──────────────────────────────────────────

    def read_constitution(self):
        """读取 KAF 宪法（constitution.json）。

        dsh 的组合配方（profile + bundle + cordis.patch.yml）是「能力组合」，
        KAF 的 constitution.json 是「治理宪法」——二者正交，本适配器以 KAF 宪法为治理真相源。
        """
        if os.path.exists(self.constitution_path):
            with open(self.constitution_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def read_memory(self, key=None):
        """读取记忆。

        优先读 dsh 会话日志（ctx.sessions 投影）若可用，否则回退 KAF 记忆文件。
        dsh 不变式：模型可见 ⟺ 已记录 → 会话日志即最权威的「发生了什么」。
        """
        # 回退：KAF 记忆文件
        memory_file = os.path.join(self.shared_dir, "MEMORY.md")
        if not os.path.exists(memory_file):
            return ""
        with open(memory_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if key:
            import re
            m = re.search(rf"##\s*{key}.*?(?=\n##\s|\Z)", content, re.DOTALL)
            return m.group(0) if m else ""
        return content

    def write_memory(self, key, value, protect_check=True):
        """写入记忆（含 KAF 520 保护检查）。

        映射到 dsh：任何对 cordis.patch.yml / 会话日志的写都是「受保护写」，
        须经 memory_integrity.protect_write 才允许，防止覆盖受保护内容。
        """
        memory_file = os.path.join(self.shared_dir, "MEMORY.md")
        if protect_check:
            _ensure_kaf_path()
            try:
                from memory_integrity import MemoryIntegrity
                mi = MemoryIntegrity(self.shared_dir)
                if not mi.protect_write(memory_file, value):
                    return {"success": False, "error": "520保护检查未通过：受保护内容不可删除"}
            except Exception as e:  # 模块缺失不阻断，但必须 loud fail
                return {"success": False, "error": f"520保护检查无法执行：{e}"}
        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(value)
        return {"success": True}

    def register_hook(self, event, callback=None):
        """dsh 拥有原生事件瀑布，强制层做成「原生监听者」而非 agent 侧门禁。

        返回把 KAF 治理挂到 dsh 事件瀑布的配方；监听器在 dsh 侧以 Cordis
        ctx.on('tools/pre-execute', listener) 注册，listener 调用本适配器的
        bridge_* 方法即可强制 KAF 门禁 / 治理。
        """
        dsh_event = None
        for dsh_ev, kaf_ev in DSH_EVENT_MAP.items():
            if kaf_ev == event or dsh_ev == event:
                dsh_event = dsh_ev
                break
        if not dsh_event:
            dsh_event = "tools/pre-execute"  # 默认挂到工具执行前
        return {
            "event": event,
            "platform": "deepseek_harness",
            "native_hook": True,  # ★ 与 WorkBuddy 的根本区别：dsh 有原生事件瀑布
            "enforcement": "native_event_listener",
            "dsh_event": dsh_event,
            "listener_recipe": (
                "ctx.on('%s', async (payload, next) => {\n"
                "  const r = await kafBridge.bridge_pre_execute(payload);\n"
                "  if (r.decision === 'deny') return { allow: false, reason: r.reason };\n"
                "  if (r.decision === 'ask') return { allow: false, ask: r.reason };\n"
                "  return next();\n"
                "});" % dsh_event
            ),
            "rule": "破坏性操作前 MUST 经 KAF 门禁；BLOCK 则 deny/ask，绝不可绕过",
        }

    def execute(self, action):
        """执行操作：经 dsh CLI/SDK 转发。

        实际执行由 dsh 的 agent loop / 插件处理；这里把 action 描述成 dsh 可调用的
        任务票，由 dsh 侧 consume（或经 dispatch 落到共享派发队列）。
        """
        return {"action": action, "platform": "deepseek_harness", "status": "forwarded_to_dsh"}

    def get_agent_id(self):
        """获取当前 Agent 身份。

        在 dsh 中，本适配器以「kaf-govern」治理插件身份存在（对应 ctx.agents 注册表的一项）。
        国王解析与 dsh 解耦：读取 KAF_KING 或回退到 dsh profile owner / OS 用户。
        """
        return os.environ.get("KAF_AGENT", "kaf-govern")

    def get_workspace(self):
        """获取当前工作区（dsh harness home）。"""
        return self.harness_home

    # v5.2 进化（方向2·路由落执行）：共享派发队列
    def dispatch(self, task, target_agent, role=None, cost_tier=None, est_cost=None):
        """路由落执行：把任务派发给目标 agent。

        映射到 dsh：写共享派发队列（KAF 跨平台路径），并附 dsh 子代理委派描述符
        （ctx.subagents 的某一 provider），目标 agent 在启动/被委派时读取执行。
        """
        import uuid
        from datetime import datetime

        queue_path = os.path.join(self.shared_dir, "dispatch_queue.json")
        ticket = {
            "id": uuid.uuid4().hex[:12],
            "task": task,
            "assigned_to": target_agent,
            "role": role,
            "cost_tier": cost_tier,
            "est_cost": est_cost,
            "dispatched_by": self.get_agent_id(),
            "dispatched_at": datetime.now().isoformat(timespec="seconds"),
            "status": "queued",
            # dsh 落地提示：用 ctx.subagents 的指定 provider 委派此任务
            "dsh_subagent_hint": {
                "provider": cost_tier or "subagent-spawn-in-process",
                "delegate": target_agent,
            },
        }
        queue = []
        if os.path.exists(queue_path):
            try:
                with open(queue_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                queue = data.get("queue", []) if isinstance(data, dict) else data
            except (json.JSONDecodeError, ValueError):
                queue = []
        queue.append(ticket)
        with open(queue_path, "w", encoding="utf-8") as f:
            json.dump({"queue": queue}, f, ensure_ascii=False, indent=2)
        return {"success": True, "ticket": ticket, "queue_path": queue_path}

    # dsh 任意 op → kaf_gate 接受的 op 归一化（防止 argparse 非法 choice 绕过门禁）
    OP_TO_GATE = {
        "delete": "delete", "rm": "delete", "rmtree": "delete",
        "move": "mv", "mv": "mv", "rename": "mv", "archive": "mv",
        "write": "write", "copy": "copy", "bulk_write": "write", "publish": "write",
    }

    # ── 桥接函数（装载的核心：把 KAF 治理翻译成 dsh 的 PreToolDecision 词汇） ──

    def bridge_pre_execute(self, exec_meta):
        """dsh tools/pre-execute 监听者调用：把 KAF 门禁+治理翻译成 dsh 的 PreToolDecision。

        exec_meta 形如：
            {"op": "delete|move|write|archive|rename|bulk_write|publish",
             "target": "<路径>", "confirmed": bool, "script": "<脚本路径>",
             "verified": bool, "content": "<新内容>", "agent": "<agent名>"}
        返回：
            {"decision": "allow"|"deny"|"ask", "reason": "...",
             "kaf_blocked": bool, "governance": {...}}
        """
        op = exec_meta.get("op", "execute")
        target = exec_meta.get("target", "")
        op = op or "execute"

        destructive = op in ("delete", "move", "archive", "rename", "bulk_write", "publish", "write")

        # 1) 非破坏性操作：放行（仍走 KAF 治理轻量层）
        if not destructive:
            return self._govern_decision(op, target, exec_meta, default_allow=True)

        # 2) 破坏性操作：MUST 过 KAF 门禁（kaf_gate.py check）
        _ensure_kaf_path()
        gate_result = self._run_kaf_gate(op, target, exec_meta)
        if gate_result.get("blocked"):
            return {
                "decision": "deny",
                "reason": "KAF 520 护栏拦截：" + gate_result.get("reason", "未授权破坏性操作"),
                "kaf_blocked": True,
                "governance": gate_result,
            }
        # 3) 门禁通过 → 再过治理层（策略即代码 / 急停 / 审计归因）
        return self._govern_decision(op, target, exec_meta, default_allow=False,
                                     gate_passed=True)

    def bridge_agent_pre_step(self, messages):
        """dsh agent/pre-step 监听者调用：在模型可见前注入 KAF 治理 + 进智检索。

        messages：模型即将看到的消息列表。
        返回：
            {"reject": bool, "rewritten": [...]|None,
             "inject": "<进智反模式注入块>", "reason": "..."}
        """
        # 进智脊柱：检索历史反模式注入上下文（kaf/cognition/retrieval_inject.py）
        inject_block = ""
        _ensure_kaf_path()
        try:
            from cognition.retrieval_inject import retrieve_antipatterns
            inject_block = retrieve_antipatterns() or ""
        except Exception:
            inject_block = ""  # 缺失不阻断，仅无注入
        # 治理层：检查 kill-switch 等全局熔断
        gov = self._governance_evaluate("model_step", exec_meta={"messages": len(messages) if isinstance(messages, list) else 0})
        if (gov.get("effect") or "").lower() == "deny":
            return {"reject": True, "rewritten": None, "inject": inject_block,
                    "reason": "KAF 治理层拒绝模型步：" + gov.get("reason", "")}
        return {"reject": False, "rewritten": None, "inject": inject_block, "reason": ""}

    def bridge_llm_route(self, task_type):
        """ctx.llm 路由建议器：把 KAF 经济学路由翻译成 dsh 的 provider+model。

        task_type：planner|worker|reviewer（来自 economics_router.classify）
        返回：{"provider": "...", "model": "...", "cost_tier": "frontier|balanced|economy"}
        """
        _ensure_kaf_path()
        try:
            from economics_router import EconomicsRouter
            r = EconomicsRouter()
            rec = r.route(task_type, None)
            cost_tier = (rec.get("cost_tier") if isinstance(rec, dict) else None) or "balanced"
        except Exception:
            cost_tier = "balanced"
        # dsh 路由语义：provider 路由 + model；这里给出按档位映射的推荐
        provider_map = {
            "frontier": ("deepseek-reasoner", "deepseek-reasoner"),
            "balanced": ("deepseek-chat", "deepseek-chat"),
            "economy": ("deepseek-chat", "deepseek-chat-lite"),
        }
        provider, model = provider_map.get(cost_tier, provider_map["balanced"])
        return {"provider": provider, "model": model, "cost_tier": cost_tier}

    # ── 内部工具 ──────────────────────────────────────────────────────────

    def _run_kaf_gate(self, op, target, exec_meta):
        """调用 kaf_gate.py check（与 WorkBuddy 适配器同机制，但此处由 dsh 原生监听触发）。

        op 归一化到 kaf_gate 接受的集合；returncode != 0（含 argparse 非法 choice 的退出码 2）
        一律视为 BLOCK —— 安全失败，杜绝绕过。
        """
        import subprocess
        gate = os.path.join(KAF_DIR, "kaf_gate.py")
        if not os.path.exists(gate):
            return {"blocked": True, "reason": "kaf_gate.py 缺失"}
        gop = self.OP_TO_GATE.get(op, "write")
        real = _real_target(exec_meta) or target
        cmd = [sys.executable, gate, "check", "--op", gop, "--target", real,
               "--constitution", self.constitution_path]
        if exec_meta.get("confirmed"):
            cmd.append("--confirmed")
        if exec_meta.get("reason"):
            cmd += ["--reason", exec_meta["reason"]]
        if exec_meta.get("script"):
            cmd += ["--script", exec_meta["script"]]
        if gop == "write" and exec_meta.get("content"):
            cmd += ["--content", exec_meta["content"]]
        r = subprocess.run(cmd, capture_output=True, text=True)
        # 非零退出（BLOCK=1 或 argparse 错误=2）→ 一律 BLOCK
        return {"blocked": r.returncode != 0, "reason": r.stdout.strip() or r.stderr.strip()}

    def _govern_decision(self, op, target, exec_meta, default_allow, gate_passed=False):
        """过 KAF 治理层（Governance.evaluate）。"""
        gov = self._governance_evaluate(op, exec_meta)
        effect = (gov.get("effect") or "").lower()
        if effect == "deny":
            return {"decision": "deny", "reason": "KAF 治理层：" + gov.get("reason", ""),
                    "kaf_blocked": True, "governance": gov}
        if effect == "ask":
            return {"decision": "ask", "reason": "KAF 治理层需人工确认：" + gov.get("reason", ""),
                    "kaf_blocked": False, "governance": gov}
        # ALLOW（或治理层不可用 → 回退默认）
        if default_allow or gate_passed:
            return {"decision": "allow", "reason": "KAF 门禁+治理通过",
                    "kaf_blocked": False, "governance": gov}
        return {"decision": "allow", "reason": "KAF 治理放行",
                "kaf_blocked": False, "governance": gov}

    def _governance_evaluate(self, action, exec_meta=None):
        """调用 governance.py 的 Governance.evaluate（若有）。

        治理层有零信任身份归因：须先 attest(agent_id)（等价于 dsh 插件挂载时
        向治理层断言自身身份），否则任何动作都会被 DENY。
        action 归一化到 policy 已知集合（archive/rename→move, bulk_write→write）。
        """
        _ensure_kaf_path()
        exec_meta = exec_meta or {}
        agent_id = exec_meta.get("agent") or self.get_agent_id()
        resource = _real_target(exec_meta) or exec_meta.get("target", "")
        # 归一化 action 到 policy 规则已知集合
        gov_action = {"archive": "move", "rename": "move", "bulk_write": "write"}.get(action, action)
        context = {
            "user_confirmed": bool(exec_meta.get("confirmed")),
            "has_script": bool(exec_meta.get("script")),
            "king_confirmed": bool(exec_meta.get("king_confirmed")),
        }
        try:
            from governance import Governance
            g = Governance(constitution_path=self.constitution_path,
                          state_dir=os.path.join(self.shared_dir, "governance"))
            g.attest(agent_id)  # dsh 插件挂载时 attest 自身身份
            res = g.evaluate(gov_action, agent_id=agent_id, resource=resource, context=context)
            return {"effect": res.status, "reason": res.reason, "attested": True,
                    "rule_id": getattr(res, "rule_id", None)}
        except Exception as e:
            # 治理层不可用：破坏性操作 MUST fail-closed 拒绝（520 铁律），
            # 绝不 fail-open；非破坏性操作允许默认通过。
            destructive = action in ("delete", "move", "archive", "rename",
                                     "bulk_write", "publish", "write")
            return {"effect": "DENY" if destructive else "ALLOW",
                    "reason": f"治理层未加载({e})，破坏性操作 fail-closed 拒绝",
                    "attested": False}


def _real_target(exec_meta):
    """从 exec_meta 抽取真实目标路径（兼容 dsh 的 exec 结构与 KAF 的 target 字段）。"""
    t = exec_meta.get("target", "")
    if isinstance(t, str):
        return t
    if isinstance(t, dict):
        return t.get("path") or t.get("name") or ""
    return ""


# 便于 dsh 侧以「插件」形式导入的工厂
def create_adapter(harness_home=None, shared_dir=None):
    return DeepSeekHarnessAdapter(harness_home=harness_home, shared_dir=shared_dir)


if __name__ == "__main__":
    # 自测：不依赖 dsh 运行时，验证桥接函数能正确 fallback 并强制 KAF 治理
    a = DeepSeekHarnessAdapter()
    print("[delete 无确认]      =>", a.bridge_pre_execute(
        {"op": "delete", "target": "/tmp/x", "confirmed": False}))
    print("[delete 已确认+脚本] =>", a.bridge_pre_execute(
        {"op": "delete", "target": "/tmp/x", "confirmed": True, "script": "del.py",
         "reason": "清理临时文件"}))
    print("[rename 已确认+脚本] =>", a.bridge_pre_execute(
        {"op": "rename", "target": "/tmp/a", "confirmed": True, "script": "mv.py",
         "reason": "重命名会话归档目录"}))
    print("[publish 无确认]     =>", a.bridge_pre_execute(
        {"op": "publish", "target": "draft", "confirmed": False}))
    print("[read]               =>", a.bridge_pre_execute(
        {"op": "read", "target": "/tmp/x"}))
    print("[llm_route/planner]  =>", a.bridge_llm_route("planner"))
    print("[agent_pre_step]     =>", a.bridge_agent_pre_step([{"role": "user", "content": "hi"}]))
    print("[dispatch]           =>", a.dispatch("测试任务", "worker-1", role="worker", cost_tier="economy"))
