#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAF v5.3 Governance Layer — 策略即代码 + 急停开关 + 防篡改审计 + Agent 身份归因

吸收自 microsoft/agent-governance-toolkit（与 KAF 概念最接近的对照系）的可工程化治理洞见：
  - Policy Enforcement：声明式 policy.json，每次动作经策略评估，结构化 DENY(带原因)
  - Kill-switch：全局急停（共享状态）
  - Zero-trust-ish Identity：HMAC 风格 agent 身份断言（动作可归因）
  - Tamper-evident Audit：hash-chained append-only 审计链（可验证完整性）

与 KAF v5.2 的 520 硬编码护栏互补：guard520 是"运行时检查点"，本模块是"声明式策略 + 急停 + 审计 + 归因"。
宣称=实现：见 governance_selftest.py，真跑通 deny/kill-switch/audit/attestation。
"""
import json
import os
import re
import hmac
import hashlib
from datetime import datetime


DEFAULT_POLICY = {
    "default_effect": "allow",
    "attestation": {"enabled": True, "secret_env": "KAF_GOV_SECRET", "secret": "kaf-shared-secret"},
    "rules": [
        {
            "id": "gov-520-write-protect",
            "effect": "deny",
            "match": {"action": ["write", "delete", "move"], "resource_regex": ".*(MEMORY\\.md|520|铁律|constitution\\.json)"},
            "require": {"king_confirmed": True},
            "reason": "宪法/520/铁律/记忆为受保护资产，须国王显式确认(king_confirmed)方可写/删/移"
        },
        {
            "id": "gov-destructive-needs-script",
            "effect": "deny",
            "match": {"action": ["delete", "move", "rm", "rmtree"]},
            "require": {"has_script": True},
            "reason": "破坏性操作须先写脚本(铁律8)"
        },
        {
            "id": "gov-delete-needs-confirm",
            "effect": "deny",
            "match": {"action": ["delete", "rm", "rmtree"]},
            "require": {"user_confirmed": True},
            "reason": "删除前须展示清单并获用户确认(铁律10)"
        },
        {
            "id": "gov-external-send-needs-approval",
            "effect": "deny",
            "match": {"action": ["send_email", "publish", "external_call"]},
            "require": {"user_confirmed": True},
            "reason": "对外发送/发布须用户确认"
        },
        {
            "id": "gov-read-allow",
            "effect": "allow",
            "match": {"action": ["read", "list"]},
            "reason": "只读操作默认放行"
        }
    ]
}


class Decision:
    ALLOW = "allow"
    DENY = "deny"

    def __init__(self, status, reason="", rule_id=None, audit_id=None, data=None):
        self.status = status
        self.reason = reason
        self.rule_id = rule_id
        self.audit_id = audit_id
        self.data = data or {}

    def __bool__(self):
        return self.status == self.ALLOW

    def __repr__(self):
        return f"Decision({self.status}: {self.reason})"


class PolicyEngine:
    """声明式策略即代码评估器。DENY 优先（任一 deny 命中即拒绝）。"""

    def __init__(self, policy=None, policy_path=None):
        if policy is not None:
            self.policy = policy
        elif policy_path and os.path.exists(policy_path):
            with open(policy_path, "r", encoding="utf-8") as f:
                self.policy = json.load(f)
        else:
            self.policy = json.loads(json.dumps(DEFAULT_POLICY))
        self.default_effect = self.policy.get("default_effect", "allow")

    def _selectors_match(self, match, action, resource, context):
        """仅匹配选择器（action / resource_regex / agent），不校验 require。"""
        acts = match.get("action")
        if acts and action not in acts:
            return False
        rre = match.get("resource_regex")
        if rre and resource is not None and not re.search(rre, resource):
            return False
        ag = match.get("agent")
        if ag:
            ags = ag if isinstance(ag, list) else [ag]
            if context.get("agent") not in ags:
                return False
        return True

    def _require_met(self, require, context):
        if not require:
            return True
        return all(context.get(k) == v for k, v in require.items())

    def evaluate(self, action, resource=None, context=None):
        context = context or {}
        # 1) DENY 优先：选择器命中 且 豁免条件(require)未全部满足 → 拒绝
        for rule in self.policy.get("rules", []):
            if rule.get("effect") != "deny":
                continue
            if self._selectors_match(rule.get("match", {}), action, resource, context):
                if not self._require_met(rule.get("require"), context):
                    return Decision(Decision.DENY, rule.get("reason", "deny"), rule.get("id"))
        # 2) ALLOW：选择器命中 且 require 满足 → 放行
        for rule in self.policy.get("rules", []):
            if rule.get("effect") == "allow":
                if self._selectors_match(rule.get("match", {}), action, resource, context):
                    if self._require_met(rule.get("require"), context):
                        return Decision(Decision.ALLOW, rule.get("reason", "allow"), rule.get("id"))
        # 3) 默认
        return Decision(self.default_effect, f"default_effect={self.default_effect}", "default")


class AuditChain:
    """防篡改审计链：append-only，每条记录 hash( prev_hash + content )。可 verify()。"""

    def __init__(self, audit_path):
        self.audit_path = audit_path
        self._ensure_dir()

    def _ensure_dir(self):
        d = os.path.dirname(self.audit_path)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

    def _prev_hash(self):
        if not os.path.exists(self.audit_path):
            return "0" * 64
        with open(self.audit_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        if not lines:
            return "0" * 64
        try:
            last = json.loads(lines[-1])
            return last.get("hash", "0" * 64)
        except Exception:
            return "0" * 64

    def append(self, entry):
        prev = self._prev_hash()
        payload = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        h = hashlib.sha256((prev + "|" + payload).encode("utf-8")).hexdigest()
        record = {"hash": h, "prev": prev, "entry": entry, "ts": datetime.now().isoformat()}
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return h[:16]

    def verify(self):
        """验证整链完整性。返回 (ok, broken_at_index_or_None)。"""
        if not os.path.exists(self.audit_path):
            return (True, None)
        with open(self.audit_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        prev = "0" * 64
        for i, line in enumerate(lines):
            try:
                rec = json.loads(line)
            except Exception:
                return (False, i)
            expected = hashlib.sha256((prev + "|" + json.dumps(rec["entry"], ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()
            if rec.get("hash") != expected or rec.get("prev") != prev:
                return (False, i)
            prev = rec.get("hash")
        return (True, None)

    def tail(self, n=10):
        if not os.path.exists(self.audit_path):
            return []
        with open(self.audit_path, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip()]
        out = []
        for line in lines[-n:]:
            try:
                rec = json.loads(line)
                e = rec["entry"]
                out.append(f"[{rec['ts']}] {e.get('status','?'):4s} | {e.get('action','')} | {e.get('agent','')} | {e.get('resource','')} | {e.get('rule_id','')} | {e.get('reason','')}")
            except Exception:
                pass
        return out


class Governance:
    """v5.3 治理编排：kill-switch + 身份归因 + 策略即代码 + 520检查点 + 防篡改审计。"""

    def __init__(self, constitution_path="constitution.json", policy_path=None,
                 state_dir=None, policy=None):
        self.constitution_path = constitution_path
        # 策略
        if policy is not None:
            self.policy_engine = PolicyEngine(policy=policy)
            self.policy_path = None
        else:
            self.policy_path = policy_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "policy.json")
            self.policy_engine = PolicyEngine(policy_path=self.policy_path)
        # 状态目录（共享优先，本地回退）
        self.state_dir = self._resolve_state_dir(state_dir)
        self.killswitch_file = os.path.join(self.state_dir, "kill_switch.json")
        self.audit_path = os.path.join(self.state_dir, "audit_chain.log")
        self.audit = AuditChain(self.audit_path)
        # 身份证明密钥
        secret = self.policy_engine.policy.get("attestation", {}).get("secret", "kaf-shared-secret")
        self._secret = os.environ.get(
            self.policy_engine.policy.get("attestation", {}).get("secret_env", "KAF_GOV_SECRET"), secret)
        self._attested = set()

    def _resolve_state_dir(self, state_dir):
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
            return state_dir
        shared = os.path.join(os.environ.get("KAF_SHARED_DIR", "${KAF_SHARED_DIR}"), "governance")
        if os.path.isdir(os.path.dirname(shared)):
            os.makedirs(shared, exist_ok=True)
            return shared
        local = os.path.join(os.getcwd(), ".kaf_governance")
        os.makedirs(local, exist_ok=True)
        return local

    # ---- 身份归因（HMAC 风格）----
    def attest(self, agent_id):
        """agent 向治理层断言身份，返回 token（后续 evaluate 须携带）。"""
        nonce = datetime.now().isoformat()
        token = hmac.new(self._secret.encode("utf-8"),
                         (agent_id + "|" + nonce).encode("utf-8"), hashlib.sha256).hexdigest()
        self._attested.add(agent_id)
        return token

    def verify_attestation(self, agent_id, token, nonce):
        exp = hmac.new(self._secret.encode("utf-8"),
                       (agent_id + "|" + nonce).encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(exp, token or "")

    # ---- kill-switch ----
    def set_kill_switch(self, on):
        with open(self.killswitch_file, "w", encoding="utf-8") as f:
            json.dump({"active": bool(on), "ts": datetime.now().isoformat()}, f)

    def kill_switch_active(self):
        if not os.path.exists(self.killswitch_file):
            return False
        try:
            with open(self.killswitch_file, "r", encoding="utf-8") as f:
                return json.load(f).get("active", False)
        except Exception:
            return False

    # ---- 主评估 ----
    def evaluate(self, action, agent_id=None, resource=None, context=None):
        context = dict(context or {})
        if agent_id:
            context["agent"] = agent_id

        # 1) kill-switch 最高优先
        if self.kill_switch_active():
            d = Decision(Decision.DENY, "kill-switch 已激活：全局急停", "kill-switch")
            self._audit(action, agent_id, resource, d)
            return d

        # 2) 身份归因要求
        att = self.policy_engine.policy.get("attestation", {})
        if att.get("enabled") and agent_id and agent_id not in self._attested:
            # 允许带 token 现场验证
            tok = context.pop("attest_token", None)
            nonce = context.pop("attest_nonce", None)
            if not (tok and self.verify_attestation(agent_id, tok, nonce or "")):
                d = Decision(Decision.DENY, f"agent '{agent_id}' 未通过身份归因(须先 attest)", "attestation")
                self._audit(action, agent_id, resource, d)
                return d

        # 3) 520 运行时检查点（若有 constitution）
        guard_block = self._run_guard520(action, context)
        if guard_block:
            d = Decision(Decision.DENY, guard_block, "guard520")
            self._audit(action, agent_id, resource, d)
            return d

        # 4) 策略即代码
        d = self.policy_engine.evaluate(action, resource, context)
        self._audit(action, agent_id, resource, d)
        return d

    def _run_guard520(self, action, context):
        try:
            from guard520 import Guard520
            if not os.path.exists(self.constitution_path):
                return None
            g = Guard520(self.constitution_path)
            act = {"type": action, "target": context.get("resource"),
                   "script": context.get("has_script"), "verified": context.get("has_script"),
                   "user_confirmed": context.get("user_confirmed")}
            if action in ("delete", "rm", "rmtree"):
                r = g.pre_delete(act)
            elif action in ("write", "move", "delete", "rm", "rmtree", "copy"):
                r = g.pre_execute(act)
            else:
                return None
            if not r:
                return r.message
        except Exception:
            return None
        return None

    def _audit(self, action, agent_id, resource, decision):
        self.audit.append({
            "action": action, "agent": agent_id or "?",
            "resource": resource or "", "status": decision.status,
            "rule_id": decision.rule_id, "reason": decision.reason,
        })


if __name__ == "__main__":
    import sys
    gov = Governance()
    print("=== KAF v5.3 Governance ===")
    print(f"  kill-switch: {'ON' if gov.kill_switch_active() else 'off'}")
    print(f"  audit chain valid: {gov.audit.verify()[0]}")
    print(f"  state_dir: {gov.state_dir}")
