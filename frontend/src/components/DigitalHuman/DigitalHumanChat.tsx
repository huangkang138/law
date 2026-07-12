'use client';

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { ArrowRight, Bot, Check, ChevronDown, History, Minus, Plus, RotateCcw, Send, Square, Trash2, X } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import DigitalHumanAvatar, { EMOTION_LABELS } from './DigitalHumanAvatar';

export default function DigitalHumanChat() {
  const [question, setQuestion] = useState('');
  const [historyOpen, setHistoryOpen] = useState(false);
  const messagesRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const {
    close,
    cancelRequest,
    deleteSession,
    emotion,
    isLoading,
    messages,
    loadSession,
    refreshHistory,
    sendMessage,
    setEmotion,
    sessions,
    sessionId,
    startNewConversation,
    agentRun,
    isAgentLoading,
    startAgentDemo,
    decideAgentApproval,
    cancelAgentRun,
  } = useDigitalHumanStore();

  useEffect(() => {
    const container = messagesRef.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const value = question.trim();
    if (!value || isLoading) return;
    setQuestion('');
    await sendMessage(value);
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
          {sessions.length === 0 ? (
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
      </div>

      <div className="dh-agent-card">
        {/* 阶段 1 最小任务卡片：用于观察步骤、审批和最终结果。 */}
        {!agentRun ? (
          <button
            type="button"
            className="dh-agent-start"
            disabled={isAgentLoading}
            onClick={() => void startAgentDemo('整理一起模拟劳动争议并生成案件摘要')}
          >
            <Bot size={16} />{isAgentLoading ? '正在建立任务…' : '体验 Agent 模拟任务'}
          </button>
        ) : (
          <>
            <div className="dh-agent-card-title">
              <span><Bot size={15} />任务状态：{agentRun.status}</span>
              {!['completed', 'cancelled', 'failed'].includes(agentRun.status) && (
                <button type="button" onClick={() => void cancelAgentRun()} aria-label="取消 Agent 任务"><X size={14} /></button>
              )}
            </div>
            {agentRun.steps.map((step) => <p key={step.id}>• {step.name}：{step.status}</p>)}
            {agentRun.approval?.status === 'pending' && (
              <div className="dh-agent-approval">
                <p>{agentRun.approval.prompt}</p>
                <div>
                  <button type="button" disabled={isAgentLoading} onClick={() => void decideAgentApproval(true)}><Check size={14} />确认继续</button>
                  <button type="button" disabled={isAgentLoading} onClick={() => void decideAgentApproval(false)}><X size={14} />拒绝</button>
                </div>
              </div>
            )}
            {agentRun.final_output?.summary && agentRun.status === 'completed' && <p className="dh-agent-result">{agentRun.final_output.summary}</p>}
          </>
        )}
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
    </section>
  );
}
