'use client';

import { useEffect, useRef } from 'react';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';

import ConversationComposer from './ConversationComposer';
import ConversationPresenterCard from './ConversationPresenterCard';
import DigitalHumanAvatar from './DigitalHumanAvatar';

export default function DigitalHumanCompanion() {
  const messagesRef = useRef<HTMLDivElement>(null);
  const {
    emotion,
    isLoading,
    messages,
    workspaceError,
    workspaceLoading,
    workspacePresentation,
  } = useDigitalHumanStore();
  const recentMessages = messages.slice(-4);

  useEffect(() => {
    const container = messagesRef.current;
    if (container) container.scrollTop = container.scrollHeight;
  }, [recentMessages, isLoading]);

  return (
    <aside className="dh-companion" aria-label="案件工作台数字人陪伴">
      <div className="dh-companion-avatar">
        <DigitalHumanAvatar emotion={emotion} size="small" />
        <div><strong>法小助</strong><small>当前案件陪伴</small></div>
      </div>
      <ConversationPresenterCard
        presentation={workspacePresentation}
        isLoading={workspaceLoading}
        error={workspaceError}
      />
      <div ref={messagesRef} className="dh-companion-messages" aria-live="polite">
        {recentMessages.map((message) => (
          <div key={message.id} className={`dh-companion-message ${message.role}`}>
            <span>{message.role === 'assistant' ? '法小助' : '你'}</span>
            <p>{message.content}</p>
          </div>
        ))}
        {isLoading && <p className="dh-companion-thinking">法小助正在整理…</p>}
      </div>
      <ConversationComposer compact />
      <p className="dh-companion-hint">完整事实、材料和审批请在左侧工作台处理</p>
    </aside>
  );
}
