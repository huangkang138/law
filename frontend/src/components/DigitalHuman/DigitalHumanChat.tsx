'use client';

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { ArrowRight, Minus, RotateCcw, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import DigitalHumanAvatar, { EMOTION_LABELS } from './DigitalHumanAvatar';

export default function DigitalHumanChat() {
  const [question, setQuestion] = useState('');
  const messagesRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const {
    close,
    emotion,
    isLoading,
    messages,
    reset,
    sendMessage,
    setEmotion,
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
          <button type="button" onClick={() => void reset()} aria-label="重新开始对话" title="重新开始">
            <RotateCcw size={17} />
          </button>
          <button type="button" onClick={close} aria-label="收起法小助" title="收起">
            <Minus size={19} />
          </button>
        </div>
      </header>

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
        <button
          type="submit"
          className="dh-send-button"
          disabled={!question.trim() || isLoading}
          aria-label="发送问题"
        >
          <Send size={18} />
        </button>
      </form>
      <p className="dh-disclaimer">回答仅供参考，重要法律事项请咨询专业律师</p>
    </section>
  );
}
