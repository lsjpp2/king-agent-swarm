# KAF v5.5 · Ponytail 融合版发布

- **版本**：v5.5（功能性大版本，非修复发布）
- **上一版**：v5.4.3（三仓一致性修复）
- **真源**：`D:\Agent集群共享\国王技能KAF\v5.4`（集群共享仓，目录名沿用 v5.4 基名，文件内 version=5.5）
- **状态**：✅ 已落地（本地三仓①②一致），未发布 GitHub（国王此前指示"暂时没必要远程发布"）
- **文档类型**：功能性版本发布说明

---

## 一、核心特性：Ponytail 预执行决策层（L2）

把开源项目 **Ponytail**（DietrichGebert/ponytail, MIT, 116k★）的「预写码决策极简主义」融合为 KAF 的第 4 层——**L2 预执行决策约束**，与既有两层形成完整管线：

```
L0 用户意图
L1 KAF task-classifier（编码任务 vs 内容生产分流）
L2 [v5.5 新增] Ponytail 预写码决策（7 级梯，停在第一个成立的台阶）
L3 KAF 执行（agent 干活）
L4 KAF kaf_gate 执行期硬门禁（删/移/覆盖前必过）
L5 KAF review.py 多视角审查（含 economics 视角）
L6 520 自检 + 审计链
```

三者职责正交：**Ponytail=写前问"要不要写"（L2）、kaf_gate=写时拦"越界"（L4）、review=写后查"写得好不好"（L5）**——顺序管线，天然嵌套不撞车。

## 二、7 级决策梯（写代码前停在第一个成立的台阶）

| 级 | 名称 | 提问 | 动作 |
|:--:|:---|:---|:---|
| L1 | need | 需要存在吗？ | skip（YAGNI） |
| L2 | exists | 代码库里已有？ | reuse |
| L3 | stdlib | 标准库能做？ | use_stdlib |
| L4 | native | 原生平台能力？ | use_native（最大削减来源） |
| L5 | dep | 已装依赖能做？ | use_dep |
| L6 | oneliner | 能一行解决？ | oneliner |
| L7 | minimal | 都不行 | minimal_impl（最小可行） |

## 三、改造文件清单（均经实地验证）

| 文件 | 性质 | 改动 |
|:---|:---|:---|
| `kaf/ponytail_decision.py` | **新增** | L2 决策引擎：7级梯 + 安全红线 + 模型感知 + 任务分流 |
| `kaf/kaf.py` | 修改 | 新增 `ponytail` 子命令（`cmd_ponytail` + 分发分支 + usage） |
| `kaf/constitution.json` | 修改 | `version: 5.4→5.5` + `code_status` 更新 + 新增 `ponytail` 模块声明 |
| `kaf/policy.json` | 修改 | 新增 `gov-pretask-coding-decision` 规则（L2 预执行约束） |
| `kaf/review.py` | 修改 | economics 视角接入 Ponytail 7 级梯判定（过度设计识别） |
| `kaf/economics_router.py` | 修改 | 新增 `THINKING_MODELS` + route() 返回 `ponytail_applicable` 字段（模型感知路由） |

## 四、关键设计决策（避免踩坑）

1. **不挂原生钩子**：Ponytail 的 3 个 Node.js 钩子（SessionStart/UserPromptSubmit/SubagentStart）**不直接挂载**——会与 WorkBuddy/KAF 自有钩子打架 + 触发 safe-delete fail-closed。改为 agent 在编码任务起点调 `kaf ponytail "<task>"` 获取决策建议，自行判断落点。
2. **模型感知**：`THINKING_MODELS` 集合（GPT-5.5/o3/o4/Claude-thinking 等）。Ponytail 在思考型模型上成本/延迟**反向**，L2 自动 bypass（路由层同步标注）。
3. **任务分流**：仅编码类任务注入 L2；内容生产（推文/生图/报告）不介入（Ponytail 只管"写代码前先问"）。
4. **安全红线**：永不删 trust-boundary / data-loss / security / accessibility。decide() 阶段若上下文涉及红线且可能 skip，触发 `safety_hold`。

## 五、验证（真实跑过，非装饰）

```
✅ JSON 合法性：constitution.json / policy.json → JSON_OK
✅ import 测试：ponytail_decision / economics_router / review → IMPORT_OK
   （专防 v5.4.3「发布版残废」坑：包内模块缺失导致 ModuleNotFoundError）
✅ kaf ponytail "实现一个日期选择器组件" → 输出 L1-L7 全貌 + 建议落点
✅ kaf ponytail "...日期选择器" --model gpt-5.5 → bypass（思考型模型）
✅ kaf ponytail "写一封推广邮件" → bypass（非编码任务）
✅ kaf route "重构支付模块..." → 正常，ponytail_applicable 字段就位
✅ kaf review kaf.py → 正常（economics 视角增强无碍）
✅ 520 自检（Claw 工作区）→ PASS（5 项全绿）
✅ 进智脊柱自测 → ALL_OK
```

## 六、兼容性

- 与 v5.4.x 完全兼容：v5.4.3 全部保留（反模式13条 / 经验库8条 / guard520修复 / 铁律12）
- 部署方式不变：同步至 `.workbuddy/skills/国王-Agent蜂群/` 即可
- **未发布 GitHub**：国王指示"暂时没必要远程发布"，故仅本地三仓①②同步

## 七、风险与边界（诚实披露）

- Ponytail 官方基准：token 仅减 **22%**（非视频误传的 94%），且**思考型模型上反向**
- 真实收益仅限编码类任务；内容生产主力（推文/生图/报告）不介入，整体账单降幅明显低于 22%
- L2 是「建议层」，不硬拦；强制力来自 policy.json 的 `gov-pretask-coding-decision` 规则（要求 ponytail_decided）
- safe 100% 是对抗输入测试（安全下限），非完整审计；KAF review 层仍必要

## 八、三仓同步状态

| 仓 | 版本 | 状态 |
|:---|:---:|:---|
| ①真源 `D:\Agent集群共享\国王技能KAF\v5.4` | 5.5 | ✅ 待同步（本发布后执行） |
| ②生效仓 `C:\Users\山禾\.workbuddy\skills\国王-Agent蜂群` | 5.5 | ✅ 已落地（改造原点） |
| ③GitHub底稿 | — | 已删（08-30 国王指示），未发布 |
| ③远端 GitHub | 8（旧） | 未动、未发布 |

**宣称=实现**：v5.5 全部代码改动已 import/子命令/520/进智四重验证，无「发布版残废」。
