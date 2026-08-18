'use client';

import { ChevronRight, Square, Volume2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

import type {
  DigitalHumanAgentRun,
  LaborAnalysisResult,
  LaborDisputeWorkflow,
  MatterAnalysisResult,
} from '@/services/digitalHumanApi';
import { isTtsSupported } from '@/lib/voice/ttsController';
import { useVoiceReady } from '@/lib/voice/useVoiceReady';
import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import ConversationComposer from './ConversationComposer';
import ConversationMessageContent from './ConversationMessageContent';
import DigitalHumanAvatar from './DigitalHumanAvatar';
import { laborFactLabel } from './LaborDisputeForm';
import { humanizeLaborMessage } from './useMatterWorkspace';
import styles from './Workspace.module.css';

export interface CaseAssistantSummary {
  judgments: string[];
  nextSteps: string[];
  missingItems: string[];
}

interface CaseAssistantSummaryInput {
  run: DigitalHumanAgentRun | null;
  analysis: LaborAnalysisResult | undefined;
  checklist: MatterAnalysisResult['checklist'] | null;
  workflowStatus: LaborDisputeWorkflow['status'] | null;
  hasDraft: boolean;
}

function uniqueItems(items: Array<string | null | undefined>): string[] {
  return Array.from(new Set(items.map((item) => item?.trim()).filter((item): item is string => Boolean(item))));
}

/** 仅把现有案件结果压缩为右栏工作摘要，不产生新的案件判断。 */
export function buildCaseAssistantSummary({
  run, analysis, checklist, workflowStatus, hasDraft,
}: CaseAssistantSummaryInput): CaseAssistantSummary {
  const decisions = analysis?.rule_decisions || [];
  const judgments = decisions
    .filter((decision) => decision.status === 'completed' && decision.assessment.trim())
    .map((decision) => decision.assessment)
    .slice(0, 2);
  const missingItems = uniqueItems([
    ...decisions.flatMap((decision) => decision.missing_facts.map((fact) => `待确认：${laborFactLabel(fact)}`)),
    ...(analysis?.missing_rule_facts || []).map((fact) => `待确认：${laborFactLabel(fact)}`),
    ...(analysis?.deadline?.warnings || []),
    ...(run?.questions || []),
    run?.blocked_reason ? humanizeLaborMessage(run.blocked_reason) : null,
    ...(checklist?.missing || []).map((item) => `缺少材料：${item}`),
    checklist?.warning,
  ]);
  const nextSteps = hasDraft
    ? ['仲裁申请草稿已生成，可在中间区域预览或导出。']
    : run?.status === 'awaiting_approval'
      ? [run.approval?.prompt || '请确认生成仲裁申请草稿。']
      : workflowStatus === 'awaiting_draft_approval'
        ? ['当前案件等待确认生成草稿。']
        : missingItems.length > 0
          ? ['请先补充待确认信息，再继续案件分析。']
          : ['可继续向法小助补充案件信息或询问下一步。'];

  return { judgments, nextSteps, missingItems };
}

interface DigitalHumanCaseAssistantProps {
  stageLabel: string;
  summary: CaseAssistantSummary;
}

/** 右栏只保留当前案件摘要与主动展开的最近上下文，完整聊天仍在对话态。 */
export default function DigitalHumanCaseAssistant({
  stageLabel,
  summary,
}: DigitalHumanCaseAssistantProps) {
  const messagesRef = useRef<HTMLDivElement>(null);
  const {
    assistantCollapsed,
    setAssistantCollapsed,
    emotion,
    isLoading,
    messages,
    speakMessage,
    speakingMessageId,
    stopSpeaking,
    streamingMessage,
    voiceSpeaking,
    workspaceError,
  } = useDigitalHumanStore();
  const voiceReady = useVoiceReady();
  const ttsSupported = voiceReady && isTtsSupported();
  const [preset, setPreset] = useState<string | null>(null);
  const [focusSignal, setFocusSignal] = useState(0);
  const [unread, setUnread] = useState(0);
  const lastMessageCount = useRef(0);
  const visibleMessages = [...messages, ...(streamingMessage ? [streamingMessage] : [])].slice(-4);

  useEffect(() => {
    const container = messagesRef.current;
    if (container) container.scrollTop = container.scrollHeight;
  }, [visibleMessages, isLoading]);

  useEffect(() => {
    const count = messages.length + (streamingMessage ? 1 : 0);
    if (assistantCollapsed && count > lastMessageCount.current) {
      setUnread((current) => current + (count - lastMessageCount.current));
    }
    lastMessageCount.current = count;
  }, [assistantCollapsed, messages.length, streamingMessage]);

  useEffect(() => {
    if (!assistantCollapsed) setUnread(0);
  }, [assistantCollapsed]);

  return <aside className={`${styles.assistant} ${assistantCollapsed ? styles.assistantCollapsed : ''}`} aria-label="法小助案件上下文助手">
    <div className={styles.assistantRail}>
      <button type="button" className={styles.assistantExpand} onClick={() => setAssistantCollapsed(false)} aria-label="展开法小助助手">
        <DigitalHumanAvatar emotion={emotion} isLoading={isLoading} voiceSpeaking={voiceSpeaking} size="small" />
        <span className={styles.railStatus} aria-hidden="true" />
        {emotion === 'thinking' && <span className={styles.railThinking} aria-label="正在思考" />}
        {voiceSpeaking && <span className={styles.railWave} aria-hidden="true"><i /><i /><i /></span>}
        {unread > 0 && <span className={styles.railUnread}>{unread > 9 ? '9+' : unread}</span>}
      </button>
      <span className={styles.railStage}>{stageLabel.slice(0, 1)}</span>
    </div>

    <div className={styles.assistantBody}>
      <div className={styles.assistantHead}>
        <DigitalHumanAvatar emotion={emotion} isLoading={isLoading} voiceSpeaking={voiceSpeaking} size="small" />
        <div className={styles.assistantHeadText}><strong>法小助 🟢</strong><small>当前：{stageLabel}</small></div>
        <button type="button" className={styles.assistantCollapse} onClick={() => setAssistantCollapsed(true)} aria-label="收起法小助助手" title="收起助手"><ChevronRight size={16} /></button>
      </div>

      <div className={styles.assistantWorkSummary}>
        {summary.judgments.length > 0 && <section>
          <strong>当前判断</strong>
          {summary.judgments.map((item) => <p key={item}>{item}</p>)}
        </section>}
        <section>
          <strong>下一步建议</strong>
          {summary.nextSteps.map((item) => <p key={item}>{item}</p>)}
        </section>
        {summary.missingItems.length > 0 && <section>
          <strong>缺失 / 待确认</strong>
          {summary.missingItems.slice(0, 4).map((item) => <p key={item}>• {item}</p>)}
        </section>}
      </div>
      {workspaceError && <p className={styles.assistantNotice}>{workspaceError}</p>}

      <div className={styles.assistantActions}>
        <button type="button" onClick={() => setPreset(`请解释一下「${stageLabel}」这一步在做什么，我需要注意什么？`)}>解释当前步骤</button>
        <button type="button" onClick={() => setPreset('帮我检查一下当前案件的材料，看看还缺什么。')}>帮我检查材料</button>
        <button type="button" onClick={() => setPreset('本案相关的法律依据有哪些？请列出相关官方依据。')}>相关法律依据</button>
        <button type="button" onClick={() => setFocusSignal((value) => value + 1)}>继续提问</button>
      </div>

      <details className={styles.assistantContext}>
        <summary>最近上下文{visibleMessages.length ? `（${visibleMessages.length}）` : ''}</summary>
        <div ref={messagesRef} className="dh-companion-messages" aria-live="polite">
          {visibleMessages.map((message) => <div key={message.id} className={`dh-companion-message ${message.role}`}>
            <div className="dh-companion-message-head">
              <span>{message.role === 'assistant' ? '法小助' : '你'}</span>
              {message.role === 'assistant' && streamingMessage?.id !== message.id && ttsSupported && <button type="button" className={`dh-companion-speak ${speakingMessageId === message.id ? 'dh-companion-speak-active' : ''}`} onClick={() => (speakingMessageId === message.id ? stopSpeaking() : speakMessage(message.id, message.content))} aria-label={speakingMessageId === message.id ? '停止朗读' : '朗读这条回复'} title={speakingMessageId === message.id ? '停止朗读' : '朗读'}>
                {speakingMessageId === message.id ? <Square size={10} /> : <Volume2 size={10} />}
              </button>}
            </div>
            <ConversationMessageContent role={message.role} content={message.content} compact streaming={streamingMessage?.id === message.id} />
          </div>)}
          {isLoading && !streamingMessage && <p className="dh-companion-thinking">法小助正在整理…</p>}
        </div>
      </details>

      <ConversationComposer compact preset={preset} onPresetConsumed={() => setPreset(null)} focusSignal={focusSignal} />
      <p className="dh-companion-hint">完整事实、材料与审批请在中间工作区处理</p>
    </div>
  </aside>;
}
