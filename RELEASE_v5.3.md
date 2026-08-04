# KAF 国王-Agent 框架 v5.3 发布说明

> 发布时间：2026-08-04
> 真源：https://github.com/lsjpp2/king-agent-swarm
> 上一版标签：v5.0（v5.1/v5.2 为演进过程中的提交，未单独打标签）

## 一句话

v5.3 在 v5.2（闭环可运行）之上，补了两件根本性的事：
1. **治理层 Governance** —— "宪法"从声明式文本变成代码可强制执行的关卡；
2. **动态国王 Deployer = King** —— 国王不再硬编码为山禾，部署者即国王。

## 两大核心补充

### A. 治理层（Governance）
- 新增 `kaf/governance.py`：所有写操作统一经 `Governance.evaluate()`，顺序为
  `kill-switch（熔断）→ agent HMAC attestation（身份背书）→ 520 护栏 → policy（策略）`。
- **防篡改审计链**：每次评估写入 hash 链（`governance/audit_chain.log`），任一节点被改都能检出。
- 前几版只有 `kaf check` 自检、无持续防篡改记录；v5.3 让"每次操作都有链上证据"，直接兑现"宣称≠实现"。

### B. 动态国王（Deployer = King）
- 新增 `kaf/king.py:resolve_king()`，优先级：
  `KAF_KING 环境变量 > kaf_config.json > 本地作者环境(山禾) > 当前 OS 用户`。
- 本地（山禾机器）→ 山禾是国王；远程复制者未配置 → 默认当前 OS 用户 = 国王；
  显式覆盖：`KAF_KING=Alice` 或 `kaf_config.json {"king":"Bob"}`。
- 解决"技能被新手复制后被强加山禾为王"的狭隘性。

## 能力对照（v5.0 → v5.3）

| 能力 | v5.0 | v5.1 | v5.2 | v5.3 |
|:---|:---:|:---:|:---:|:---:|
| 宪法 / 520 护栏 | ✓ | ✓ | ✓ | ✓ |
| 模型经济学路由 | – | ✓ | ✓ | ✓ |
| 多视角审查闭环 | – | ✓ | ✓ | ✓ |
| 共享账本持久化 | – | ✓ | ✓ | ✓ |
| 治理层 + kill-switch | – | – | – | **✓** |
| 防篡改审计链 | – | – | – | **✓** |
| agent HMAC 背书 | – | – | – | **✓** |
| 动态国王 | 硬编码 | 硬编码 | 硬编码 | **✓** |
| 图解 01-08 + 离线页 | 部分 | 部分 | 01-03 | **✓** |

## 远程复制者指引

```bash
git clone https://github.com/lsjpp2/king-agent-swarm.git
cd king-agent-swarm
# 默认你就是国王（当前 OS 用户），无需改代码
# 显式指定国王：
export KAF_KING=你的名字        # 或 kaf_config.json 写 {"king":"你的名字"}
python kaf/kaf.py check
```

## 校验

- 远程 master tip = `f09f47720a0a30c532bf869ccd2aeb38ca982dff`（与本地一致）
- v5.3 tag 指向该提交；本 Release 附完整优势说明
- 共享归档：`D:/Agent集群共享/国王技能KAF/v5.3/`（git archive 真快照）、`KAF版本优势说明.md`
