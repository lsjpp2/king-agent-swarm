#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KAF v5.3 Governance 自测 — 宣称=实现，真跑通 deny / kill-switch / attestation / audit。

覆盖：
  1) 受保护资产删除无 king_confirmed → DENY
  2) 受保护资产删除有 king_confirmed+user_confirmed+has_script → ALLOW
  3) kill-switch ON → 任何动作 DENY；OFF → 恢复
  4) 未归因 agent → DENY；attest 后 → 通过
  5) 审计链完整性：追加后 verify()=True；篡改中行后 verify()=False
"""
import os
import sys
import json
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from governance import Governance, Decision

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def main():
    tmp = tempfile.mkdtemp(prefix="kaf_gov_test_")
    print(f"[self-test] state_dir = {tmp}\n")

    g = Governance(state_dir=tmp)
    g.attest("worker1")  # 真实用法：agent 启动时归因一次

    # 1) 受保护资产删除，无确认 → DENY
    d = g.evaluate("delete", agent_id="worker1", resource="D:/x/MEMORY.md",
                   context={"user_confirmed": True, "has_script": True})
    check("受保护资产(MEMORY.md)删除无 king_confirmed → DENY", not d and d.rule_id == "gov-520-write-protect")

    # 2) 受保护资产删除，全确认 → ALLOW
    d2 = g.evaluate("delete", agent_id="worker1", resource="D:/x/MEMORY.md",
                    context={"user_confirmed": True, "has_script": True, "king_confirmed": True})
    check("受保护资产删除 + king_confirmed+user_confirmed+has_script → ALLOW", bool(d2) and d2.status == "allow")

    # 3) kill-switch
    g.set_kill_switch(True)
    dk = g.evaluate("read", agent_id="worker1", resource="D:/x/file")
    check("kill-switch ON → 任何动作 DENY", not dk and dk.rule_id == "kill-switch")
    g.set_kill_switch(False)
    dk2 = g.evaluate("read", agent_id="worker1", resource="D:/x/file")
    check("kill-switch OFF → 恢复 ALLOW", bool(dk2))

    # 4) 身份归因
    d_un = g.evaluate("write", agent_id="stranger", resource="D:/x/a.txt", context={"has_script": True})
    check("未归因 agent → DENY(attestation)", not d_un and d_un.rule_id == "attestation")
    tok = g.attest("stranger")  # 该实例内归因成功
    d_at = g.evaluate("write", agent_id="stranger", resource="D:/x/a.txt",
                      context={"has_script": True, "attest_token": tok, "attest_nonce": ""})
    check("attest 后 → 通过(非 attestation 拒绝)", d_at.rule_id != "attestation")

    # 5) 审计链完整性
    ok1, _ = g.audit.verify()
    check("审计链追加后 verify()=True", ok1)
    # 篡改中行
    with open(g.audit_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) >= 3:
        mid = len(lines) // 2
        tampered = lines[mid].replace('"status": "allow"', '"status": "DENIED_FAKE"', 1)
        if tampered == lines[mid]:
            tampered = lines[mid].replace('"status": "deny"', '"status": "allow_FAKE"', 1)
        lines[mid] = tampered
        with open(g.audit_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        ok2, broken = g.audit.verify()
        check("篡改审计链中行后 verify()=False（防篡改生效）", (not ok2) and broken is not None)
    else:
        check("审计链含足够条目以供篡改测试", False)

    print(f"\n[self-test] PASS={PASS} FAIL={FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
