"""KAF Platform Adapter Base — 适配器接口定义

接入新平台只需继承此类，实现4个方法。
"""


class PlatformAdapter:
    """平台适配器接口。4个方法接入任意平台。"""

    platform_name = "base"

    def read_constitution(self):
        """读取宪法配置"""
        raise NotImplementedError

    def read_memory(self, key=None):
        """读取记忆"""
        raise NotImplementedError

    def write_memory(self, key, value, protect_check=True):
        """写入记忆（含520保护检查）"""
        raise NotImplementedError

    def register_hook(self, event, callback):
        """注册hook（pre:delete / pre:write / startup等）"""
        raise NotImplementedError

    def execute(self, action):
        """执行操作"""
        raise NotImplementedError

    def get_agent_id(self):
        """获取当前Agent身份"""
        raise NotImplementedError

    def get_workspace(self):
        """获取当前工作区路径"""
        raise NotImplementedError

    def dispatch(self, task, target_agent, role=None, cost_tier=None, est_cost=None):
        """路由落执行：把任务派发给目标 agent。

        v5.2 进化（方向2·路由落执行）：route 只推荐，dispatch 才真正交付。
        本方法默认写入共享派发队列（${KAF_SHARED_DIR}/dispatch_queue.json），
        目标 agent 在启动自检时读取并执行。无原生调用其他 agent API 的平台均走此路径。
        """
        raise NotImplementedError
