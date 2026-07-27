# 工作流

## 核心原则

Mode 和状态是 Agent 内部机制，用户只需自然表达目标。用户目标高于旧 `CURRENT_TASK`；若不一致，标记 `CURRENT_TASK_MISMATCH`，先修正当前任务，绝不继续执行旧目标。

## TASK INTAKE / CLARIFY

所有新任务先经过统一入口：用户自然语言请求 → TASK INTAKE → 检查上下文 → 信息充分则自动路由；只有真正影响方向、范围、产品行为、架构、数据结构、高风险操作或验收的歧义才 CLARIFY。

提问前必须先调查：读取 CURRENT_TASK、NEXT_STEP，识别项目模块并阅读直接相关源码；按需读取最新项目分析、相关 DECISIONS、按关键词查询修改日志，架构任务再读相关 `raw/`。能从项目得到的答案不得再问用户。

- 正常一次最多 1～3 个问题；一个问题能解决就只问一个，优先一轮完成。
- 每个问题必须有决策价值：不同回答会实际改变实现方式。存在明确候选时给选项和推荐，不要求用户重写完整需求。
- 低风险、易回退、不改公开契约、不扩大范围的小歧义，沿用当前项目的合理默认值并简短说明，不打断用户。
- 用户回答后由 Agent 自动更新/初始化 CURRENT_TASK：目标、背景、已确认决策、范围、禁止项和验收；随后自动选择 Mode。

“继续当前任务”且 CURRENT_TASK 已清楚时不提问；用户补充改变范围时自动更新，只有重要影响才确认一次。TASK INTAKE 解决“要做什么”，ARCHITECTURE 解决“技术上如何设计”。

## 自动路由

| 用户意图 | 默认方式 |
| --- | --- |
| 实现、增加、完善、继续开发明确功能 | FEATURE |
| 报错、回归、行为异常 | BUGFIX |
| 页面、UI、样式、布局、交互体验 | FRONTEND |
| 方案、边界、架构、高风险且方案不明确 | ARCHITECTURE |
| 检查、验收、审核、完成了吗 | REVIEW |
| 带我看代码、解释调用关系 | LEARN |

只有意图冲突、高风险不可逆操作，或无法判断“修改还是分析”时才询问。用户明确指定 Mode 时强制采用。

## CURRENT_TASK 生命周期

新想法或 `NEXT_STEP` 必须先初始化为 `CURRENT_TASK`：`PLANNED`。高风险任务进入 `DESIGNING → ARCHITECTURE → APPROVED`；明确任务进入 `IMPLEMENTING` 后执行。技术验证为 `VERIFYING`，随后 REVIEW。

REVIEW 不通过：`FAILED_REVIEW`，返回 FEATURE、BUGFIX、FRONTEND 或 ARCHITECTURE。通过且无需人工体验确认：`COMPLETED`；前端、数字人、浏览器交互、设备或用户业务流程：`READY_FOR_ACCEPTANCE → 用户接受 → COMPLETED`。不得自动开始 `NEXT_STEP`。

更新任务文档只是初始化，不代表业务完成。

## 不满意后的自动返工

用户说“不满意”“做偏了”“页面不好看”“还有问题”“重新调整”时先判断：

- 实现偏离需求：保持 CURRENT_TASK，最小修正 → FEATURE。
- 局部行为错误：→ BUGFIX，不重做架构。
- 方案/边界错误：→ ARCHITECTURE，重新确认后再实现。
- 视觉或交互不满意：→ FRONTEND，保持正确业务逻辑。
- 仅不满意说明或报告：不改代码、不改 CURRENT_TASK，只重组输出。

若原因已明确，禁止重复询问；原因完全不明时最多问一个问题，例如“主要是不满意功能行为、整体方案，还是页面效果？”。REVIEW 后的新诉求先经 Intake 判断是原任务返工还是新任务。

## 安全与收尾

不满意不自动 `git reset --hard` 或 `git clean`。只有用户明确要求撤销时，先检查 status/diff、区分任务前已有改动与本任务改动、说明拟撤销范围并获得确认，再只撤销本任务范围。

完成后按需更新 `DEVELOPER_MEMORY`、`DECISIONS`、`NEXT_STEP` 与 `modification-log`；结构性事实变化同步 `latest-project-analysis`。
