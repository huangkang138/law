'use client';

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { ArrowRight, ChevronDown, History, Maximize2, Minimize2, Minus, Plus, RotateCcw, Send, Square, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import DigitalHumanAvatar, { EMOTION_LABELS } from './DigitalHumanAvatar';
import LaborTriageCard from './LaborTriageCard';
import DigitalHumanMatterWorkspace from './DigitalHumanMatterWorkspace';
import { isLaborQuestion, useLaborTriage } from './useLaborTriage';

export default function DigitalHumanChat() {
  const [question, setQuestion] = useState('');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [workspaceExpanded, setWorkspaceExpanded] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const laborTriage = useLaborTriage();
  const {
    close,
    cancelRequest,
    deleteSession,
    emotion,
    historyError,
    isLoading,
    messages,
    loadSession,
    refreshHistory,
    sendMessage,
    setEmotion,
    sessions,
    sessionId,
    startNewConversation,
  } = useDigitalHumanStore();

  useEffect(() => {
    const container = messagesRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isLoading, laborTriage.snapshot, laborTriage.isLoading]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const value = question.trim();
    if (!value || isLoading) return;
    setQuestion('');
    await sendMessage(value);
    if (isLaborQuestion(value)) await laborTriage.start(value);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  const handleRoute = (route: string) => {
    setEmotion('handoff');
    window.setTimeout(() => {
      router.push(route);
      close();
    }, 420);
  };

  return (
    <section className={`dh-panel ${workspaceExpanded ? 'dh-panel-expanded' : ''}`} role="dialog" aria-label="法小助数字人智能助手">
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
            onClick={() => setWorkspaceExpanded((value) => !value)}
            aria-label={workspaceExpanded ? '收起案件工作台' : '展开案件工作台'}
            title={workspaceExpanded ? '收起工作台' : '展开工作台'}
          >
            {workspaceExpanded ? <Minimize2 size={17} /> : <Maximize2 size={17} />}
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
            laborTriage.reset();
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
                  laborTriage.reset();
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
        <div className="dh-portrait-halo" aria-hidden="true" />
        <DigitalHumanAvatar emotion={emotion} />
      </div>

      <div ref={messagesRef} className="dh-messages" aria-live="polite">
        {messages.map((message) => (
          <div key={message.id} className={`dh-message-row dh-message-${message.role}`}>
            <div className="dh-message-bubble">
              <p>{message.content}</p>
              {message.role === 'assistant' && message.route && message.routeLabel && (
                <button
                  type="button"
                  className="dh-route-button"
                  onClick={() => handleRoute(message.route as string)}
                >
                  去{message.routeLabel}看看
                  <ArrowRight size={15} />
                </button>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
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
          isLoading={laborTriage.isLoading}
          error={laborTriage.error}
          onSubmit={laborTriage.submitFacts}
          onRetry={laborTriage.retry}
        />
      </div>

      <form className="dh-composer" onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="告诉法小助，你想解决什么问题…"
          rows={1}
          maxLength={1000}
          disabled={isLoading}
          aria-label="输入问题"
        />
        {isLoading ? (
          <button type="button" className="dh-send-button" onClick={cancelRequest} aria-label="停止等待">
            <Square size={15} />
          </button>
        ) : <button
          type="submit"
          className="dh-send-button"
          disabled={!question.trim() || isLoading}
          aria-label="发送问题"
        >
          <Send size={18} />
        </button>}
      </form>
      <p className="dh-disclaimer">回答仅供参考，重要法律事项请咨询专业律师</p>
      </div>
      <div className="dh-workspace-column">
        <DigitalHumanMatterWorkspace expanded={workspaceExpanded} onExpand={() => setWorkspaceExpanded(true)} />
      </div>
      </div>
    </section>
  );
}
