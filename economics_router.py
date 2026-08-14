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

Usage:
    from economics_router import EconomicsRouter
    r = EconomicsRouter()
    r.route("重构支付模块的事务边界并评估兼容性风险")   # 返回推荐 agent + 真实成本估算
    r.calibrate("usage_log.json")                       # 据真实用量校准 ROLE_TOKEN_SHARE

CLI:
    python economics_router.py "<task>"        # 路由
    python economics_router.py calibrate        # 校准
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
        preferred = PREFERRED_TIER.get(task_type, "balanced")

        # 候选：role 匹配（reviewer 允许任意，planner/worker 必须 role 一致）
        candidates = []
        for aid, info in self.agents.items():
            if task_type in ("planner", "worker") and info.get("role") != task_type:
                continue
            candidates.append((aid, info))

        if not candidates:
            return {"error": f"无匹配角色 {task_type} 的候选 agent"}

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
        return {
            "task_type": task_type,
            "agent": chosen_id,
            "platform": chosen.get("platform", chosen_id),
            "role": chosen.get("role", task_type),
            "cost_tier": chosen.get("cost_tier", "?"),
            "est_relative_cost": est,
            "reason": (
                f"{task_type}类任务需{preferred}档；命中 {len(candidates)} 个候选，"
                f"按'质量达标优先+成本最低'选定（相对成本指数 {self._agent_cost_index(chosen_id)}）"
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
        print('Usage: python economics_router.py "<task>" | calibrate')
        return 1
    if sys.argv[1] == "calibrate":
        r = EconomicsRouter()
        print(json.dumps(r.calibrate(), ensure_ascii=False, indent=2))
        return 0
    r = EconomicsRouter()
    out = r.route(" ".join(sys.argv[1:]))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
