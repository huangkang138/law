# LAW-DEV｜日常开发工作流

用于明确的功能开发、缺陷修复和实现返工。目标是在严格控制范围的前提下，一次完成定位、实现、测试与验收闭环。

## 执行流程

收到具体任务后连续执行：

```text
理解需求
→ 定位局部调用链
→ 确定最小修改点
→ 实施修改
→ 补充或修改测试
→ 执行相关测试
→ 检查 git diff
→ 输出最终验收报告
```

任务边界明确时不得拆成多轮询问。只有缺少必须信息、不同解释会造成明显架构差异，或需求会突破阶段边界并造成大范围破坏时才暂停确认。

## 架构边界

保持现有主链：

```text
Conversation / Triage
→ Matter
→ LegalAgentFacade
→ CapabilityRuntime
→ CapabilityRuntimeGraph
→ Domain Adapter
→ Tool / ToolRegistry
→ Labor Service / Rule
→ Verifier / Decision
→ Persistence
```

- Router 只处理 HTTP 参数、权限和错误映射。
- Facade 只提供稳定入口、装配和转发。
- `CapabilityRuntimeGraph` 保持唯一通用 Runtime Graph。
- 劳动领域特殊逻辑进入 `domains/labor/`，劳动业务规则进入 `labor_disputes/`。
- Runtime 动作必须经 ToolRegistry 白名单执行。
- 不绕过 Executor、Verifier、审批、法域和法源检查。
- 不自动确认材料候选事实；Plan 变化必须保留 revision。
- 不为当前任务顺手重构无关代码或扩大阶段范围。

## 最小改动

修改前只确认本任务的：

```text
任务入口
→ 真正发生行为变化的位置
→ 下游结果
```

禁止无关重命名、格式化、目录调整、类型抽象、旧代码清理和稳定模块重写。已有 Service、Rule、Tool 或 Adapter 可以复用时优先复用。

动态调用必须核对真实绑定：

```text
Plan Step
→ tool_name
→ ToolRegistry
→ handler
→ Service
→ Rule
```

不得仅根据函数名称推断调用关系，也不得为了局部任务重新遍历整个项目。

## 测试

修改完成后必须实际执行测试，优先顺序：

1. 本次新增或修改的测试。
2. 当前模块相关测试。
3. 受影响核心模块回归测试。

修改 Runtime、Graph、Adapter、Plan、Registry、Verifier 或 Persistence 时，必须补充相关回归检查。测试应验证输入、行为、状态变化和最终输出；只覆盖本任务实际涉及的成功、信息不足、法源不足、审批、retry、replan、handoff/reject 或 completed 状态。

## Diff 与法律安全验收

完成后执行：

```text
git diff --stat
git diff
```

确认：

- 没有任务范围外修改和无关格式化。
- 新逻辑已接入真实入口并能传递到最终结果。
- 状态写入与实际运行结果一致。
- 未绕过 ToolRegistry、Verifier、审批、法源或法域检查。
- 关键事实、法域或法源不足时仍失败关闭。
- 用户候选事实仍需确认，高风险动作仍需审批。
- 不确定结果未包装成确定法律结论，人工复核边界仍保留。

发现无关修改时只撤销本任务产生的内容，不得覆盖用户已有未提交工作。

## 最终输出

```text
## 结论
完成 / 部分完成 / 无法完成

## 本次目标
一句话说明解决了什么。

## 实际修改
- 文件：修改原因

## 本次局部调用链
入口
→ ...
→ 【修改点】
→ ...
→ 最终结果

## Before → After
Before：原来的实际行为。
After：修改后的实际行为。

## 测试
执行命令：
...

结果：
XX passed / XX failed

## Diff 验收
任务范围外修改：无 / 有
架构边界变化：无 / 有
未解决风险：无 / 有

## 我需要人工检查
最多列 1～3 个真正值得检查的位置：
文件 → 函数/类 → 原因
```

失败测试必须说明原因以及是否由本次修改造成。最终报告只讲本次局部调用链，不重新解析整个项目。
