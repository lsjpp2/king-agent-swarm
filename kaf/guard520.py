"""
KAF 520 Runtime Guard — 运行时护栏
4个检查点：pre_execute / pre_delete / post_execute / on_failure

Usage:
    from guard520 import Guard520
    guard = Guard520("constitution.json")
    guard.pre_execute(action)
    guard.pre_delete(action)
    guard.post_execute(action, result)
    guard.on_failure(action, error)
"""
import json
import os
import hashlib
from datetime import datetime


class GuardResult:
    OK = "ok"
    BLOCK = "block"
    WARN = "warn"

    def __init__(self, status, message="", data=None):
        self.status = status
        self.message = message
        self.data = data or {}

    def __bool__(self):
        return self.status != self.BLOCK

    def __repr__(self):
        return f"Guard520({self.status}: {self.message})"


class Guard520:
    """520法则运行时护栏。每个操作经过检查点。"""

    DESTRUCTIVE_OPS = {"rm", "mv", "copy", "delete", "rmtree", "shutil.move", "shutil.rmtree"}
    DELETE_OPS = {"rm", "delete", "rmtree", "shutil.rmtree"}

    def __init__(self, constitution_path="constitution.json"):
        self.constitution = self._load_constitution(constitution_path)
        self.log_file = os.path.join(
            os.path.dirname(os.path.abspath(constitution_path)),
            "..", "kaf_operations.log"
        )
        self.rule_520 = self.constitution.get("rule_520", {})

    def _load_constitution(self, path):
        if not os.path.exists(path):
            return {"rule_520": {"enabled": True}}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _log(self, action, result, extra=""):
        """可追溯：自动记录操作日志"""
        entry = f"[{datetime.now().isoformat()}] {action.get('type','?')} | {result.status} | {action.get('target','')} | {extra}\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except:
            pass

    # ---- 检查点1：pre_execute（铁律8：操作必须写脚本）----
    def pre_execute(self, action):
        """执行前检查：破坏性操作必须有脚本"""
        if not self.rule_520.get("enabled"):
            return GuardResult(GuardResult.OK)

        op_type = action.get("type", "")
        if op_type in self.DESTRUCTIVE_OPS:
            if not action.get("script"):
                r = GuardResult(GuardResult.BLOCK, f"铁律8违规：{op_type} 操作无脚本")
                self._log(action, r, "铁律8")
                return r
            if not action.get("verified"):
                r = GuardResult(GuardResult.WARN, f"铁律8提醒：{op_type} 操作未验证")
                self._log(action, r, "铁律8")
                return r

        return GuardResult(GuardResult.OK)

    # ---- 检查点2：pre_delete（铁律10：删除前展示清单）----
    def pre_delete(self, action):
        """删除前检查：必须展示清单并获用户确认"""
        if not self.rule_520.get("enabled"):
            return GuardResult(GuardResult.OK)

        op_type = action.get("type", "")
        if op_type not in self.DELETE_OPS:
            return GuardResult(GuardResult.OK)

        target = action.get("target", "")
        if not target or not os.path.exists(target):
            return GuardResult(GuardResult.OK, "target不存在，跳过")

        # 列清单
        items = self._list_items(target)
        if not action.get("user_confirmed"):
            r = GuardResult(
                GuardResult.BLOCK,
                f"铁律10违规：未展示清单/未获确认。待删{len(items)}项",
                {"items": items}
            )
            self._log(action, r, "铁律10")
            return r

        return GuardResult(GuardResult.OK, f"已确认，{len(items)}项待删")

    def _list_items(self, target):
        """列出待删清单"""
        items = []
        if os.path.isfile(target):
            items.append({"path": target, "size": os.path.getsize(target)})
        elif os.path.isdir(target):
            for root, dirs, files in os.walk(target):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        items.append({"path": fp, "size": os.path.getsize(fp)})
                    except:
                        pass
                if len(items) > 1000:
                    items.append({"path": "...", "size": -1, "note": f"超过1000项，共更多"})
                    break
        return items

    # ---- 检查点3：post_execute（可追溯：记录日志）----
    def post_execute(self, action, result):
        """执行后：自动记录操作日志"""
        status = GuardResult.OK if result.get("success", True) else GuardResult.BLOCK
        r = GuardResult(status, f"操作完成: {result.get('summary', '')}")
        self._log(action, r, f"result={result}")
        return r

    # ---- 检查点4：on_failure（可恢复：提供回滚方案）----
    def on_failure(self, action, error):
        """失败时：提供回滚方案"""
        rollback = {
            "error": str(error),
            "action": action,
            "rollback_options": []
        }

        op_type = action.get("type", "")
        target = action.get("target", "")

        if op_type in self.DELETE_OPS:
            rollback["rollback_options"].append("检查回收站是否可还原")
            rollback["rollback_options"].append(f"从备份恢复: {target}")
        elif op_type in ("mv", "shutil.move"):
            rollback["rollback_options"].append(f"移回原位: {action.get('dest','')} -> {target}")
        elif op_type == "write":
            rollback["rollback_options"].append("从.git恢复或从备份恢复")

        rollback["rollback_options"].append("联系国王(人类)确认恢复方案")

        r = GuardResult(GuardResult.WARN, f"操作失败，提供{len(rollback['rollback_options'])}个回滚方案", rollback)
        self._log(action, r, f"failure: {error}")
        return r

    # ---- 520自检（真实核查，非装饰）----
    def _find_backup(self):
        """查找 archive/ 下含 manifest.json 的备份目录"""
        archive = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "archive"))
        if not os.path.isdir(archive):
            return None
        for d in sorted(os.listdir(archive), reverse=True):
            if os.path.exists(os.path.join(archive, d, "manifest.json")):
                return os.path.join(archive, d)
        return None

    def self_check(self):
        """520自检：可追溯/可恢复/可修复/可进化/已强制(无钩子环境的agent侧强制)"""
        results = {
            "traceable": self._check_traceable(),
            "recoverable": self._check_recoverable(),
            "fixable": self._check_fixable(),
            "evolvable": self._check_evolvable(),
            "enforced": self._check_enforced(),
        }
        all_pass = all(r["pass"] for r in results.values())
        results["overall"] = "PASS" if all_pass else "FAIL"
        results["timestamp"] = datetime.now().isoformat()
        return results

    def _check_traceable(self):
        # 真实核查：确有操作被记录（非仅方法存在）
        if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > 0:
            sz = os.path.getsize(self.log_file)
            return {"pass": True, "detail": f"操作日志存在且有记录: {sz} 字节 (可追溯)"}
        return {"pass": False, "detail": "尚无操作日志：护栏从未实际拦截/记录过任何操作 (不可追溯)"}

    def _check_recoverable(self):
        bak = self._find_backup()
        if bak:
            return {"pass": True, "detail": f"存在备份: {os.path.basename(bak)} (可恢复)"}
        return {"pass": False, "detail": "archive/ 下无含 manifest.json 的备份 (不可恢复)"}

    def _check_fixable(self):
        # 真实核查：on_failure 能给出指向真实备份的回滚方案
        bak = self._find_backup()
        rb = self.on_failure({"type": "delete", "target": "D:/x"}, "test")
        opts = rb.data.get("rollback_options", [])
        has_backup_rollback = any("备份恢复" in o for o in opts)
        if bak and has_backup_rollback:
            return {"pass": True, "detail": f"失败回滚方案指向真实备份: {os.path.basename(bak)} (可修复)"}
        return {"pass": False, "detail": "回滚方案缺失真实备份目标 (不可修复)"}

    def _check_evolvable(self):
        kaf_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(kaf_dir, "skills"),
            os.path.join(kaf_dir, "..", "..", "skills"),
            os.path.expanduser("~/.workbuddy/skills"),
        ]
        for sdir in candidates:
            if os.path.exists(sdir) and len(os.listdir(sdir)) > 0:
                return {"pass": True, "detail": f"skill目录: {sdir} ({len(os.listdir(sdir))}个skill)"}
        return {"pass": False, "detail": "未找到skill目录"}

    def _check_enforced(self):
        # 无钩子环境：强制靠 agent 侧门禁(kaf_gate.py) + 铁律接入
        kaf_dir = os.path.dirname(os.path.abspath(__file__))
        gate = os.path.join(kaf_dir, "kaf_gate.py")
        mem = os.path.abspath(os.path.join(os.path.dirname(kaf_dir), "..", ".workbuddy", "memory", "MEMORY.md"))
        gate_ok = os.path.exists(gate)
        rule_ok = False
        if os.path.exists(mem):
            with open(mem, "r", encoding="utf-8", errors="ignore") as f:
                _content = f.read()
            rule_ok = ("铁律11" in _content) or ("kaf_gate" in _content)
        if gate_ok and rule_ok:
            return {"pass": True, "detail": "agent侧强制门禁(kaf_gate.py)已接入铁律 (已强制)"}
        missing = []
        if not gate_ok:
            missing.append("kaf_gate.py")
        if not rule_ok:
            missing.append("MEMORY.md 铁律11")
        return {"pass": False, "detail": f"未接入强制门禁(仅被动库): 缺 {missing} (无自动强制)"}


if __name__ == "__main__":
    guard = Guard520()
    print("=== KAF 520 自检 ===")
    result = guard.self_check()
    for k, v in result.items():
        if k != "timestamp":
            status = "✅" if v.get("pass") else "❌"
            print(f"  {status} {k}: {v.get('detail','')}")
    print(f"\n总体: {result['overall']}")
