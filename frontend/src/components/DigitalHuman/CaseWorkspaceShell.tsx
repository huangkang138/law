'use client';

import { useState } from 'react';

import { CASE_STAGE_LABELS, useDigitalHumanStore } from '@/store/digitalHumanStore';

import CaseStageContent from './CaseStageContent';
import CaseStageNav from './CaseStageNav';
import DigitalHumanCaseAssistant, { buildCaseAssistantSummary } from './DigitalHumanCaseAssistant';
import { matterStatusLabel, useMatterWorkspace } from './useMatterWorkspace';
import WorkspaceHeader from './WorkspaceHeader';
import WorkspaceSidebar from './WorkspaceSidebar';
import styles from './Workspace.module.css';

const STAGE_ORDER_INDEX: Record<string, number> = {
  jurisdiction: 1,
  material: 2,
  facts: 3,
  analysis: 4,
};

/**
 * 案件工作台外壳：桌面 = 左侧会话/案件导航 + 中间四阶段工作区 + 右侧可收起数字人助手；
 * 移动端 = 侧栏抽屉 + 阶段横滚 + Bottom Sheet 助手。
 * 业务逻辑统一由 useMatterWorkspace 持有（挂载一次），四个 Stage 只接收 props 展示。
 */
export default function CaseWorkspaceShell() {
  const {
    close,
    closeWorkspace,
    sidebarTab,
    setSidebarTab,
    activeStage,
    setActiveStage,
    assistantCollapsed,
    currentMatterId,
    currentAgentRun,
  } = useDigitalHumanStore();
  const flow = useMatterWorkspace();
  // 移动端侧栏抽屉（桌面端为常驻列，CSS 控制）。
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const stageIndex = STAGE_ORDER_INDEX[activeStage] || 1;
  const assistantSummary = buildCaseAssistantSummary({
    run: currentAgentRun,
    analysis: flow.runtimeAnalysis,
    checklist: flow.result?.checklist || null,
    workflowStatus: flow.workflowStatus,
    hasDraft: Boolean(flow.laborDraft),
  });

  return (
    <section className={`${styles.shell} ${assistantCollapsed ? styles.shellAssistantCollapsed : ''}`} role="dialog" aria-label="法小助案件工作台">
      <WorkspaceHeader
        matterId={currentMatterId}
        goal={flow.goal}
        statusLabel={matterStatusLabel(currentAgentRun?.status, flow.workflowStatus)}
        activeStage={activeStage}
        stageIndex={stageIndex}
        onBackToChat={closeWorkspace}
        onClose={close}
        onToggleSidebar={() => setSidebarOpen((open) => !open)}
      />
      <div className={styles.shellBody}>
        <div className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ''}`}>
          <WorkspaceSidebar
            tab={sidebarTab}
            onTabChange={(tab) => {
              setSidebarTab(tab);
              setSidebarOpen(false);
            }}
            matters={flow.matters}
            mattersError={flow.mattersError}
            matterStatuses={flow.matterStatuses}
            statusesLoading={flow.statusesLoading}
            currentMatterId={currentMatterId}
            onRefreshMatters={() => void flow.refreshMatters()}
            onRestoreMatter={(matter) => {
              setSidebarOpen(false);
              void flow.restoreMatter(matter);
            }}
            onRemoveMatter={(matterId) => void flow.removeMatter(matterId)}
            onNewMatter={() => {
              setSidebarOpen(false);
              void flow.startNewMatter();
            }}
          />
        </div>
        {sidebarOpen && (
          <button
            type="button"
            className={styles.sidebarBackdrop}
            aria-label="关闭导航"
            onClick={() => setSidebarOpen(false)}
          />
        )}
        <div className={styles.shellMain}>
          <CaseStageNav
            activeStage={activeStage}
            onSelect={setActiveStage}
            materialCount={flow.result ? flow.result.checklist.available.length : null}
            factCount={flow.result ? flow.result.facts.length : null}
            hasRun={Boolean(currentAgentRun)}
          />
          <CaseStageContent flow={flow} />
          <footer className={styles.shellFooter}>
            本工作台产出均为 AI 辅助草稿：正式提交前必须人工复核；
            法律结论以官方法源为准，重要事项请咨询专业律师。草稿不代表已提交任何机构。
          </footer>
        </div>
        <DigitalHumanCaseAssistant
          stageLabel={CASE_STAGE_LABELS[activeStage]}
          summary={assistantSummary}
        />
      </div>
    </section>
  );
}
