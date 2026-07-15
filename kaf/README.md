# KAF · King-Agent Framework

> **多智能体治理框架** — Constitution-as-Code + 520 Runtime Guard  
> 让AI Agent集群有法可依、有规可守、有据可查

[English](./README_EN.md) | 中文

---

## 为什么需要KAF？

你用了CrewAI/Ruflo/MetaGPT编排多Agent执行任务，但发现：

- Agent**删了不该删的文件**（你的数据没了）
- Agent**到处建临时文件**（C盘塞满）
- Agent**覆盖了关键配置**（规则/记忆丢失）
- 多个Agent**互相读对方记忆**（隔离墙形同虚设）
- 出了事**无法追溯**（没脚本没日志）

**CrewAI管"怎么执行任务"，KAF管"怎么治理Agent"**——两者互补。

## 核心理念

```
Constitution-as-Code   宪法从md文档 → 可解析JSON，规则可机器验证
520 Runtime Guard      从事后检查 → 运行时强制（有原生hook走hook，无hook平台走agent侧门禁kaf_gate.py）
Memory Integrity       从"丢失后恢复" → "写入前阻止覆盖"
Platform Adapter       从绑定特定平台 → 5行代码接入任意平台
```

## 快速开始

```bash
# 初始化KAF
python kaf.py init

# 520自检（可追溯/可恢复/可修复/可进化）
python kaf.py check

# 记忆完整性校验（指纹+drift检测）
python kaf.py verify

# 查看集群状态
python kaf.py status

# 宰相轮值
python kaf.py rotate claude
```

## 五层架构

```
┌─────────────────────────────────────────┐
│  Platform Adapters  平台适配器            │
│  WorkBuddy / Claude / OpenCode / ...    │
├─────────────────────────────────────────┤
│  Coordinator Protocol  宰相轮值协议       │
├─────────────────────────────────────────┤
│  520 Runtime Guard  运行时护栏            │
├─────────────────────────────────────────┤
│  Constitution-as-Code  声明式宪法         │
├─────────────────────────────────────────┤
│  Memory Integrity  记忆完整性             │
└─────────────────────────────────────────┘
```

## 520法则（核心）

| 原则 | 含义 | 工程化 |
|------|------|--------|
| 可追溯 | 每个操作有脚本+日志 | `kaf_operations.log`自动记录 |
| 可恢复 | 删除走回收站，配置改前备份 | `FOF_ALLOWUNDO` + `.bak` |
| 可修复 | 错误可回滚 | `on_failure`提供回滚方案 |
| 可进化 | 提炼工作流/铁律/skill | skill自动封装 |

**铁律8/9/10**：
- 铁律8：操作必须写脚本+验证（rm/mv/copy → 先写.py → 执行 → ls验证）
- 铁律9：记忆数字必须实地核查（任何数量 → find/ls验证）
- 铁律10：删除前展示清单（ls -R → 展示用户 → 确认才删）

## 文件结构

```
kaf/
├── constitution.json      声明式宪法（可机器解析）
├── guard520.py            520运行时护栏（4个检查点）
├── memory_integrity.py    记忆完整性（SHA-256指纹+drift检测）
├── coordinator.json       宰相注册表（轮值/投票/handover）
├── kaf.py                 CLI入口（init/check/verify/guard/rotate/status）
├── adapters/
│   ├── base.py            适配器接口（7个方法）
│   ├── workbuddy.py       WorkBuddy适配器（已实现）
│   └── _template.py       新平台适配器模板
└── examples/
    └── basic/             基础示例
```

## 接入新平台

```python
# 1. 继承PlatformAdapter
from adapters.base import PlatformAdapter

class MyAdapter(PlatformAdapter):
    platform_name = "my_platform"

    def read_constitution(self): ...
    def read_memory(self, key=None): ...
    def write_memory(self, key, value, protect_check=True): ...
    def register_hook(self, event, callback): ...
    def execute(self, action): ...
    def get_agent_id(self): ...
    def get_workspace(self): ...
```

## 治理层 vs 编排层

```
你的技术栈：
  CrewAI / Ruflo / LangGraph    ← 任务编排层（怎么执行任务）
          +
  KAF                           ← 治理层（怎么管Agent）
          +
  SKILL.md standard             ← 技能标准
```

**KAF不替代任何框架，而是给所有框架加一层治理。**

## 实战背景

KAF源自真实的多Agent集群（WorkBuddy+OpenCode+Claude+Kimi+Cursor），经过3个月实战、踩过v4地图删除事故（历史地图2000+张不可逆丢失）后提炼。

不是玩具demo，是拿真实数据换来的治理经验。

## License

MIT

## 相关

- [king-agent-swarm](https://github.com/lsjpp2/king-agent-swarm) — 国王模型Agent集群架构（KAF的前身）
- [CrewAI](https://github.com/crewAIInc/crewAI) — 多Agent任务编排（与KAF互补）
- [planning-with-files](https://github.com/OthmanAdi/planning-with-files) — SKILL.md标准
