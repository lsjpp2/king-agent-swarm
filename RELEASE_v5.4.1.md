# KAF v5.4.1 发布说明

> 发布日期：2026-08-07
> 上一版：v5.4（架构与规范定稿，纯规范/文档/图解）
> 真源：https://github.com/lsjpp2/king-agent-swarm （tag `v5.4.1`）
> 状态：**代码完整版**（v5.4 spec + v5.3.1 地基三件套已落地并接强制门禁）
> 文档类型：Release Note

---

## 0. 一句话

v5.4 把进智脊柱（Cognition Spine）**设计**出来了；v5.4.1 把它**接进运行时代码**了。
本次发布 = v5.4 完整规范 + 5.3.1 地基三件套（①②⑤）真实落地，受 520 强制门禁 `kaf_gate.py` 约束。

---

## 1. 本版到底加了什么（代码，非文档）

| 零件 | 文件 | 状态 | 接入口 |
|:---|:---|:---|:---|
| ★① 反模式库 | `kaf/cognition/anti_patterns.jsonl` | ✅ 已实现 | 8 条来自 Claw 会话清理事件 `8f6d42dc` 的真实种子 |
| ★② 检索注入 | `kaf/cognition/retrieval_inject.py` | ✅ 已实现 | `kaf_gate.py retrieve` 子命令 + `__init__` 导出 |
| ★⑤ 元认知门控 | `kaf/cognition/deliberate.py` | ✅ 已实现 | `kaf_gate.py check`（高利害动作前触发软刹车） |
| 自测 | `kaf/cognition/cognition_selftest.py` | ✅ 已实现 | 6/6 PASS（520 式真跑通） |
| ③④ 经验蒸馏 / 校准引擎 | — | ⏳ 待 v5.4 代码范畴 | 预留接口，未实现（守"宣称=实现"） |
| Loop Driver 闭环自修 | — | ⏳ 待 v5.4 代码范畴 | 规范已定，代码未写 |

---

## 2. 进智如何受治理层约束（关键，未变）

- `deliberate()` 只做**软刹车**（HOLD/WARN 提示），不返回非零、**不硬拦**；
  真正的硬拦仍由 520 护栏（`kaf_gate.py` / `guard520.py`）负责。
- `deliberate()` 的"放行"**不高于国王否决权**，不绕过 `kaf_gate.py`。
- 触发 kill-switch / 520 护栏立即中止，进智不介入。

---

## 3. 实测证据（本仓可复跑）

```bash
cd kaf
python cognition/cognition_selftest.py
# [PASS] anti_patterns >= 3
# [PASS] retrieve 命中归档类反模式
# [PASS] deliberate HOLD on 批量归档备份
# [PASS] HOLD 携带正确替代
# [PASS] deliberate GO on 普通动作
# [PASS] 注入块非空
# RESULT: ALL_OK

python kaf_gate.py retrieve --task "把所有标题含备份的会话全部归档"
# ⚠️ 历史反模式（进智脊柱检索注入，软提示非硬拦截）：
#   • [HIGH] 一刀切归档: 逐条核查 + conversation_search 实锤…
#   • [MED]  标题改写踩坑: 按 plan 文本精确匹配…
#   • [HIGH] 误标活会话: 归档时排除活会话…

python kaf_gate.py check --op delete --target "D:/x/备份记忆" --task "标题含备份的全部归档"
# DELIBERATE_HOLD: 命中历史反模式 [一刀切归档]
#   => 等同 520 软刹车：请先列清单并向用户确认后，再 --confirmed 执行。
```

---

## 4. 能力对照（v5.0 → v5.4.1）

| 能力 | v5.0 | v5.2 | v5.3 | v5.4 | **v5.4.1** |
|:---|:---:|:---:|:---:|:---:|:---:|
| 宪法即代码 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 520 运行时护栏 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 记忆完整性 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 平台适配器 | — | ✅ | ✅ | ✅ | ✅ |
| 宰相轮值 | — | ✅ | ✅ | ✅ | ✅ |
| 模型经济学路由 | — | 📋 | 📋 | ✅ | ✅ |
| 治理层(策略/急停/审计/HMAC) | — | — | ✅ | ✅ | ✅ |
| 动态国王 | — | — | ✅ | ✅ | ✅ |
| ① 反模式库 | — | — | — | 📋 | **✅** |
| ② 检索注入 | — | — | — | 📋 | **✅** |
| ⑤ deliberate 门控 | — | — | — | 📋 | **✅** |
| ③ 经验蒸馏 | — | — | — | 📋 | ⏳ |
| ④ 校准引擎 | — | — | — | 📋 | ⏳ |
| Loop Driver 闭环 | — | — | — | 📋 | ⏳ |

图例：✅ 已实现 · 📋 规范已定待落地 · ⏳ 代码待写

---

## 5. 兼容性 / 破坏性

- **零破坏性**：仅新增 `kaf/cognition/` 包 + `kaf_gate.py` 加 `retrieve` 子命令与 `--task` 参数；
  原有 `check` 行为不变（520 硬拦依旧），`deliberate` 仅追加软提示。
- 若 `cognition` 包缺失，`kaf_gate.py` 自动降级（`_COG_OK=False`），不报致命错。
- Python 3.8+ 标准库即可，零外部依赖。

---

## 6. 下一步

- v5.4 代码范畴：③④ 经验蒸馏 + 校准引擎 + Loop Driver 闭环自修（需 ①②⑤ 先跑出经验沉淀）。
- 在真实长任务上观测检索注入命中率与 deliberate 误报率，再定 ③④ 字段。

> 守"宣称=实现"：本文仅声明本版**真实落地**的部分；③④+Loop 明确标"待写"，不提前宣称。
