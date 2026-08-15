'use client';

import { MessageSquare, Plus, Trash2 } from 'lucide-react';
import { useState } from 'react';

import type {
  DigitalHumanMatterSummary,
  LaborDisputeWorkflow,
} from '@/services/digitalHumanApi';
import { CASE_STAGE_LABELS, useDigitalHumanStore } from '@/store/digitalHumanStore';
import { matterStatusLabel } from './useMatterWorkspace';
import styles from './Workspace.module.css';

interface WorkspaceSidebarProps {
  tab: 'sessions' | 'matters';
  onTabChange: (tab: 'sessions' | 'matters') => void;
  matters: DigitalHumanMatterSummary[];
  mattersError: string;
  matterStatuses: Record<string, LaborDisputeWorkflow['status'] | null>;
  statusesLoading: boolean;
  currentMatterId: string | null;
  onRefreshMatters: () => void;
  onRestoreMatter: (matter: DigitalHumanMatterSummary) => void;
  onRemoveMatter: (matterId: string) => void;
  onNewMatter: () => void;
}

const WORKFLOW_STATUS_LABELS: Record<LaborDisputeWorkflow['status'], string> = {
  awaiting_information: '待补充信息',
  ready: '材料就绪',
  blocked_authority: '法源受阻',
  awaiting_draft_approval: '待确认草稿',
  completed: '已完成',
};

/** 左侧导航（约 250px）：[会话][案件] Tab 切换，会话 ≠ 案件但可展示关联。 */
export default function WorkspaceSidebar({
  tab, onTabChange, matters, mattersError, matterStatuses, statusesLoading,
  currentMatterId, onRefreshMatters, onRestoreMatter, onRemoveMatter, onNewMatter,
}: WorkspaceSidebarProps) {
  const {
    sessions,
    sessionId,
    loadSession,
    deleteSession,
    startNewConversation,
    refreshHistory,
    historyError,
    laborContextBySession,
    currentMatter,
    activeStage,
    currentAgentRun,
  } = useDigitalHumanStore();

  const matterTitleById = new Map(matters.map((matter) => [matter.matter_id, matter.title]));
  const inProgress = matters.filter((matter) => matterStatuses[matter.matter_id] !== 'completed');
  const completed = matters.filter((matter) => matterStatuses[matter.matter_id] === 'completed');
  const [showAllSessions, setShowAllSessions] = useState(false);
  const currentSession = sessions.find((session) => session.id === sessionId);
  const recentSessions = sessions.filter((session) => session.id !== sessionId);
  const visibleRecentSessions = showAllSessions ? recentSessions : recentSessions.slice(0, 4);
  const prioritizeCurrentMatter = (items: DigitalHumanMatterSummary[]) => [
    ...items.filter((matter) => matter.matter_id === currentMatterId),
    ...items.filter((matter) => matter.matter_id !== currentMatterId),
  ];

  return (
    <aside className={styles.sidebarInner} aria-label="会话与案件导航">
      {currentMatterId && currentMatter && (
        <div className={styles.sidebarCurrentCase}>
          <small>当前案件</small>
          <strong>{currentMatter.title || currentMatter.goal}</strong>
          <p>{CASE_STAGE_LABELS[activeStage]} · {matterStatusLabel(currentAgentRun?.status, matterStatuses[currentMatterId] ?? null)}</p>
        </div>
      )}
      <div className={styles.sidebarTabs} role="tablist" aria-label="导航类型">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'sessions'}
          className={`${styles.sidebarTab} ${tab === 'sessions' ? styles.sidebarTabActive : ''}`}
          onClick={() => onTabChange('sessions')}
        >
          <MessageSquare size={13} /> 会话
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'matters'}
          className={`${styles.sidebarTab} ${tab === 'matters' ? styles.sidebarTabActive : ''}`}
          onClick={() => onTabChange('matters')}
        >
          案件
        </button>
      </div>

      {tab === 'sessions' && (
        <div className={styles.sidebarSection}>
          <button type="button" className={styles.sidebarNew} onClick={startNewConversation}>
            <Plus size={13} />新建会话
          </button>
          {historyError && (
            <p className={styles.sidebarError}>
              {historyError}
              <button type="button" onClick={() => void refreshHistory()}>重试</button>
            </p>
          )}
          {currentSession && <>
            <p className={styles.sidebarGroupLabel}>当前会话</p>
            {renderSessionItem(currentSession, true)}
          </>}
          <p className={styles.sidebarGroupLabel}>最近会话</p>
          {sessions.length === 0 && <p className={styles.sidebarEmpty}>暂无历史会话</p>}
          {visibleRecentSessions.map((session) => renderSessionItem(session, false))}
          {recentSessions.length > 4 && <button type="button" className={styles.sidebarShowAll} onClick={() => setShowAllSessions((show) => !show)}>
            {showAllSessions ? '收起会话' : `查看全部会话（${recentSessions.length}）`}
          </button>}
          <p className={styles.sidebarNote}>会话 ≠ 案件。案件是材料、事实与文书的容器，历史案件请到「案件」页管理。</p>
        </div>
      )}

      {tab === 'matters' && (
        <div className={styles.sidebarSection}>
          <button type="button" className={styles.sidebarNew} onClick={onNewMatter}>
            <Plus size={13} />新建案件
          </button>
          {mattersError && (
            <p className={styles.sidebarError}>
              {mattersError}
              <button type="button" onClick={onRefreshMatters}>重试</button>
            </p>
          )}
          {statusesLoading && <p className={styles.sidebarGroupLabel}>案件状态读取中…</p>}
          <p className={styles.sidebarGroupLabel}>办理中</p>
          {inProgress.length === 0 && <p className={styles.sidebarEmpty}>暂无进行中的案件</p>}
          {prioritizeCurrentMatter(inProgress).map((matter) => renderMatterItem(matter, matterStatuses[matter.matter_id]))}
          <p className={styles.sidebarGroupLabel}>已完成 / 已归档</p>
          {completed.length === 0 && <p className={styles.sidebarEmpty}>暂无已完成的案件</p>}
          {prioritizeCurrentMatter(completed).map((matter) => renderMatterItem(matter, matterStatuses[matter.matter_id]))}
        </div>
      )}
    </aside>
  );

  function renderSessionItem(session: typeof sessions[number], isCurrent: boolean) {
    const linkedMatterId = laborContextBySession[session.id]?.matterId;
    const linkedTitle = linkedMatterId ? matterTitleById.get(linkedMatterId) : undefined;
    return <div key={session.id} className={`${styles.sidebarItem} ${isCurrent ? styles.sidebarItemCurrent : ''}`}>
      <button type="button" className={styles.sidebarItemMain} onClick={() => void loadSession(session.id)}>
        <strong>{session.title}</strong>
        <small>{isCurrent ? '当前会话' : '点击切换'}</small>
        {linkedMatterId && <small className={styles.sidebarLinked}>关联案件：{linkedTitle || '已关联案件'}</small>}
      </button>
      <button type="button" className={styles.sidebarItemAction} onClick={() => void deleteSession(session.id)} aria-label={`删除会话：${session.title}`}>
        <Trash2 size={13} />
      </button>
    </div>;
  }

  function renderMatterItem(
    matter: DigitalHumanMatterSummary,
    status: LaborDisputeWorkflow['status'] | null | undefined,
  ) {
    return (
      <div
        key={matter.matter_id}
        className={`${styles.sidebarItem} ${matter.matter_id === currentMatterId ? styles.sidebarItemCurrent : ''}`}
      >
        <button
          type="button"
          className={styles.sidebarItemMain}
          onClick={() => onRestoreMatter(matter)}
        >
          <strong>{matter.title}</strong>
          <small>
            {status ? WORKFLOW_STATUS_LABELS[status] : '待办理'}
            {matter.matter_id === currentMatterId ? ' · 当前案件' : ' · 继续处理'}
          </small>
        </button>
        <button
          type="button"
          className={styles.sidebarItemAction}
          onClick={() => onRemoveMatter(matter.matter_id)}
          aria-label={`删除案件：${matter.title}`}
        >
          <Trash2 size={13} />
        </button>
      </div>
    );
  }
}
