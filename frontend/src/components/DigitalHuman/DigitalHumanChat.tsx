'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ChevronDown, FileSearch, History, Minus, Plus, RotateCcw, Square, Trash2, Volume2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import { isTtsSupported } from '@/lib/voice/ttsController';
import { useVoiceReady } from '@/lib/voice/useVoiceReady';

import DigitalHumanAvatar, { EMOTION_LABELS } from './DigitalHumanAvatar';
import ConversationComposer from './ConversationComposer';
import ConversationMessageContent from './ConversationMessageContent';
import LaborTriageCard from './LaborTriageCard';
import MatterEntryCard from './MatterEntryCard';
import { useLaborTriage } from './useLaborTriage';

interface DigitalHumanChatProps {
  avatarVisible?: boolean;
}

export default function DigitalHumanChat({ avatarVisible = true }: DigitalHumanChatProps) {
  const [historyOpen, setHistoryOpen] = useState(false);
  const [caseEntryExpanded, setCaseEntryExpanded] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const laborTriage = useLaborTriage();
  const {
    close,
    currentMatterId,
    deleteSession,
    emotion,
    historyError,
    isLoading,
    messages,
    loadSession,
    openWorkspace,
    refreshHistory,
    setEmotion,
    sessions,
    sessionId,
    speakMessage,
    speakingMessageId,
    startNewConversation,
    stopSpeaking,
    streamFallbackNotice,
    streamingMessage,
    voiceSpeaking,
    workspaceOpen,
  } = useDigitalHumanStore();
  const voiceReady = useVoiceReady();
  const ttsSupported = voiceReady && isTtsSupported();

  useEffect(() => {
    const container = messagesRef.current;
    // 工作台打开时聊天列被 display:none 隐藏，此时 scrollHeight 为 0，
    // 若照常滚动会把 scrollTop 置 0；返回对话时依赖变化重新滚动到底部。
    if (container && !workspaceOpen) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, streamingMessage, isLoading, laborTriage.snapshot, laborTriage.agentRun, laborTriage.isLoading, workspaceOpen]);

  const handleRoute = (route: string) => {
    setEmotion('handoff');
    window.setTimeout(() => {
      router.push(route);
      close();
    }, 420);
  };

  return (
    <section className="dh-panel" role="dialog" aria-label="法小助数字人智能助手">
      <header className="dh-panel-header">
        <div>
          <div className="dh-title-row">
            <h2>法小助</h2>
            <span className="dh-online-dot" aria-label="在线" />
          </div>
          <p>{EMOTION_LABELS[emotion]}</p>
        </div>
        <div className="dh-header-actions">
          <button
            type="button"
            className="dh-workspace-switch"
            onClick={() => {
              // 聊天内只提供上下文转办；工作台的全局主入口位于顶栏。
              if (currentMatterId) openWorkspace();
              else setCaseEntryExpanded((open) => !open);
            }}
            aria-label={currentMatterId ? '继续案件办理' : '转入案件办理'}
            title={currentMatterId ? '继续案件办理' : '转入案件办理'}
          >
            <FileSearch size={16} />
            <span>{currentMatterId ? '继续办理' : '转入办理'}</span>
          </button>
          <button
            type="button"
            onClick={() => void refreshHistory()}
            aria-label="刷新会话记录"
            title="刷新记录"
          >
            <RotateCcw size={17} />
          </button>
          <button type="button" onClick={close} aria-label="收起法小助" title="收起">
            <Minus size={19} />
          </button>
        </div>
      </header>

      <div className="dh-history-section">
        <div className="dh-session-bar">
        <button
          type="button"
          className="dh-history-toggle"
          onClick={() => setHistoryOpen((open) => !open)}
          aria-expanded={historyOpen}
        >
          <History size={15} />
          <span>历史会话{sessions.length ? `（${sessions.length}）` : ''}</span>
          <ChevronDown size={15} className={historyOpen ? 'dh-chevron-open' : ''} />
        </button>
        <button
          type="button"
          onClick={() => {
            startNewConversation();
            setHistoryOpen(false);
          }}
          aria-label="开始新对话"
          title="新对话"
        >
          <Plus size={16} />
        </button>
        </div>

        {historyOpen && (
          <div className="dh-history-list" role="list" aria-label="历史会话列表">
          {historyError ? (
            <div className="dh-history-error">
              <span>{historyError}</span>
              <button type="button" onClick={() => void refreshHistory()}>重新读取</button>
            </div>
          ) : sessions.length === 0 ? (
            <p>暂无历史会话</p>
          ) : sessions.map((session) => (
            <div
              key={session.id}
              className={`dh-history-item ${session.id === sessionId ? 'dh-history-current' : ''}`}
              role="listitem"
            >
              <button
                type="button"
                className="dh-history-select"
                onClick={() => {
                  void loadSession(session.id);
                  setHistoryOpen(false);
                }}
              >
                <span>{session.title}</span>
                <small>{session.id === sessionId ? '当前会话' : '点击切换'}</small>
              </button>
              <button
                type="button"
                className="dh-history-delete"
                onClick={() => void deleteSession(session.id)}
                aria-label={`删除会话：${session.title}`}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          </div>
        )}
      </div>

      <div className="dh-panel-body">
      <div className="dh-chat-column">
      <div className="dh-portrait-stage">
        <DigitalHumanAvatar
          emotion={emotion}
          isLoading={isLoading}
          voiceSpeaking={voiceSpeaking}
          variant="portrait"
          visible={avatarVisible}
        />
      </div>

      <div ref={messagesRef} className="dh-messages" aria-live="polite">
        {messages.map((message) => (
          <div key={message.id} className={`dh-message-row dh-message-${message.role}`}>
            <div className="dh-message-bubble">
              <ConversationMessageContent
                role={message.role}
                content={message.content}
              />
              {message.role === 'assistant' && message.route && message.routeLabel && message.route !== '/chat' && (
                <button
                  type="button"
                  className="dh-route-button"
                  onClick={() => handleRoute(message.route as string)}
                >
                  打开{message.routeLabel}
                  <ArrowRight size={15} />
                </button>
              )}
              {message.role === 'assistant' && ttsSupported && (
                <button
                  type="button"
                  className={`dh-speak-button ${speakingMessageId === message.id ? 'dh-speak-button-active' : ''}`}
                  onClick={() => (
                    speakingMessageId === message.id
                      ? stopSpeaking()
                      : speakMessage(message.id, message.content)
                  )}
                  aria-label={speakingMessageId === message.id ? '停止朗读' : '朗读这条回复'}
                  title={speakingMessageId === message.id ? '停止朗读' : '朗读'}
                >
                  {speakingMessageId === message.id ? <Square size={13} /> : <Volume2 size={13} />}
                </button>
              )}
            </div>
          </div>
        ))}
        {streamingMessage && (
          <div className="dh-message-row dh-message-assistant">
            <div className="dh-message-bubble" aria-label="法小助正在输入">
              <ConversationMessageContent
                role="assistant"
                content={streamingMessage.content}
                streaming
              />
            </div>
          </div>
        )}
        {isLoading && !streamingMessage && (
          <div className="dh-message-row dh-message-assistant">
            <div className="dh-message-bubble dh-typing" aria-label="法小助正在输入">
              <span />
              <span />
              <span />
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
        {(currentMatterId || caseEntryExpanded) && (
          <MatterEntryCard expanded={caseEntryExpanded} />
        )}
      </div>

      {streamFallbackNotice && (
        <p className="dh-stream-fallback-hint">{streamFallbackNotice}</p>
      )}
      <ConversationComposer />
      <p className="dh-disclaimer">回答仅供参考，重要法律事项请咨询专业律师</p>
      </div>
      </div>
    </section>
  );
}
