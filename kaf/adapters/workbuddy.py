"""KAF WorkBuddy Adapter — WorkBuddy平台适配器

将KAF治理层接入WorkBuddy（类VS Code Electron应用）。
"""
import json
import os
import re
from .base import PlatformAdapter


class WorkBuddyAdapter(PlatformAdapter):
    platform_name = "workbuddy"

    def __init__(self, workspace=None):
        self.workspace = workspace or (os.environ.get("WORKBUDDY_WORKSPACE") or os.path.join(os.path.expanduser("~"), "workbuddy-workspace"))
        self.home = os.path.expanduser("~/.workbuddy")
        self.memory_dir = os.path.join(self.workspace, ".workbuddy", "memory")
        self.constitution_path = os.path.join(self.workspace, "projects/kaf/constitution.json")

    def read_constitution(self):
        if os.path.exists(self.constitution_path):
            with open(self.constitution_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def read_memory(self, key=None):
        memory_file = os.path.join(self.home, "MEMORY.md")
        if not os.path.exists(memory_file):
            return ""
        with open(memory_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if key:
            # 简单的markdown段落提取
            match = re.search(rf"##\s*{re.escape(key)}.*?(?=\n##\s|\Z)", content, re.DOTALL)
            return match.group(0) if match else ""
        return content

    def write_memory(self, key, value, protect_check=True):
        memory_file = os.path.join(self.home, "MEMORY.md")

        # 520保护检查：防止删除受保护段落
        if protect_check and os.path.exists(memory_file):
            from memory_integrity import MemoryIntegrity
            mi = MemoryIntegrity(self.memory_dir)
            if not mi.protect_write(memory_file, value):
                return {"success": False, "error": "520保护检查未通过：受保护内容不可删除"}

        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(value)
        return {"success": True}

    def register_hook(self, event, callback=None):
        """WorkBuddy 平台无原生 hook 接口（已实测：~/.workbuddy 无 hooks.json，
        settings.json 无 hook 字段，app.asar 搜 PreToolUse/hook 零结果）。
        因此 KAF 在此平台的强制层为 AGENT 侧门禁：agent 在每次破坏性操作前
        必须调用 kaf_gate.py 并服从其结果。本方法返回该策略，不再写无人读取的 hooks.json。
        """
        gate = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kaf_gate.py")
        return {
            "event": event,
            "platform": "workbuddy",
            "native_hook": False,
            "enforcement": "agent_side_gate",
            "gate_command": f'python "{gate}" check --op <delete|move|write> --target "<path>" [--confirmed]',
            "rule": "破坏性操作前 MUST 跑 kaf_gate.py；BLOCK 则停止并展示清单，绝不可绕过",
        }

    def agent_side_gate(self, op, target, confirmed=False, script="", verified=False, content=""):
        """实际调用门禁（agent 侧强制入口）。返回 blocked=True 时操作须停止。"""
        import subprocess
        import sys
        gate = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kaf_gate.py")
        cmd = [sys.executable, gate, "check", "--op", op, "--target", target]
        if confirmed:
            cmd.append("--confirmed")
        if script:
            cmd += ["--script", script]
        if verified:
            cmd.append("--verified")
        if content:
            cmd += ["--content", content]
        r = subprocess.run(cmd, capture_output=True, text=True)
        return {"returncode": r.returncode, "stdout": r.stdout.strip(), "blocked": r.returncode == 1}

    def execute(self, action):
        """执行操作（通过WorkBuddy的Bash/Write等工具）"""
        # 实际执行由WorkBuddy的agent loop处理
        # 这里返回操作描述，由调用方转发给agent
        return {"action": action, "platform": "workbuddy", "status": "forwarded"}

    # v5.2 进化（方向2·路由落执行）：共享派发队列根目录
    # 公开技能：共享根目录用环境变量 KAF_SHARED_DIR 配置，默认回退作者本机路径（向后兼容）
    SHARED_ROOT = os.environ.get("KAF_SHARED_DIR", "${KAF_SHARED_DIR}")
    DISPATCH_QUEUE = os.path.join(SHARED_ROOT, "dispatch_queue.json")

    def dispatch(self, task, target_agent, role=None, cost_tier=None, est_cost=None):
        """路由落执行：把任务派发给目标 agent。

        v5.2 进化（方向2·路由落执行）：route 只推荐，dispatch 才真正交付。
        本方法将任务票写入共享派发队列 ${KAF_SHARED_DIR}/dispatch_queue.json，
        目标 agent 在启动自检时读取并执行。无原生调用其他 agent API 的平台均走此路径。
        """
        import uuid
        from datetime import datetime

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
        }
        # 读取已有队列（不存在则新建）
        queue = []
        if os.path.exists(self.DISPATCH_QUEUE):
            try:
                with open(self.DISPATCH_QUEUE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                queue = data.get("queue", []) if isinstance(data, dict) else data
            except (json.JSONDecodeError, ValueError):
                queue = []
        queue.append(ticket)
        os.makedirs(os.path.dirname(self.DISPATCH_QUEUE), exist_ok=True)
        with open(self.DISPATCH_QUEUE, "w", encoding="utf-8") as f:
            json.dump({"queue": queue}, f, ensure_ascii=False, indent=2)
        return {"success": True, "ticket": ticket, "queue_path": self.DISPATCH_QUEUE}

    def get_agent_id(self):
        identity_file = os.path.join(self.home, "IDENTITY.md")
        if os.path.exists(identity_file):
            with open(identity_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if "Name:" in line:
                        return line.split("Name:")[1].strip()
        return "workbuddy"

    def get_workspace(self):
        return self.workspace
