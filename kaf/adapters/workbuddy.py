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
        self.workspace = workspace or os.environ.get("WORKBUDDY_WORKSPACE", "D:/WorkBuddy/Claw")
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

    def register_hook(self, event, callback):
        """WorkBuddy hook注册（通过PreToolUse等机制）"""
        # WorkBuddy作为类VS Code应用，hook通过配置文件注册
        # 实际enforcement依赖平台hook能力
        hooks_config = os.path.join(self.home, "hooks.json")
        hooks = {}
        if os.path.exists(hooks_config):
            with open(hooks_config, "r", encoding="utf-8") as f:
                hooks = json.load(f)
        hooks.setdefault(event, []).append(callback.__name__ if callable(callback) else callback)
        with open(hooks_config, "w", encoding="utf-8") as f:
            json.dump(hooks, f, indent=2, ensure_ascii=False)
        return {"success": True, "event": event}

    def execute(self, action):
        """执行操作（通过WorkBuddy的Bash/Write等工具）"""
        # 实际执行由WorkBuddy的agent loop处理
        # 这里返回操作描述，由调用方转发给agent
        return {"action": action, "platform": "workbuddy", "status": "forwarded"}

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
