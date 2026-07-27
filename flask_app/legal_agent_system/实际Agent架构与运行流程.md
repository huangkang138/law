# 法律 Agent 实际架构与运行流程

本文只说明当前项目已经实现的法律 Agent，不介绍通用 Agent 理论。内容以当前源码为准。

## 一、30 秒整体理解

```text
用户在案件工作台发起法律任务
  → 系统识别任务所属领域和计划模板
  → 检查法域及关键事实是否完整
  → 根据固定模板生成本次执行计划
  → 每次选择一个步骤并调用受控工具
  → 记录工具结果并校验事实、法源和结构
  → 决定继续、重试、暂停补充信息或结束
  → 返回任务状态和结构化结果
```

重要现状：普通 `/digital-human/chat` 只是数字人问答和意图识别，不会自动启动法律 Agent。可执行 Agent 必须通过案件工作台接口启动。

## 二、核心模块职责

LangGraph 是把任务拆成多个节点、按照状态决定下一步的状态机框架。

| 模块 | 负责什么 | 不负责什么 | 输入 → 输出 | 前后关系 |
| --- | --- | --- | --- | --- |
| Runtime 用例层 | 创建或恢复 Run、解析能力、处理继续动作 | 不执行具体工具 | 案件、任务类型、事实 → 已绑定能力的运行状态 | API 后、LangGraph 前 |
| LangGraph | 串联上下文、计划、执行、观察、验证和决策节点 | 不包含劳动法业务规则 | 当前运行状态 → 更新后的运行状态 | 整个执行骨架 |
| Planner | 根据已注册模板生成不可变 Plan revision | 不是 LLM，不自由创造步骤 | 模板、案件事实 → 有顺序的 Plan Step | 上下文检查后、执行前 |
| ToolExecutor | 检查参数、法域、审批、超时并调用白名单工具 | 不判断法律结论是否正确 | 工具定义、参数 → 统一 ToolResult | 计划步骤后、Observer 前 |
| Observer | 把工具结果整理成统一观察记录 | 不作通过或失败决定 | ToolResult → observation | Executor 后、Verifier 前 |
| Verifier | 校验返回结构、事实、法源和领域规则 | 不推进状态、不选择下一节点 | ToolResult、状态、策略 → 验证报告 | Observer 后、Decider 前 |
| Decider | 把验证结果转换成继续、重试、补信息、重规划、移交或拒绝 | 不执行工具、不修改计划内容 | 验证报告、错误属性 → decision | Verifier 后 |
| Response Generator | 当前没有独立实现 | 不存在自然语言汇总节点 | 各步骤结果 → 直接汇总进 `final_output` | 最后由 Repository 组装 JSON |

## 三、用一个请求跑完整流程

案例：“公司拖欠员工三个月工资，员工应该如何维权？”

先说明真实限制：仅发送这句话不能跑完整 Agent。代码不会从句子自动选择 `labor_consultation`，也无法得到姓名、工资、工作地点、入职日期、时效起算日等必填事实。真实流程需要前端先创建 Matter、确认中国法域，再提交结构化事实。

以下假设调用时明确指定 `task_type=labor_consultation`，并补齐必要事实。

### 1. 请求入口

`POST /api/digital-human/agent/matters/<matter_id>/labor-dispute/run` 进入 Router，然后依次进入 Facade 和 CapabilityRuntime。

### 2. 关键状态初始化

Repository 创建或复用 Run，初始包含案件、客户端、目标、任务类型、`planning` 状态、当前步骤位置、重试次数、工具调用数和预算。劳动事实单独保存在劳动纠纷 Profile，不直接放入 AgentState。

### 3. 第一个执行节点

技术上的首节点是 `dispatch`，它只根据当前状态分流；第一个真正工作的节点是 `ensure_context`，负责检查法域和必填事实。

如果只有示例中的一句话，系统会进入 `awaiting_information`，返回补充问题并停止。

### 4. Planner 生成的计划

`labor_consultation` 使用确定性两步模板：

1. 核对材料与证据缺口。
2. 生成只读劳动法律咨询分析，并计算期限、验证法源。

因为争议类型包含“欠薪”，第一步名称会调整为“核对欠薪期间、金额与工资证据”。

### 5. 步骤如何交给 ToolExecutor

Graph 每次只选择一个 Plan Step，通过 ToolRegistry 取得白名单工具。领域 Adapter 补入 `matter_id`、`client_id` 和法域，PolicyToolExecutor 检查参数、法域、审批和超时后调用工具。

### 6. 工具结果保存在哪里

结果先进入运行状态的最近工具结果字段，同时写入 `ToolCall` 审计记录。Observer 再把数据、证据引用、法源引用、假设、警告和错误整理后保存到当前 Step。

### 7. Verifier 验证什么

- 全局层：工具是否成功、成功结果是否为结构化字典。
- 劳动领域层：期限是否有起算日、开放期限是否标记人工复核、是否存在已验证法源。
- 任务层：工具返回状态、必需字段以及法源引用是否一致。

### 8. Decider 如何决定

- 工具成功且验证通过：执行下一步或结束。
- 错误可重试：重试当前步骤。
- 缺少上下文：暂停并等待用户补充。
- 需要重规划：保存 `replanning` 状态并退出本次 Graph。
- 法源不足：进入 `blocked_authority`。
- 连续重试耗尽：转人工接管。

### 9. 最终结果在哪里生成

当前没有独立回答生成器。每个通过验证的工具结果被放入 `final_output`，Repository 组装 Run、Steps、验证报告和结果快照，Facade 返回给 Router，再以 JSON 返回前端。

因此当前输出更接近“证据清单 + 期限 + 已验证法源”的结构化分析，不是重新润色后的自然语言律师答复。

## 四、循环到底在哪里

当前 Graph 的真实循环如下：

```text
dispatch
  ↓
ensure_context
  ├─ 缺法域或事实 → 暂停并结束本次调用
  ↓
build_plan
  ↓
select_next_step
  ├─ 需审批 → 暂停并结束本次调用
  ├─ 已跳过 → select_next_step
  ↓
execute_step
  ↓
observe_step
  ↓
verify_step
  ↓
decide_step
  ├─ next_step → select_next_step
  ├─ retry_step → execute_step
  ├─ request_context → 暂停并结束
  ├─ replan → 保存重规划状态并结束
  ├─ handoff/reject → 结束
  └─ finish → 完成
```

每轮处理的是一个 Plan Step，不是整个案件。

- `next_step`：当前步骤成功，步骤下标加一。
- `retry_step`：计划不变，重新执行当前步骤；Graph 层只允许一次连续重试，再失败转人工。
- `replan`：当前计划不再适用，退出本次调用；后续重新启动或补充信息时生成新的 Plan revision。
- `finish`：模板步骤已完成，Run 进入 `completed`。

防止死循环的机制：

- 默认最多 6 个计划步骤。
- 最多 8 次工具调用。
- 默认运行时间预算 300 秒。
- Token 预算 12000、成本预算 100 分。
- Graph 层连续重试最多一次。
- 工具本身另有 `max_retries`，但当前劳动工具设置为 0。
- 当前代码没有配置自定义 LangGraph `recursion_limit`，无法确认项目级递归上限。

## 五、源码对应表

| 流程阶段 | 文件 | 类/函数 | 作用 |
| --- | --- | --- | --- |
| HTTP 入口 | `routers/digital_human_agent.py` | `start_labor_dispute_run` | 接收任务类型和事实 |
| 稳定门面 | `legal_agent_system/facade.py` | `start_task` | 同步法源并进入 Runtime |
| Run 用例层 | `runtime/capability_runtime.py` | `CapabilityRuntime.start_task` | 解析能力、创建或恢复 Run |
| 计划模板 | `domains/labor/package.py` | `build_labor_domain_package` | 声明三类劳动任务模板 |
| Planner | `capabilities/plans.py` | `TemplatePlanBuilder` | 生成版本化计划 |
| Graph 骨架 | `runtime/capability_graph.py` | `CapabilityRuntimeGraph` | 串联全部节点 |
| 单步执行 | `runtime/capability_graph.py` | `_execute_step` | 调用一个计划步骤 |
| 工具策略 | `runtime/executor.py` | `PolicyToolExecutor` | 参数、法域、审批和超时控制 |
| 结果验证 | `runtime/verifier.py` | `LayeredVerifier` | 汇总全局和领域验证报告 |
| 路由决策 | `runtime/decision_router.py` | `DecisionRouter` | 决定下一步动作 |
| 最终返回 | `runtime/persistence.py` | `snapshot` | 组装前端运行快照 |

## 六、当前实现边界

### 已实现

- 一套通用 Runtime Graph。
- 中国劳动领域能力包及四种计划模板。
- 单 Plan Step 执行循环。
- 工具白名单、法域检查、审批、预算和审计。
- 全局、领域、任务三层验证报告。
- 暂停补充信息、审批恢复、法源阻断和人工接管状态。
- 不可变 Plan revision 和运行状态持久化。

### 未实现或无法从当前代码确认

- 普通数字人聊天自动转换成可执行 Agent 任务：未实现。
- 由 LLM 自由拆解任务并生成计划：未实现，当前 Planner 使用确定性模板。
- 独立自然语言 Response Generator：未实现。
- 其他真实法律领域：未实现；`domains/mock` 只是兼容能力，不属于真实法律领域。
- 项目自定义 LangGraph `recursion_limit`：无法从当前代码确认。

## 七、阶段 3.7B：劳动问题组合 Plan（已实现）

以下内容已于 2026-07-21 落地；仍属于 3.7B 组合能力，不代表 3.7C 的实体规则深化已经完成。

### 1. 固定 LangGraph，不按案件复制状态图

项目继续只保留一套 `CapabilityRuntimeGraph`。欠薪、辞退、补偿或仲裁申请不会分别创建 Graph。固定 Graph 仍只执行：

```text
ensure_context
→ build_plan
→ select_next_step
→ execute_step
→ observe_step
→ verify_step
→ decide_step
```

### 2. 由 Plan 组合本次案件需要的能力

```text
用户问题和材料
→ 案件分流：领域、任务类型、争议标签、风险
→ 选择一个已审核的主 PlanTemplate
→ 启用模板允许的可选步骤
→ 处理依赖并去重公共步骤
→ 保存新的不可变 Plan revision
→ 固定 Runtime Graph 逐 Step 执行
```

当前按交付目的选择 `labor_case_analysis` 或 `labor_arbitration_application` 主模板；欠薪、试用期、解除和经济补偿不是独立 Graph，而是模板内固定声明的白名单可选步骤。`labor_consultation` 和 `labor_relationship_assessment` 继续保留原职责。所有能力仍属于同一个 `cn_labor` Domain Package。

### 3. 复合问题使用主模板加争议标签

例如用户同时提出欠薪、违法解除和经济补偿：

```text
主模板：labor_arbitration_application
争议标签：wage_arrears + termination + economic_compensation

生成步骤：
1. 公共材料与证据检查
2. 欠薪金额分析
3. 解除事实、依据与程序分析
4. 经济补偿或赔偿估算
5. 统一期限与法源验证
6. 用户审批后的仲裁申请书草稿
```

公共证据检查、法源验证和审批不得重复执行。非劳动问题、法域冲突或高风险问题不得强行塞入劳动 Plan，应明确拒绝、分流或人工接管。

### 4. 计划变化必须创建新 revision

如果用户先只描述欠薪，后来补充“同时被辞退”，旧 Plan 不得原地覆盖：

```text
revision 1：欠薪处理
revision 2：新增违法解除与补偿步骤
```

新 revision 保存稳定争议标签、步骤触发标签、变更原因、父 Plan 和触发者。未启用步骤保留为 `skipped` 并记录 `skip_reason`；未知标签以及 Adapter 插步、换工具或削弱审批会以 `INVALID_PLAN_COMPOSITION` 失败关闭。

## 八、阶段 3.7C：事实、证据、法源和实体规则（已实现）

- `material_adapters/` 按实习协议、劳动合同、Offer、解除通知、考勤、工资记录和聊天记录分类，候选事实保留文档、片段、偏移和原文；采用前仍需用户确认。
- `evidence.py` 将规则字段与已确认事实、支持材料、冲突值和缺口组成证据矩阵，复用现有事实与材料表，不新增数据库结构。
- `labor_rules/` 分离欠薪、试用期、解除和补偿/赔偿规则；劳动关系工具也补入事实、证据和法源引用。
- 所有实体规则使用 `LaborRuleDecision` 返回规则版本、判断、计算、事实引用、证据引用、法源引用、假设、警告和人工复核要求；不得包装为最终法律结论。
- 法源扩充劳动合同法第七、十、十九至二十一条等条款；缺少当前有效来源或关键事实时分别进入法源阻断或补信息状态。
- `evals/labor_disputes/flagship_cases.jsonl` 包含正常、信息不足、非劳动关系、复合争议和高风险五类共25条金标，并区分合成金标与官方公开案例改写。

## 九、产品与开发优先级

当前产品定位为劳动用工法律服务，第一批用户入口为大学生实习、兼职和毕业初期青年劳动者。技术实现保持通用 Runtime，不把核心架构写死成校园系统。

```text
P0  劳动案件分流、劳动关系判断、聊天转 Agent、法源与规则可信性
P1  欠薪/解除/补偿模板、复合问题 Plan 组合、通俗结果解释
P2  数字人文字流式交互、基础语音输入与播报
P3  Live2D、复杂口型、表情和动作
P4  电商、跨境等新法律领域
```

数字人与 Agent 的职责保持清晰：Agent 负责法律任务，数字人负责让普通用户容易描述问题、补充信息、上传材料并理解 Agent 当前状态。下一阶段先打通聊天、Matter 和 Run，不优先追求复杂动画。
