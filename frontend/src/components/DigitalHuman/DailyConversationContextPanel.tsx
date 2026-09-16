'use client';

import { ArrowRight, FileText, MessageCircle } from 'lucide-react';

import { laborFactLabel } from './LaborDisputeForm';
import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import styles from './DailyConversationPage.module.css';

const TRIAGE_LABELS: Record<string, string> = {
  simple_labor_consultation: '劳动咨询',
  labor_relationship_assessment: '劳动关系判断',
  formal_labor_dispute: '正式劳动纠纷',
  non_labor_dispute: '非劳动纠纷',
  high_risk_handoff: '高风险人工处理',
};

const RELATIONSHIP_LABELS: Record<string, string> = {
  not_assessed: '尚未判断劳动关系',
  uncertain: '劳动关系待确认',
  likely_established: '倾向存在劳动关系',
  likely_not_established: '倾向不构成劳动关系',
};

const RISK_LABELS: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
};

const RUN_STATUS_LABELS: Record<string, string> = {
  planning: '规划中',
  awaiting_jurisdiction: '等待确认法域',
  awaiting_information: '等待补充信息',
  executing: '执行中',
  observing: '观察中',
  verifying: '验证中',
  deciding: '判断中',
  retrying: '重试中',
  awaiting_approval: '等待人工审批',
  blocked_authority: '法源受阻',
  replanning: '重新规划中',
  human_handoff: '等待人工处理',
  completed: '已完成',
  failed: '处理失败',
  cancelled: '已取消',
};

function formatUpdatedAt(value: string | null | undefined): string {
  if (!value) return '暂无更新时间';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '暂无更新时间';
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}
function uniqueItems(items: Array<string | null | undefined>): string[] {
  return Array.from(new Set(items.map((item) => item?.trim()).filter((item): item is string => Boolean(item))));
}

interface DailyConversationContextPanelProps {
  statusLabel: string;
  onOpenWorkspace: () => void;
}

export default function DailyConversationContextPanel({
  statusLabel,
  onOpenWorkspace,
}: DailyConversationContextPanelProps) {
  const {
    currentAgentRun,
    currentMatter,
    currentMatterId,
    currentTriage,
    laborTriageError,
    laborTriageLoading,
    messages,
    sessionId,
    sessions,
    voiceEnabled,
    voiceSpeaking,
    workspaceError,
    workspaceLoading,
    workspacePresentation,
  } = useDigitalHumanStore();

  const currentSession = sessions.find((session) => session.id === sessionId);
  const lastUserMessage = [...messages].reverse().find((message) => message.role === 'user')?.content || '';
  const currentStep = currentAgentRun?.steps.find((step) => step.id === currentAgentRun.current_step_id);
  const missingItems = uniqueItems([
    ...(currentTriage?.result.missing_facts || []),
    ...(currentTriage?.result.questions || []),
    ...(currentAgentRun?.missing_facts || []),
    ...(currentAgentRun?.questions || []),
  ]).slice(0, 4);
  const errorMessage = workspaceError || laborTriageError;

  return (
    <aside className={styles.contextRail} aria-label="法小助当前会话与案件状态">
      <header className={styles.contextHeader}>
        <div>
          <span className={styles.contextEyebrow}>LIVE CONTEXT</span>
          <h2>当前状态</h2>
        </div>
        <span className={styles.contextLive}><i />真实数据</span>
      </header>

      <div className={styles.contextScroll}>
        <section className={styles.contextSection}>
          <div className={styles.contextSectionTitle}>
            <MessageCircle size={14} />
            <span>当前会话</span>
            <span className={styles.contextBadge}>{sessionId ? '已连接' : '未建立'}</span>
          </div>
          <strong className={styles.contextPrimary}>{currentSession?.title || '法小助日常交流'}</strong>
          <p>{currentSession ? `最近更新 ${formatUpdatedAt(currentSession.updated_at)}` : sessionId ? '当前会话正在使用' : '发送问题后会保存到历史记录'}</p>
        </section>

        <section className={styles.contextSection}>
          <div className={styles.contextSectionTitle}>
            <FileText size={14} />
            <span>当前案件</span>
          </div>
          {currentMatterId ? (
            <>
              <strong className={styles.contextPrimary}>{currentMatter?.title || currentMatter?.goal || '已关联当前案件'}</strong>
              <p>{currentMatter?.goal || `案件 ID · ${currentMatterId.slice(0, 8)}`}</p>
              <button type="button" className={styles.contextAction} onClick={onOpenWorkspace}>
                打开案件工作台 <ArrowRight size={14} />
              </button>
            </>
          ) : (
            <p className={styles.contextEmpty}>当前对话暂未关联案件，普通咨询不会自动创建案件。</p>
          )}
        </section>

        <section className={styles.contextSection}>
          <div className={styles.contextSectionTitle}>
            <span>劳动分流</span>
            <span className={styles.contextBadge}>{currentTriage ? '已同步' : laborTriageLoading ? '同步中' : '暂无记录'}</span>
          </div>
          {currentTriage ? (
            <>
              <div className={styles.contextMetrics}>
                <div><small>场景</small><strong>{TRIAGE_LABELS[currentTriage.result.triage_type] || currentTriage.result.triage_type}</strong></div>
                <div><small>风险</small><strong>{RISK_LABELS[currentTriage.result.risk_level] || currentTriage.result.risk_level}</strong></div>
              </div>
              <p>{RELATIONSHIP_LABELS[currentTriage.result.relationship_status] || currentTriage.result.relationship_status}</p>
              <p className={styles.contextNext}>{currentTriage.result.recommended_next_step}</p>
            </>
          ) : (
            <p className={styles.contextEmpty}>{laborTriageLoading ? '正在读取真实分流状态…' : '当前暂无真实劳动分流结果。'}</p>
          )}
          {missingItems.length > 0 && (
            <div className={styles.contextMissing}>
              <small>缺失 / 待确认</small>
              {missingItems.map((item) => <span key={item}>· {laborFactLabel(item)}</span>)}
            </div>
          )}
        </section>

        <section className={styles.contextSection}>
          <div className={styles.contextSectionTitle}>
            <span>处理进度</span>
            <span className={styles.contextBadge}>
              {currentAgentRun ? (RUN_STATUS_LABELS[currentAgentRun.status] || currentAgentRun.status) : workspaceLoading ? '同步中' : '待开始'}
            </span>
          </div>
          {currentAgentRun ? (
            <>
              <strong className={styles.contextPrimary}>{currentStep?.name || '案件任务处理中'}</strong>
              {currentAgentRun.blocked_reason && <p>{currentAgentRun.blocked_reason}</p>}
              {currentAgentRun.approval?.prompt && <p className={styles.contextNext}>{currentAgentRun.approval.prompt}</p>}
            </>
          ) : workspacePresentation ? (
            <>
              <strong className={styles.contextPrimary}>{workspacePresentation.headline}</strong>
              <p>{workspacePresentation.summary}</p>
              {workspacePresentation.requires_user_action && <p className={styles.contextNext}>{workspacePresentation.next_action.label}</p>}
            </>
          ) : (
            <p className={styles.contextEmpty}>当前暂无案件工作台状态。</p>
          )}
        </section>

        <section className={styles.contextSection}>
          <div className={styles.contextSectionTitle}><span>最近提问</span></div>
          <p className={lastUserMessage ? styles.contextQuote : styles.contextEmpty}>
            {lastUserMessage || '还没有用户消息'}
          </p>
        </section>

        <section className={styles.contextSection}>
          <div className={styles.contextSectionTitle}><span>服务状态</span></div>
          <div className={styles.contextServiceRow}><span>法小助</span><strong>{statusLabel}</strong></div>
          <p>语音播报：{voiceSpeaking ? '进行中' : voiceEnabled ? '已开启' : '未开启'}</p>
        </section>

        {errorMessage && <p className={styles.contextError}>{errorMessage}</p>}
      </div>

      <footer className={styles.contextFooter}>右栏只展示当前 Store 与后端返回的数据，不生成新的法律结论。</footer>
    </aside>
  );
}
