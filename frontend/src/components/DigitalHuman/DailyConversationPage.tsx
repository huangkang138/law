'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { ArrowRight, Check, Copy, FilePenLine, FileText, Gavel, History, Lightbulb, MessageCircle, Plus, RotateCcw, Settings, Square, Trash2, UserRound, Volume2 } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';

import lawAssistantHead from '../../../digital-human/law_xiaozhi/head_reference.png';

import { isTtsSupported } from '@/lib/voice/ttsController';
import { useVoiceReady } from '@/lib/voice/useVoiceReady';
import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import ConversationComposer from './ConversationComposer';
import ConversationMessageContent from './ConversationMessageContent';
import DigitalHumanAvatar, { EMOTION_LABELS } from './DigitalHumanAvatar';
import LaborTriageCard from './LaborTriageCard';
import MatterEntryCard from './MatterEntryCard';
import DailyConversationContextPanel from './DailyConversationContextPanel';
import { useLaborTriage } from './useLaborTriage';
import styles from './DailyConversationPage.module.css';

const QUICK_PROMPT_GROUPS = [
  ['试用期被辞退怎么办', '拖欠工资怎么维权', '劳动合同解除赔偿', '竞业限制是否有效'],
  ['租房押金不退怎么办', '交通事故责任如何认定', '合同违约怎么处理', '欠款不还如何起诉'],
] as const;

const HERO_ACTIONS = [
  {
    label: '法律咨询',
    description: '先说说你的情况',
    icon: MessageCircle,
    tone: 'blue',
    preset: '请帮我分析一下我的法律问题',
    route: undefined,
  },
  {
    label: '合同审查',
    description: '进入合同审查',
    icon: FileText,
    tone: 'teal',
    route: '/contract',
    preset: undefined,
  },
  {
    label: '案件与纠纷',
    description: '先判断处理方式',
    icon: Gavel,
    tone: 'violet',
    preset: '我遇到劳动争议，想先了解该怎么处理',
    route: undefined,
  },
  {
    label: '文书起草',
    description: '进入文书起草',
    icon: FilePenLine,
    tone: 'orange',
    route: '/document-drafting',
    preset: undefined,
  },
] as const;

function formatSessionDate(value: string | null): string {
  if (!value) return '刚刚';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '刚刚';
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' });
}

function formatMessageTime(value: number): string {
  if (!value) return '刚刚';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '刚刚';
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

export default function DailyConversationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const messagesRef = useRef<HTMLDivElement>(null);
  const routeTimerRef = useRef<number | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [preset, setPreset] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [quickPromptGroup, setQuickPromptGroup] = useState(0);
  const voiceReady = useVoiceReady();
  const ttsSupported = voiceReady && isTtsSupported();
  const laborTriage = useLaborTriage();

  const {
    currentMatterId,
    deleteSession,
    emotion,
    historyError,
    isLoading,
    loadSession,
    loadSessions,
    messages,
    open,
    refreshHistory,
    sessionId,
    sessions,
    speakingMessageId,
    speakMessage,
    startNewConversation,
    stopSpeaking,
    streamFallbackNotice,
    streamingMessage,
    voiceSpeaking,
    openWorkspace,
  } = useDigitalHumanStore();

  useEffect(() => {
    const targetSessionId = searchParams.get('sessionId');
    let active = true;

    if (targetSessionId) {
      void (async () => {
        await loadSessions();
        if (active) await loadSession(targetSessionId);
      })();
    } else {
  // open() 保留数字人 Store 的既有会话恢复语义；本页常态隐藏悬浮入口，
  // 进入案件工作台时由 Float 恢复工作台壳。
      open();
    }

    return () => {
      active = false;
      if (routeTimerRef.current !== null) window.clearTimeout(routeTimerRef.current);
    };
  }, [loadSession, loadSessions, open, searchParams]);

  useEffect(() => {
    const container = messagesRef.current;
    if (!container) return;
    const frame = window.requestAnimationFrame(() => {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: streamingMessage ? 'auto' : 'smooth',
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [isLoading, messages, laborTriage.agentRun, laborTriage.isLoading, laborTriage.snapshot, streamingMessage]);

  const latestAssistantId = useMemo(
    () => [...messages].reverse().find((message) => message.role === 'assistant')?.id || null,
    [messages],
  );

  const statusLabel = isListening
    ? '正在聆听'
    : isLoading
      ? '正在思考'
      : voiceSpeaking
        ? '正在回答'
        : EMOTION_LABELS[emotion];

  const handleRoute = (route: string) => {
    routeTimerRef.current = window.setTimeout(() => {
      router.push(route);
    }, 260);
  };

  const handleCopy = useCallback(async (messageId: string, content: string) => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(content);
      } else {
        const helper = document.createElement('textarea');
        helper.value = content;
        helper.setAttribute('readonly', 'true');
        helper.style.position = 'fixed';
        helper.style.opacity = '0';
        document.body.appendChild(helper);
        helper.select();
        document.execCommand('copy');
        document.body.removeChild(helper);
      }
      setCopiedMessageId(messageId);
      window.setTimeout(() => setCopiedMessageId((current) => current === messageId ? null : current), 1600);
    } catch {
      setCopiedMessageId(null);
    }
  }, []);

  const handlePreset = useCallback((question: string) => {
    setPreset(question);
  }, []);

  return (
    <div className={styles.page}>
      <div className={styles.ambientGlow} aria-hidden="true" />
      <div className={styles.ambientLine} aria-hidden="true" />

      <aside className={styles.sidebar} aria-label="法小助会话记录">
        <div className={styles.sidebarHeader}>
          <div>
            <span className={styles.eyebrow}>DIGITAL HUMAN</span>
            <h2>会话记录</h2>
          </div>
          <button
            type="button"
            className={styles.newButton}
            onClick={startNewConversation}
            aria-label="新建数字人会话"
            title="新建会话"
          >
            <Plus size={18} />
          </button>
        </div>

        <div className={styles.sidebarTools}>
          <span><MessageCircle size={14} /> 法小助日常交流</span>
          <button type="button" onClick={() => void refreshHistory()} aria-label="刷新数字人会话记录" title="刷新记录">
            <RotateCcw size={14} />
          </button>
        </div>

        <div className={styles.sessionList} role="list" aria-label="数字人历史会话">
          {historyError && (
            <div className={styles.historyError}>
              <span>{historyError}</span>
              <button type="button" onClick={() => void refreshHistory()}>重试</button>
            </div>
          )}
          {sessions.map((session) => (
            <div key={session.id} className={`${styles.sessionItem} ${session.id === sessionId ? styles.sessionItemActive : ''}`} role="listitem">
              <button type="button" className={styles.sessionButton} onClick={() => void loadSession(session.id)}>
                <span className={styles.sessionIcon}><History size={15} /></span>
                <span className={styles.sessionCopy}>
                  <strong>{session.title || '新对话'}</strong>
                  <small>{formatSessionDate(session.updated_at)}</small>
                </span>
              </button>
              <button
                type="button"
                className={styles.deleteButton}
                onClick={() => void deleteSession(session.id)}
                aria-label={`删除会话：${session.title || '新对话'}`}
                title="删除会话"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {!historyError && sessions.length === 0 && (
            <div className={styles.emptyHistory}>
              <History size={22} />
              <p>暂无历史会话</p>
              <small>发送第一条消息后会自动保存</small>
            </div>
          )}
        </div>

        <div className={styles.sidebarFooter}>
          <Link href="/settings"><Settings size={16} /> 设置</Link>
        </div>
      </aside>

      <main className={styles.main}>
        <section className={styles.hero} aria-labelledby="daily-conversation-title">
          <div className={styles.heroCopy}>
            <span className={styles.heroKicker}>法律问题，从这里开始</span>
            <h1 id="daily-conversation-title">法小助</h1>
            <p>您的智能法律助手</p>
            <div className={styles.heroMeta}>
              <span className={styles.onlineStatus}><i /> 在线 · 随时为你服务</span>
            </div>
            <div className={styles.heroHint}>
              不知道该去哪个功能？先告诉我你的情况。
            </div>
          </div>
          <div className={styles.avatarStage} aria-label={`法小助：${statusLabel}`}>
            <div className={styles.avatarBubble} aria-hidden="true">
              您好！我是法小助<br />有法律问题，随时问我～
            </div>
            <div className={styles.avatarHalo} aria-hidden="true" />
            <DigitalHumanAvatar
              emotion={emotion}
              state={isListening ? 'listening' : undefined}
              isLoading={isLoading}
              voiceSpeaking={voiceSpeaking}
              useLegacyImageFallback={false}
              variant="portrait"
              visible
            />
          </div>
          <div className={styles.heroActions} aria-label="法小助功能入口">
            {HERO_ACTIONS.map((action) => {
              const Icon = action.icon;
              return (
                <button
                  type="button"
                  key={action.label}
                  className={styles.heroAction}
                  data-tone={action.tone}
                  onClick={() => action.route ? handleRoute(action.route) : handlePreset(action.preset)}
                >
                  <span className={styles.heroActionIcon}><Icon size={17} /></span>
                  <span className={styles.heroActionCopy}>
                    <strong>{action.label}</strong>
                    <small>{action.description}</small>
                  </span>
                  <ArrowRight size={14} className={styles.heroActionArrow} />
                </button>
              );
            })}
          </div>
        </section>

        <section ref={messagesRef} className={styles.conversation} aria-label="法小助多轮对话" aria-live="polite">
          <div className={styles.conversationInner}>
            {messages.map((message) => {
              const isLatestAssistant = message.id === latestAssistantId && message.role === 'assistant';
              const canRoute = message.role === 'assistant' && message.route && message.routeLabel && message.route !== '/chat';
              const isSpeaking = speakingMessageId === message.id && voiceSpeaking;
              return (
                <article key={message.id} className={`${styles.messageRow} ${message.role === 'user' ? styles.userRow : styles.assistantRow}`}>
                  {message.role === 'assistant' && (
                    <div className={`${styles.messageAvatar} ${styles.assistantAvatar}`} aria-label="法小助头像">
                      <Image src={lawAssistantHead} alt="" aria-hidden="true" className={styles.assistantAvatarImage} />
                    </div>
                  )}
                  <div className={message.role === 'assistant' ? styles.assistantMessageBody : styles.userMessageBody}>
                    <div className={`${styles.messageCard} ${message.role === 'assistant' ? styles.assistantCard : styles.userCard}`}>
                      {message.role === 'assistant' && (
                        <div className={styles.messageHeader}>
                          <strong>法小助</strong>
                          <time dateTime={new Date(message.createdAt).toISOString()}>{formatMessageTime(message.createdAt)}</time>
                          {isLatestAssistant && <span className={styles.latestLabel}>最新回答</span>}
                        </div>
                      )}
                      <ConversationMessageContent role={message.role} content={message.content} />
                      {canRoute && (
                        <button type="button" className={styles.routeButton} onClick={() => handleRoute(message.route as string)}>
                          打开{message.routeLabel}
                          <ArrowRight size={15} />
                        </button>
                      )}
                      {message.role === 'assistant' && (
                        <div className={styles.messageActions}>
                          {ttsSupported && (
                            <button type="button" onClick={() => isSpeaking ? stopSpeaking() : speakMessage(message.id, message.content)}>
                              {isSpeaking ? <Square size={13} /> : <Volume2 size={13} />}
                              {isSpeaking ? '停止朗读' : '朗读'}
                            </button>
                          )}
                          <button type="button" onClick={() => void handleCopy(message.id, message.content)}>
                            {copiedMessageId === message.id ? <Check size={13} /> : <Copy size={13} />}
                            {copiedMessageId === message.id ? '已复制' : '复制'}
                          </button>
                        </div>
                      )}
                    </div>
                    {message.role === 'user' && (
                      <time className={styles.userMessageTime} dateTime={new Date(message.createdAt).toISOString()}>
                        {formatMessageTime(message.createdAt)}
                      </time>
                    )}
                  </div>
                  {message.role === 'user' && (
                    <div className={`${styles.messageAvatar} ${styles.userAvatar}`} aria-label="用户头像">
                      <UserRound size={21} aria-hidden="true" />
                    </div>
                  )}
                </article>
              );
            })}

            {streamingMessage && (
              <article className={`${styles.messageRow} ${styles.assistantRow}`}>
                <div className={`${styles.messageAvatar} ${styles.assistantAvatar}`} aria-label="法小助头像">
                  <Image src={lawAssistantHead} alt="" aria-hidden="true" className={styles.assistantAvatarImage} />
                </div>
                <div className={styles.assistantMessageBody}>
                  <div className={`${styles.messageCard} ${styles.assistantCard} ${styles.latestCard}`} aria-label="法小助正在回答">
                    <div className={styles.messageHeader}><strong>法小助</strong><time>现在</time><span className={styles.latestLabel}>实时回答</span></div>
                    <ConversationMessageContent role="assistant" content={streamingMessage.content} streaming />
                  </div>
                </div>
              </article>
            )}
            {isLoading && !streamingMessage && (
              <div className={`${styles.messageRow} ${styles.assistantRow}`} aria-label="法小助正在思考">
                <div className={`${styles.messageAvatar} ${styles.assistantAvatar}`}>
                  <Image src={lawAssistantHead} alt="" aria-hidden="true" className={styles.assistantAvatarImage} />
                </div>
                <div className={styles.assistantMessageBody}>
                  <div className={`${styles.messageCard} ${styles.assistantCard} ${styles.typingCard}`}>
                    <span /><span /><span /><em>法小助正在思考…</em>
                  </div>
                </div>
              </div>
            )}

            <LaborTriageCard
              snapshot={laborTriage.snapshot}
              agentRun={laborTriage.agentRun}
              isLoading={laborTriage.isLoading}
              error={laborTriage.error}
              onSubmit={laborTriage.submitFacts}
              onRetry={laborTriage.retry}
            />
            {currentMatterId && <MatterEntryCard expanded={false} />}
            {streamFallbackNotice && <p className={styles.streamNotice}>{streamFallbackNotice}</p>}
          </div>
        </section>

        <section className={styles.composerArea} aria-label="继续提问">
          <div className={styles.quickHeader}>
            <span className={styles.quickTitle}><Lightbulb size={14} />你也可以这样问</span>
            <div className={styles.quickHeaderActions}>
              <small>点击后可修改，确认后再发送</small>
              <button type="button" className={styles.quickRefresh} onClick={() => setQuickPromptGroup((group) => (group + 1) % QUICK_PROMPT_GROUPS.length)}>
                <RotateCcw size={12} />换一批
              </button>
            </div>
          </div>
          <div className={styles.quickPrompts}>
            {QUICK_PROMPT_GROUPS[quickPromptGroup].map((question) => (
              <button type="button" key={question} onClick={() => handlePreset(question)}>
                <FileText size={14} />
                {question}
              </button>
            ))}
          </div>
          <ConversationComposer
            preset={preset}
            onPresetConsumed={() => setPreset(null)}
            onListeningChange={setIsListening}
          />
          <p className={styles.disclaimer}>法小助提供 AI 辅助信息，重要法律事项请结合具体材料并咨询专业人士。</p>
        </section>
      </main>

      <DailyConversationContextPanel
        statusLabel={statusLabel}
        onOpenWorkspace={openWorkspace}
      />
    </div>
  );
}
