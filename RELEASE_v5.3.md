# KAF 国王-Agent 框架 v5.3 发布说明

> 发布时间：2026-08-04
> 真源：https://github.com/lsjpp2/king-agent-swarm
> 上一版标签：v5.0（v5.1/v5.2 为演进过程中的提交，未单独打标签）

## 一句话

v5.3 在 v5.2（闭环可运行）之上，补了两件根本性的事：
1. **治理层 Governance** —— "宪法"从声明式文本变成代码可强制执行的关卡；
2. **动态国王 Deployer = King** —— 国王不再硬编码为${KING_NAME}，部署者即国王。

## 两大核心补充

### A. 治理层（Governance）
- 新增 `kaf/governance.py`：所有写操作统一经 `Governance.evaluate()`，顺序为
  `kill-switch（熔断）→ agent HMAC attestation（身份背书）→ 520 护栏 → policy（策略）`。
- **防篡改审计链**：每次评估写入 hash 链（`governance/audit_chain.log`），任一节点被改都能检出。
- 前几版只有 `kaf check` 自检、无持续防篡改记录；v5.3 让"每次操作都有链上证据"，直接兑现"宣称≠实现"。

### B. 动态国王（Deployer = King）
- 新增 `kaf/king.py:resolve_king()`，优先级：
  `KAF_KING 环境变量 > kaf_config.json > 本地作者环境(${KING_NAME}) > 当前 OS 用户`。
- 本地（${KING_NAME}机器）→ ${KING_NAME}是国王；远程复制者未配置 → 默认当前 OS 用户 = 国王；
  显式覆盖：`KAF_KING=Alice` 或 `kaf_config.json {"king":"Bob"}`。
- 解决"技能被新手复制后被强加${KING_NAME}为王"的狭隘性。

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

- 远程 master tip = `8f251c1`（含本 Release 说明 + 文档去狭隘化提交）
- v5.3 tag 指向 `f09f477`；文档去狭隘化在后续提交 `8f251c1`，均已推送并 SHA 回验一致
- 共享归档：`${KAF_SHARED_DIR}/国王技能KAF/v5.3/`（git archive 真快照）、`KAF版本优势说明.md`

---

## 2026-08-04 补：文档去狭隘化（v5.3 发版后修正）

发版后复核发现 **README / SKILL / architecture.md 的旧文案过于${KING_NAME}中心化、且带创伤叙事（rm -rf / C盘散文件事故），不利于大众接受与推广**，已在本提交修正：

- **去掉创伤叙事**：README 不再以"AI 删你文件"的事故堆砌为门面，改为"多 agent 协作的通用治理层"价值主张。
- **去${KING_NAME}中心化**：框架不再绑定"${KING_NAME}的 6-agent 集群"；明确**平台无关、谁部署谁为王**。
- **对齐 v5.3 代码**：说明 / 架构图 / SKILL 统一为"治理层 + 动态国王(Deployer=King)"，消除"代码进 v5.3、文档停 v5.0"的割裂。
- 保留 `coordinator.json` / `kaf_config.example.json` 中的${KING_NAME}路径作为**本机示例数据**（注释已声明绝不硬编码、远程回退 OS 用户），非狭隘叙事。

