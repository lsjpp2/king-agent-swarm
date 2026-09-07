#!/usr/bin/env python3
"""
KAF Economics Router — 模型经济学路由（任务分类 + 成本-质量权衡分配）

参考 Cursor《智能体蜂群与新的模型经济学》(2026-07-20)：
- 质量相近但成本可差 10 倍
- Worker 占 69%~90% token 但用便宜模型；Planner token 少却用贵的前沿模型（占 ~2/3 成本）
- 真正需要前沿智能的环节极少（初始拆解/设计决策/权衡），一旦收敛为明确指令，便宜模型照执行即可

v5.2 进化（方向1·路由真实化）：
- 成本不再靠硬编码 COST_WEIGHT，而读 **pricing.json** 的真实相对计价（每 agent 每 1M token 价）
- 新增 **calibrate()**：读 usage_log.json（各 agent 实际 token 消耗）动态重算 ROLE_TOKEN_SHARE，
  写入 calibration.json 供 route() 实时采纳 → 路由随真实用量自我校准

v5.6 进化（GitHub 同类项目补检索回流，见 RESEARCH_github_peers_v556.md）：
- **T2 复杂度分级路由**（借鉴 zscole/model-hierarchy-skill，345★）：
  仅按 role 选档会把"简单活派给贵模型"。新增 routine/moderate/complex 三级评估，
  目标分布 80/15/5；routine 自动降档省钱，complex 自动升档保质。
- **T1 四层 token 治理**（借鉴 vagkaratzas/token-saviour，10★，方法论价值 >> star）：
  token 成本有 4 个互不重叠的层 —— code_read(-66%) / command_output(-65%) /
  prose_output(-6%) / code_gen(-40%)，四层堆叠实测 -69.6%。
  **Ponytail 只覆盖 code_gen 一层**，v5.5 曾误当"全能省 token 方案"，v5.6 明确边界。

Usage:
    from economics_router import EconomicsRouter
    r = EconomicsRouter()
    r.route("重构支付模块的事务边界并评估兼容性风险")   # 推荐 agent + 成本 + 复杂度 + token 层
    r.assess_complexity("批量替换文案")                  # v5.6 三级复杂度
    r.token_plan("定位并修复登录接口的空指针")            # v5.6 四层 token 治理方案
    r.calibrate("usage_log.json")                       # 据真实用量校准 ROLE_TOKEN_SHARE

CLI:
    python economics_router.py "<task>"        # 路由
    python economics_router.py calibrate        # 校准
    python economics_router.py tokens "<task>" # v5.6 四层 token 治理方案
"""
import os
import sys
import json


# 候选 agent（与 coordinator.json 同步；路由时以 coordinator 实际注册为准）
DEFAULT_AGENTS = {
    "workbuddy": {"platform": "WorkBuddy", "role": "planner", "cost_tier": "balanced"},
    "opencode":  {"platform": "OpenCode Desktop", "role": "worker", "cost_tier": "economy"},
    "claude":    {"platform": "Claude", "role": "planner", "cost_tier": "frontier"},
    "kimi":      {"platform": "Kimi", "role": "worker", "cost_tier": "economy"},
    "cursor":    {"platform": "Cursor", "role": "worker", "cost_tier": "balanced"},
}

# 任务类型关键词（命中计数 → 分类为 planner/worker/reviewer）
KEYWORDS = {
    "planner": ["设计", "架构", "规划", "权衡", "决策", "拆解", "评估", "方案", "重构决策",
                "design", "architect", "plan", "tradeoff", "decide", "evaluate"],
    "worker": ["翻译", "批量", "执行", "生成", "格式化", "搬运", "替换", "扫描", "转换",
               "translate", "batch", "execute", "generate", "format", "convert"],
    "reviewer": ["审查", "复核", "检查", "审计", "review", "audit", "verify"],
}

# 每角色偏好的成本档（质量达标前提下尽量便宜）
PREFERRED_TIER = {"planner": "frontier", "worker": "economy", "reviewer": "balanced"}

# 思考型模型（Ponytail 极简决策梯在此类模型上成本/延迟反向，L2 自动 bypass）
# 来源：Ponytail 官方基准 — GPT-5.5 上 token/成本反而上升
THINKING_MODELS = {
    "gpt-5.5", "gpt-5.5-mini", "gpt-5.5-nano",
    "o3", "o4", "o4-mini",
    "claude-opus-4.5-thinking", "claude-4-opus-thinking",
    "deepseek-r2-thinking",
}

# ---------- v5.6 · T2 复杂度分级路由（80/15/5） ----------
# 来源：zscole/model-hierarchy-skill（345★）——绝大多数任务不需要前沿模型
TIER_RANK = {"economy": 1, "balanced": 2, "frontier": 3}
RANK_TIER = {v: k for k, v in TIER_RANK.items()}

COMPLEXITY_TIERS = {
    "routine":  {"target_share": 0.80, "tier": "economy",
                 "desc": "机械/单点/有明确先例，便宜模型足够"},
    "moderate": {"target_share": 0.15, "tier": "balanced",
                 "desc": "多步骤但路径清楚，中档模型胜任"},
    "complex":  {"target_share": 0.05, "tier": "frontier",
                 "desc": "跨模块/高风险/需权衡设计，才动前沿模型"},
}

# 复杂度信号词（complex 权重 2，moderate 权重 1）
COMPLEXITY_SIGNALS = {
    "complex": ["架构", "跨模块", "迁移", "并发", "分布式", "事务", "权衡", "兼容性",
                "数据一致", "性能瓶颈", "安全边界", "拆解", "设计方案",
                "architecture", "migrate", "concurrency", "distributed",
                "transaction", "tradeoff", "consistency", "bottleneck"],
    "moderate": ["多个", "批量", "联动", "集成", "接口", "流程", "模块", "组件",
                 "调试", "重构", "对接", "integrate", "pipeline", "module",
                 "component", "debug", "refactor"],
}

# ---------- v5.6 · T1 四层 token 治理 ----------
# 来源：vagkaratzas/token-saviour（10★）——token 成本分 4 个互不重叠层，
# 各层由不同工具主导；Ponytail 只管 code_gen 一层（v5.5 曾误当全能方案）
TOKEN_LAYERS = {
    "code_read": {
        "order": 1, "desc": "读码/检索代码上下文（最大单层开销）",
        "tool": "serena (MCP · LSP 符号级检索，只取需要的符号而非整文件)",
        "measured_saving": 0.66, "kaf_status": "未集成（外部 MCP，集成成本高）",
        "signals": ["读", "检索", "查找", "定位", "理解", "分析", "排查", "溯源",
                    "grep", "search", "locate", "trace", "inspect"],
    },
    "command_output": {
        "order": 2, "desc": "命令/构建/测试输出回填",
        "tool": "rtk (输出裁剪，只回填有信息量的行)",
        "measured_saving": 0.65, "kaf_status": "未集成（外部 MCP）",
        "signals": ["运行", "执行", "构建", "编译", "测试", "日志", "输出", "报错",
                    "build", "test", "log", "run", "ci", "compile"],
    },
    "prose_output": {
        "order": 3, "desc": "散文/说明性输出（省得最少，别指望）",
        "tool": "caveman (精简语体)",
        "measured_saving": 0.06, "kaf_status": "未集成（收益极低，优先级最末）",
        "signals": ["文档", "说明", "报告", "总结", "解释", "readme", "doc",
                    "report", "summary", "explain"],
    },
    "code_gen": {
        "order": 4, "desc": "代码生成（Ponytail 唯一覆盖层）",
        "tool": "Ponytail L2 决策梯",
        "measured_saving": 0.40, "kaf_status": "✅ 已集成（v5.5 · kaf ponytail）",
        "signals": ["写", "实现", "生成", "函数", "脚本", "类", "组件", "代码",
                    "新增", "重构", "改造", "修复", "封装",
                    "implement", "write", "function", "class", "component",
                    "code", "refactor", "fix"],
    },
}
# 四层堆叠实测总削减（token-saviour 2026-07 复测口径）
STACKED_SAVING = 0.696

# 兜底常量（pricing.json 缺失时使用）
FALLBACK_COST = {"frontier": 10.0, "balanced": 3.0, "economy": 1.0}


class EconomicsRouter:
    def __init__(self, coord_path=None, pricing_path=None):
        base = os.path.dirname(os.path.abspath(__file__))
        self.coord_path = coord_path or os.path.join(base, "coordinator.json")
        self.pricing_path = pricing_path or os.path.join(base, "pricing.json")
        self.calibration_path = os.path.join(base, "calibration.json")
        self.agents = self._load_coordinator()
        self.pricing = self._load_pricing()
        self.token_share = self._load_calibration()

    # ---------- 加载 ----------
    def _load_coordinator(self):
        if os.path.exists(self.coord_path):
            try:
                with open(self.coord_path, "r", encoding="utf-8") as f:
                    c = json.load(f)
                out = {}
                for aid, info in c.get("coordinators", {}).items():
                    out[aid] = {
                        "platform": info.get("platform", aid),
                        "role": info.get("role", "worker"),
                        "cost_tier": info.get("cost_tier", "balanced"),
                    }
                if out:
                    return out
            except Exception:
                pass
        return dict(DEFAULT_AGENTS)

    def _load_pricing(self):
        if os.path.exists(self.pricing_path):
            try:
                with open(self.pricing_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _load_calibration(self):
        """读 calibration.json；不存在则用 pricing 的 role_estimated_tokens 默认占比"""
        if os.path.exists(self.calibration_path):
            try:
                with open(self.calibration_path, "r", encoding="utf-8") as f:
                    cal = json.load(f)
                if "role_token_share" in cal:
                    return cal["role_token_share"]
            except Exception:
                pass
        est = (self.pricing.get("role_estimated_tokens", {})
               or {"planner": 8000, "worker": 40000, "reviewer": 4000})
        total = sum(est.values()) or 1
        return {k: round(v / total, 3) for k, v in est.items()}

    # ---------- 分类 ----------
    def classify(self, task_text):
        text = (task_text or "").lower()
        scores = {k: 0 for k in KEYWORDS}
        for role, kws in KEYWORDS.items():
            for kw in kws:
                if kw.lower() in text:
                    scores[role] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "worker"

    # ---------- v5.6 · T2 复杂度分级 ----------
    def assess_complexity(self, task_text):
        """三级复杂度评估（routine/moderate/complex），目标分布 80/15/5。

        评分：complex 信号 ×2，moderate 信号 ×1，长文本加权。
        判定：complex_score>=2 → complex；>=1 或 moderate>=2 → moderate；否则 routine。
        """
        text = (task_text or "").lower()
        hits = {"complex": [], "moderate": []}
        for lvl, kws in COMPLEXITY_SIGNALS.items():
            for kw in kws:
                if kw.lower() in text:
                    hits[lvl].append(kw)
        c_score = len(hits["complex"]) * 2
        m_score = len(hits["moderate"])
        # 长任务描述本身是复杂度信号（需求越啰嗦越可能牵扯多处）
        n = len(task_text or "")
        if n > 260:
            c_score += 2
        elif n > 120:
            m_score += 1

        if c_score >= 2:
            level = "complex"
        elif c_score >= 1 or m_score >= 2:
            level = "moderate"
        else:
            level = "routine"

        spec = COMPLEXITY_TIERS[level]
        return {
            "level": level,
            "complex_score": c_score,
            "moderate_score": m_score,
            "signals_hit": {k: v for k, v in hits.items() if v},
            "preferred_tier": spec["tier"],
            "target_share": spec["target_share"],
            "desc": spec["desc"],
        }

    # ---------- v5.6 · T1 四层 token 治理 ----------
    def classify_token_layer(self, task_text):
        """判定任务主要落在哪个 token 开销层（4 层互不重叠）。"""
        text = (task_text or "").lower()
        scored = []
        for name, spec in TOKEN_LAYERS.items():
            hit = [kw for kw in spec["signals"] if kw.lower() in text]
            if hit:
                scored.append((name, len(hit), hit))
        if not scored:
            return {"primary": None, "hit_layers": [],
                    "note": "无明确 token 层信号；按默认全链路治理"}
        # 命中数降序，同分按 order 升序（读码层优先，单层收益最大）
        scored.sort(key=lambda x: (-x[1], TOKEN_LAYERS[x[0]]["order"]))
        primary = scored[0][0]
        return {
            "primary": primary,
            "primary_tool": TOKEN_LAYERS[primary]["tool"],
            "primary_saving": TOKEN_LAYERS[primary]["measured_saving"],
            "primary_status": TOKEN_LAYERS[primary]["kaf_status"],
            "hit_layers": [{"layer": n, "hits": c, "keywords": kw} for n, c, kw in scored],
            "note": "Ponytail 仅覆盖 code_gen 层；其余层需外部工具，KAF 当前未集成",
        }

    def token_plan(self, task_text=None):
        """输出四层 token 治理全景方案（含本任务命中层标注）。"""
        cls = self.classify_token_layer(task_text) if task_text else {"primary": None, "hit_layers": []}
        hit_names = {h["layer"] for h in cls.get("hit_layers", [])}
        layers = []
        for name, spec in sorted(TOKEN_LAYERS.items(), key=lambda x: x[1]["order"]):
            layers.append({
                "layer": name,
                "order": spec["order"],
                "desc": spec["desc"],
                "tool": spec["tool"],
                "measured_saving": spec["measured_saving"],
                "kaf_status": spec["kaf_status"],
                "hit_by_task": name in hit_names,
            })
        covered = [l["layer"] for l in layers if l["kaf_status"].startswith("✅")]
        return {
            "task": task_text,
            "primary_layer": cls.get("primary"),
            "layers": layers,
            "stacked_saving": STACKED_SAVING,
            "kaf_covered": covered,
            "kaf_uncovered": [l["layer"] for l in layers if l["layer"] not in covered],
            "principle": ("token 成本分 4 个互不重叠层，单靠 Ponytail 只吃到 code_gen 一层(-40%)；"
                          f"四层堆叠实测可达 -{STACKED_SAVING * 100:.1f}%"),
            "source": "vagkaratzas/token-saviour（v5.6 补检索回流）",
        }

    # ---------- 成本计算（真实计价） ----------
    def _agent_cost_index(self, agent_id):
        """返回该 agent 的相对成本指数（读 pricing.json，缺失回退 FALLBACK_COST）"""
        info = self.agents.get(agent_id, {})
        tier = info.get("cost_tier", "balanced")
        p = self.pricing.get("agents", {}).get(agent_id, {})
        return float(p.get("relative_index", FALLBACK_COST.get(tier, 3.0)))

    def _estimate_cost(self, role, agent_id):
        """估计相对成本 = 该角色预估 token 占比 × 该 agent 单位成本指数"""
        share = self.token_share.get(role, 0.1)
        idx = self._agent_cost_index(agent_id)
        return round(share * idx, 3)

    # ---------- 路由 ----------
    def route(self, task_text):
        if not task_text or not task_text.strip():
            return {"error": "任务描述为空"}
        task_type = self.classify(task_text)
        role_tier = PREFERRED_TIER.get(task_type, "balanced")

        # v5.6 · T2 复杂度分级校正：routine 降档省钱，complex 升档保质，moderate 不动
        cx = self.assess_complexity(task_text)
        role_rank = TIER_RANK.get(role_tier, 2)
        cx_rank = TIER_RANK.get(cx["preferred_tier"], 2)
        if cx["level"] == "routine":
            final_rank = min(role_rank, cx_rank)
        elif cx["level"] == "complex":
            final_rank = max(role_rank, cx_rank)
        else:
            final_rank = role_rank
        preferred = RANK_TIER.get(final_rank, role_tier)
        tier_adjusted = preferred != role_tier
        adjust_note = ""
        if tier_adjusted:
            direction = "降档省钱" if final_rank < role_rank else "升档保质"
            adjust_note = (f"；T2 复杂度[{cx['level']}]触发{direction}："
                           f"{role_tier}→{preferred}")

        # 候选：role 匹配（reviewer 允许任意，planner/worker 必须 role 一致）
        candidates = []
        for aid, info in self.agents.items():
            if task_type in ("planner", "worker") and info.get("role") != task_type:
                continue
            candidates.append((aid, info))

        if not candidates:
            return {"error": f"无匹配角色 {task_type} 的候选 agent"}

        # v5.6 · T2 跨 role 升/降档：若复杂度校正后的目标档在本 role 内无候选，
        # 放宽 role 过滤引入该档 agent。否则"5% 复杂任务必须上前沿 / 80% 简单任务必须下沉便宜档"
        # 会被 role 过滤器架空（v5.6 实测发现的架空 bug）。
        role_filter_relaxed = False
        if tier_adjusted and not any(i.get("cost_tier") == preferred for _, i in candidates):
            have = {a for a, _ in candidates}
            extra = [(aid, info) for aid, info in self.agents.items()
                     if info.get("cost_tier") == preferred and aid not in have]
            if extra:
                candidates.extend(extra)
                role_filter_relaxed = True
                adjust_note += f"（跨 role 放宽以取得 {preferred} 档候选）"

        def score(item):
            aid, info = item
            tier = info.get("cost_tier", "balanced")
            # 质量达标（命中偏好档优先）+ 成本最低
            quality = 1.0 if tier == preferred else 0.6
            cost = self._agent_cost_index(aid)
            return (quality, -cost)  # 先质量后成本

        candidates.sort(key=score, reverse=True)
        chosen_id, chosen = candidates[0]
        est = self._estimate_cost(task_type, chosen_id)
        # Ponytail L2 预执行决策层模型感知（v5.5）：思考型模型上极简梯反向
        pt_applicable = chosen_id not in THINKING_MODELS
        pt_note = "" if pt_applicable else "（⚠️ 选定 agent 为思考型，Ponytail L2 自动 bypass）"
        # v5.6 · T1 四层 token 治理：标注本任务主要开销层 + 该层归谁管
        tk = self.classify_token_layer(task_text)
        return {
            "task_type": task_type,
            "agent": chosen_id,
            "platform": chosen.get("platform", chosen_id),
            "role": chosen.get("role", task_type),
            "cost_tier": chosen.get("cost_tier", "?"),
            "est_relative_cost": est,
            "ponytail_applicable": pt_applicable,
            # --- v5.6 新增字段 ---
            "complexity": cx["level"],
            "complexity_desc": cx["desc"],
            "complexity_target_share": cx["target_share"],
            "role_preferred_tier": role_tier,
            "final_preferred_tier": preferred,
            "tier_adjusted": tier_adjusted,
            "role_filter_relaxed": role_filter_relaxed,
            "token_layer": tk.get("primary"),
            "token_layer_tool": tk.get("primary_tool"),
            "token_layer_saving": tk.get("primary_saving"),
            "token_layer_status": tk.get("primary_status"),
            "reason": (
                f"{task_type}类任务需{preferred}档；命中 {len(candidates)} 个候选，"
                f"按'质量达标优先+成本最低'选定（相对成本指数 {self._agent_cost_index(chosen_id)}）"
                f"{adjust_note}{pt_note}"
            ),
        }

    # ---------- 校准（方向1核心） ----------
    def calibrate(self, usage_log_path=None):
        """读 usage_log.json（[{agent, tokens}]），重算各 role 真实 token 占比，
        写入 calibration.json。route() 下次直接采纳。"""
        if usage_log_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            usage_log_path = os.path.join(base, "usage_log.json")
        if not os.path.exists(usage_log_path):
            return {"calibrated": False, "reason": f"usage_log 不存在: {usage_log_path}",
                    "tip": "由各 agent 上报真实 token 消耗到 usage_log.json 后重跑"}

        try:
            with open(usage_log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception as e:
            return {"calibrated": False, "reason": f"解析失败: {e}"}

        role_tokens = {}
        for rec in logs:
            aid = rec.get("agent")
            toks = rec.get("tokens", 0)
            role = self.agents.get(aid, {}).get("role", "worker")
            role_tokens[role] = role_tokens.get(role, 0) + toks

        total = sum(role_tokens.values()) or 1
        new_share = {r: round(t / total, 3) for r, t in role_tokens.items()}
        for r in ("planner", "worker", "reviewer"):
            new_share.setdefault(r, 0.0)

        cal = {
            "calibrated_at": __import__("datetime").datetime.now().isoformat(),
            "source": os.path.basename(usage_log_path),
            "role_token_share": new_share,
            "previous": self.token_share,
        }
        with open(self.calibration_path, "w", encoding="utf-8") as f:
            json.dump(cal, f, indent=2, ensure_ascii=False)
        self.token_share = new_share
        return {"calibrated": True, "role_token_share": new_share,
                "note": "下一路由将采纳真实 token 占比"}


def main():
    if len(sys.argv) < 2:
        print('Usage: python economics_router.py "<task>" | calibrate | tokens "<task>"')
        return 1
    if sys.argv[1] == "calibrate":
        r = EconomicsRouter()
        print(json.dumps(r.calibrate(), ensure_ascii=False, indent=2))
        return 0
    if sys.argv[1] == "tokens":
        r = EconomicsRouter()
        task = " ".join(sys.argv[2:]) or None
        print(json.dumps(r.token_plan(task), ensure_ascii=False, indent=2))
        return 0
    r = EconomicsRouter()
    out = r.route(" ".join(sys.argv[1:]))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
