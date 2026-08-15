'use client';

import { ArrowRight, FolderOpen, Sparkles } from 'lucide-react';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import styles from './Workspace.module.css';

interface MatterEntryCardProps {
  expanded: boolean;
}

/**
 * 聊天窗内的轻量案件入口：
 * - 有关联案件：当前案件状态卡片 + [继续办理 →]（不把工作台内容塞回聊天窗）；
 * - 无当前案件：轻量入口卡片（从当前对话创建案件 / 打开历史案件），
 *   由聊天头部"案件工作台"按钮展开，不直接进入完整工作台。
 */
export default function MatterEntryCard({ expanded }: MatterEntryCardProps) {
  const {
    currentMatterId,
    currentMatter,
    messages,
    openWorkspace,
    setWorkspaceGoalDraft,
    setSidebarTab,
    workspacePresentation,
  } = useDigitalHumanStore();

  const lastUserMessage = [...messages].reverse().find((message) => message.role === 'user')?.content || '';

  const createFromChat = () => {
    // 从当前对话创建案件：把最近一条用户问题预填为案件目标，用户在工作台确认后创建。
    if (lastUserMessage) setWorkspaceGoalDraft(lastUserMessage);
    openWorkspace();
  };

  const openHistory = () => {
    setSidebarTab('matters');
    openWorkspace();
  };

  if (currentMatterId) {
    return (
      <section className={styles.entryCard} aria-label="当前关联案件">
        <span className={styles.entryTag}>当前关联案件</span>
        <strong className={styles.entryTitle}>{currentMatter?.title || currentMatter?.goal || '当前案件'}</strong>
        <small className={styles.entryStatus}>{workspacePresentation?.headline || '办理中'}</small>
        <button type="button" className={styles.entryGo} onClick={openWorkspace}>
          继续办理 <ArrowRight size={14} />
        </button>
      </section>
    );
  }

  if (!expanded) return null;

  return (
    <section className={styles.entryCard} aria-label="案件工作台入口">
      <span className={styles.entryTag}>案件工作台</span>
      <strong className={styles.entryTitle}>还没有当前案件</strong>
      <small className={styles.entryStatus}>
        你可以把当前复杂法律问题整理成一个案件，持续管理材料、事实、证据、分析结果与文书。
      </small>
      <div className={styles.entryActions}>
        <button type="button" onClick={createFromChat}><Sparkles size={13} />从当前对话创建案件</button>
        <button type="button" onClick={openHistory}><FolderOpen size={13} />打开历史案件</button>
      </div>
    </section>
  );
}
