'use client';

import { Menu, MessageCircle, Minus } from 'lucide-react';

import { CASE_STAGE_LABELS, CaseStage } from '@/store/digitalHumanStore';
import styles from './Workspace.module.css';

interface WorkspaceHeaderProps {
  matterId: string | null;
  goal: string;
  statusLabel: string;
  activeStage: CaseStage;
  stageIndex: number;
  onBackToChat: () => void;
  onClose: () => void;
  onToggleSidebar: () => void;
}

/** 工作台头栏：当前案件 + 状态 + 当前阶段 + 返回对话/收起（移动端含侧栏开关）。 */
export default function WorkspaceHeader({
  matterId, goal, statusLabel, activeStage, stageIndex,
  onBackToChat, onClose, onToggleSidebar,
}: WorkspaceHeaderProps) {
  return (
    <header className={styles.shellHeader}>
      <div className={styles.shellHeaderLeft}>
        <button
          type="button"
          className={styles.shellMenuButton}
          onClick={onToggleSidebar}
          aria-label="打开会话与案件导航"
        >
          <Menu size={18} />
        </button>
        <div className={styles.shellHeaderTitle}>
          <div className="dh-title-row">
            <h2>{matterId ? goal : '案件工作台'}</h2>
            <span className="dh-online-dot" aria-label="在线" />
          </div>
          <p>
            {matterId
              ? `第 ${stageIndex} 阶段 · ${CASE_STAGE_LABELS[activeStage]}`
              : '目标与法域 · 材料整理 · 事实与证据 · 分析与文书'}
          </p>
        </div>
        {matterId && <span className={styles.shellStatusChip}>{statusLabel}</span>}
      </div>
      <div className="dh-header-actions">
        <button
          type="button"
          className="dh-workspace-switch"
          onClick={onBackToChat}
          aria-label="返回对话"
          title="返回对话"
        >
          <MessageCircle size={16} />
          <span>返回对话</span>
        </button>
        <button type="button" onClick={onClose} aria-label="收起法小助" title="收起">
          <Minus size={19} />
        </button>
      </div>
    </header>
  );
}
