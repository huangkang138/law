'use client';

import { FormEvent, KeyboardEvent, useState } from 'react';
import { Send, Square } from 'lucide-react';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

interface ConversationComposerProps {
  compact?: boolean;
}

export default function ConversationComposer({ compact = false }: ConversationComposerProps) {
  const [question, setQuestion] = useState('');
  const { cancelRequest, isLoading, sendMessage } = useDigitalHumanStore();

  const submit = async (event: FormEvent) => {
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

  return (
    <form
      className={`dh-composer ${compact ? 'dh-companion-composer' : ''}`}
      onSubmit={submit}
    >
      <textarea
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={compact ? '围绕当前案件继续提问…' : '告诉法小助，你想解决什么问题…'}
        rows={1}
        maxLength={1000}
        disabled={isLoading}
        aria-label="输入问题"
      />
      {isLoading ? (
        <button
          type="button"
          className="dh-send-button"
          onClick={cancelRequest}
          aria-label="停止等待"
        >
          <Square size={15} />
        </button>
      ) : (
        <button
          type="submit"
          className="dh-send-button"
          disabled={!question.trim()}
          aria-label="发送问题"
        >
          <Send size={18} />
        </button>
      )}
    </form>
  );
}
