# KAF v5.6 发布说明 — 预执行经济学（复杂度分级 + token 层边界）

> 发布日期：2026-08-31
> 上一版：v5.5（L2 预执行决策层 · Ponytail 融合）
> 触发来源：国王质询「融合迭代之前，你在 GitHub 上检索了同类型高热度开源项目了吗？」
> 答案是**没有**——v5.5 直接动手了。补检索后回流两项增强，即本版。
> 调研报告：`RESEARCH_github_peers_v556.md`（真源①根目录）

---

## 一句话总结

v5.5 解决了"**该不该写**"，v5.6 解决了"**该派给谁写**"和"**省的钱到底在哪一层**"。

---

## 变更清单

### T2 · 复杂度分级路由（80/15/5）

**问题**：v5.5 及之前只按 `role`（planner/worker/reviewer）选成本档，导致"简单活派给贵模型"——一个改圆角的需求因命中「设计」关键词被判为 planner，直接上 frontier 档。

**方案**（借鉴 `zscole/model-hierarchy-skill`，345★）：

| 级别 | 目标占比 | 默认档 | 判据 |
|---|---|---|---|
| routine | 80% | economy | 机械/单点/有明确先例 |
| moderate | 15% | balanced | 多步骤但路径清楚 |
| complex | 5% | frontier | 跨模块/高风险/需权衡设计 |

- 评分：complex 信号词 ×2、moderate 信号词 ×1，长描述（>120 / >260 字）加权
- 校正：routine 取 role 档与复杂度档中**更便宜**者；complex 取**更强**者；moderate 不动
- **跨 role 放宽**：目标档在本 role 内无候选时放宽 role 过滤

> ⚠️ **本版实测发现并修复的架空 bug**：初版把复杂度校正后的目标档交给原 role 过滤器筛选，
> 结果 worker 任务判为 complex 也拿不到 frontier 候选（frontier 档只有 planner 角色的 claude），
> 80/15/5 里的 5% 形同虚设。修复即 `role_filter_relaxed` 机制。

**新增输出字段**：`complexity` / `complexity_desc` / `complexity_target_share` /
`role_preferred_tier` / `final_preferred_tier` / `tier_adjusted` / `role_filter_relaxed`

### T1 · 四层 token 治理（诚实边界澄清）

**问题**：v5.5 把 Ponytail 当作"省 token 的方案"，实际上它只管**代码生成**一层。若真实开销落在读码或命令输出层，精简代码救不了成本。

**方案**（借鉴 `vagkaratzas/token-saviour`，10★，方法论价值远超 star）：

| 层 | 实测可省 | 归属工具 | KAF 状态 |
|---|---|---|---|
| L1 code_read | −66% | serena (MCP·LSP 符号级检索) | ❌ 未集成（外部 MCP，集成成本高） |
| L2 command_output | −65% | rtk (输出裁剪) | ❌ 未集成（外部 MCP） |
| L3 prose_output | −6% | caveman (精简语体) | ❌ 未集成（收益极低，优先级最末） |
| L4 code_gen | −40% | **Ponytail L2 决策梯** | ✅ 已集成（v5.5） |

- 四层堆叠上限 **−69.6%**；**KAF 当前只吃到 code_gen 一层（−40%）**
- ⚠️ **诚实口径入宪**：`constitution.json → token_governance.honest_note` 明确写死
  "宣称省 69.6% 属虚假，须外接 serena/rtk 才成立"，与 `kaf honest` 诚实扫描同口径

---

## 文件改动

| 文件 | 改动 |
|---|---|
| `kaf/economics_router.py` | +T2 三级复杂度评估 `assess_complexity()`；+T1 `classify_token_layer()` / `token_plan()`；`route()` 增 11 个字段；CLI 增 `tokens` 子命令 |
| `kaf/kaf.py` | 新增 `cmd_tokens()`；`cmd_route()` 打印复杂度与 token 层；usage 增 `kaf tokens` |
| `kaf/constitution.json` | version 5.5→**5.6**；`economics_routing.complexity_routing`(T2)；新节 `token_governance`(T1)；`ponytail.token_layer_scope` 边界澄清；`amendment.history[v5.6]` |
| `kaf/policy.json` | 新增规则 `gov-routine-no-frontier`（routine 派 frontier 须 `cost_justified`） |
| `kaf/review.py` | economics 视角从「仅 Ponytail 判定」升级为「过度设计 + 模型档位 + token 层」三查 |
| `SKILL.md` | **补齐 v5.4→v5.6**（v5.5 那轮漏更新 SKILL.md）：description/标题/核心理念/L0–L6 管线 + 新增 v5.5/v5.6 完整章节 |
| `RELEASE_v5.6.md` | 本文件 |

升级脚本：`D:\WorkBuddy\Claw\scripts\upgrade_kaf_v56.py`（幂等，含回读断言）

---

## 新增 CLI

```bash
kaf tokens "定位并修复登录接口的空指针"   # 四层 token 治理方案 + 本任务命中层
kaf route  "<task>"                      # 输出新增复杂度与 token 层信息
python economics_router.py tokens "<task>"
```

---

## 验证结果

| 项 | 结果 |
|---|---|
| JSON 合法性（constitution/policy） | ✅ PASS |
| 模块 import（economics_router/kaf/review/ponytail_decision） | ✅ PASS |
| T2 四例回归（planner+routine 降档 / worker+complex 升档 / 两例不变） | ✅ PASS |
| T1 token_plan 四层输出 + 命中标注 | ✅ PASS |
| `kaf tokens` / `kaf route` / `kaf ponytail` CLI | ✅ PASS |
| policy allow 兜底仍在末位 | ✅ PASS |
| 520 自检 `kaf check` | ✅ PASS |
| 进智自测 `cognition_selftest` | ✅ PASS |
| 三仓①② sha256 一致 | ✅ 一致 |

---

## 回滚点

| 仓 | 备份路径 |
|---|---|
| ① 真源 | `D:\Agent集群共享\国王技能KAF\v5.5.bak.20260831_0306` |
| ② 生效仓 | `D:\Agent集群共享\backups\kaf_v55_pre_v56\国王-Agent蜂群.bak.20260831_0306` |

---

## 待办（不在本版范围）

1. **serena / rtk 实际集成**（T1 的 L1/L2 层，−66%/−65%，收益最大但需接外部 MCP）
2. **A/B 实测**：T2 复杂度分级的真实成本削减（当前仅结构性保证，无实测数据）
3. **GitHub 发布**：③ 本地底稿已于 2026-08-30 删除，远端仍为旧版；需要时重建净化版
4. **复杂度信号词调优**：当前为关键词+长度启发式，可接 cognition 的经验蒸馏做数据驱动校准

---

## 教训沉淀

1. **迭代前必查 GitHub 同类高热度项目** —— 这条铁律 v5.5 违反了，v5.6 补做才发现 T1/T2 两个真缺口。
2. **搜索页热度会骗人** —— `rkwap/aegis-framework`、`qlycool/agent-os` 自称"世界首个 GenAI OS / 内核级治理"，实测 **0★**。必须用 shields.io 或 API 实地核查再决定借鉴。
3. **star 少 ≠ 没价值** —— token-saviour 仅 10★，但其四层方法论直接纠正了 KAF 对 Ponytail 能力边界的误判。
4. **改完必须实测行为，不能只测 import** —— T2 的 role 过滤架空 bug 是 import 全绿之后跑四例回归才暴露的。
