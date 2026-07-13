"""KAF Platform Adapter Template — 新平台适配器模板

接入新平台：
1. 复制此文件，改名为 <platform>.py
2. 继承 PlatformAdapter
3. 实现7个方法
4. 在 kaf.py 中注册适配器
"""
import os
from .base import PlatformAdapter


class TemplateAdapter(PlatformAdapter):
    platform_name = "template"  # ← 改成你的平台名

    def __init__(self, workspace=None):
        self.workspace = workspace or os.getcwd()
        # ← 初始化你的平台路径

    def read_constitution(self):
        """读取KAF宪法配置"""
        # ← 实现你的平台读取逻辑
        pass

    def read_memory(self, key=None):
        """读取记忆文件"""
        # ← 实现你的平台记忆读取
        pass

    def write_memory(self, key, value, protect_check=True):
        """写入记忆（含520保护检查）"""
        # ← 实现你的平台记忆写入
        # 注意：protect_check=True时必须经过MemoryIntegrity检查
        pass

    def register_hook(self, event, callback):
        """注册hook"""
        # ← 实现你的平台hook注册
        # 常见event: pre:delete, pre:write, startup, post:execute
        pass

    def execute(self, action):
        """执行操作"""
        # ← 实现你的平台操作执行
        pass

    def get_agent_id(self):
        """获取当前Agent身份"""
        # ← 返回当前Agent的标识
        pass

    def get_workspace(self):
        """获取当前工作区"""
        return self.workspace
