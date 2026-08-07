# KAF v5.4.2 · 发布说明

## 版本
- 版本号：**v5.4.2**
- 上一版：v5.4.1（2026-08-07，进智地基 ①②⑤ 落地）
- 发布日期：2026-08-07
- 真源：`D:/WorkBuddy/Claw/projects/kaf`
- 状态：稳定（闭环三件套落地，进智五零件全部 `implemented`）

## 本次变更（一句话）
把 v5.4 规范里"待实现"的闭环三件套（③经验蒸馏 + ④决策校准 + **Loop Driver 闭环自修**）真正写成运行时代码并接进 `kaf_gate.py`。KAF 进智脊柱五零件至此**全部 implemented**，交付质量闭环从"规范 + 图解"变为**可运行、可自动收敛**。

## 能力对照
| 零件 | v5.4.1 | v5.4.2 |
|---|---|---|
| ① 反模式库 | ✅ | ✅ |
| ② 检索注入 | ✅ | ✅ |
| ③ 经验蒸馏 | ❌ 仅规范 | ✅ `kaf/cognition/experience_distillation.py` |
| ④ 决策校准 | ❌ 仅规范 | ✅ `kaf/cognition/calibration_engine.py` |
| ⑤ deliberate 门控 | ✅ | ✅ |
| **Loop Driver 闭环** | ❌ 仅规范+图解 | ✅ `kaf/cognition/loop_driver.py` + `kaf_gate.py loop` 子命令 |

## 新增模块
- **`kaf/cognition/experience_distillation.py`**：`add_experience()` 压经验 `{context, action, outcome, confidence}`；置信度随复核累积（同类 +0.1 封顶 1.0）；`get_high_conf()` 供检索注入复用，低置信不注入防噪声。
- **`kaf/cognition/calibration_engine.py`**：`calibrate()` 比对历史相似决策，标注误校准（高置信失败但本次预测成功 → 警告）。
- **`kaf/cognition/loop_driver.py`**：`run_loop()` 交付质量闭环——候选物 vs 指令逐条比对 → 差异清单 → 调修订器 → 再比对 → 收敛；阈值三档（hard/soft/king）；熔断 `max_rounds=5`；每轮留可逆副本。
- **`kaf/kaf_gate.py`**：新增 `loop` 子命令（`--instruction / --candidate / --mode / --auto-fix / --max-rounds`）；导入 `loop_driver`。

## 闭环行为（实跑验证）
- **hard**（可量化指令"归档 113 条纯系统备份；均经 conversation_search 零命中"）：2 轮收敛，`score=1.0`，自动无需人工确认。
- **soft**（"归档所有纯系统备份；保留活会话；不得误归档真实工作对话"）：收敛，候选物被补全对齐。
- **king**（模糊"把会话整理得好看点"）：`needs_king=True`，不擅自定稿，升国王确认。

## 校验
- `cognition_selftest.py`：**14/14 PASS**（含 ③④ + Loop 三模式）。
- `constitution.json`：③ ④ loop `implemented=true`；`code_status=v5.4.2 全落地`。
- `kaf_gate.py loop` 三模式 CLI 实测通过。

## 兼容性 / 约束
- 仅新增文件 + 接线，**不动**既有 ①②⑤ 逻辑。
- Loop Driver 触发 520 护栏 / kill-switch 立即中止，不高于国王否决权，不绕过 `kaf_gate.py`。
- 修订器默认 `simple_revise`（演示用最简追加）；真实 agent 用 LLM 修订替换 `revise_fn`。

## 同步
- GitHub `tag v5.4.2` + Release 页面
- 集群共享仓 `D:/Agent集群共享/国王技能KAF/v5.4/`
- 本地生效仓 `C:/Users/山禾/.workbuddy/skills/国王-Agent蜂群/`
