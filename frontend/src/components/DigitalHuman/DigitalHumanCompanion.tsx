'use client';

import { useEffect, useRef } from 'react';
import { Square, Volume2 } from 'lucide-react';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import { isTtsSupported } from '@/lib/voice/ttsController';
import { useVoiceReady } from '@/lib/voice/useVoiceReady';

import ConversationComposer from './ConversationComposer';
import ConversationMessageContent from './ConversationMessageContent';
import ConversationPresenterCard from './ConversationPresenterCard';
import DigitalHumanAvatar from './DigitalHumanAvatar';

export default function DigitalHumanCompanion() {
  const messagesRef = useRef<HTMLDivElement>(null);
  const {
    emotion,
    isLoading,
    messages,
    speakMessage,
    speakingMessageId,
    stopSpeaking,
    streamingMessage,
    voiceSpeaking,
    workspaceError,
    workspaceLoading,
    workspacePresentation,
  } = useDigitalHumanStore();
  const voiceReady = useVoiceReady();
  const ttsSupported = voiceReady && isTtsSupported();
  const recentMessages = [
    ...messages,
    ...(streamingMessage ? [streamingMessage] : []),
  ].slice(-4);

  useEffect(() => {
    const container = messagesRef.current;
    if (container) container.scrollTop = container.scrollHeight;
  }, [recentMessages, isLoading]);

  return (
    <aside className="dh-companion" aria-label="案件工作台数字人陪伴">
      <div className="dh-companion-avatar">
        <DigitalHumanAvatar emotion={voiceSpeaking ? 'talk_normal' : emotion} size="small" />
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
            <div className="dh-companion-message-head">
              <span>{message.role === 'assistant' ? '法小助' : '你'}</span>
              {message.role === 'assistant'
                && streamingMessage?.id !== message.id
                && ttsSupported && (
                <button
                  type="button"
                  className={`dh-companion-speak ${speakingMessageId === message.id ? 'dh-companion-speak-active' : ''}`}
                  onClick={() => (
                    speakingMessageId === message.id
                      ? stopSpeaking()
                      : speakMessage(message.id, message.content)
                  )}
                  aria-label={speakingMessageId === message.id ? '停止朗读' : '朗读这条回复'}
                  title={speakingMessageId === message.id ? '停止朗读' : '朗读'}
                >
                  {speakingMessageId === message.id ? <Square size={10} /> : <Volume2 size={10} />}
                </button>
              )}
            </div>
            <ConversationMessageContent
              role={message.role}
              content={message.content}
              compact
              streaming={streamingMessage?.id === message.id}
            />
          </div>
        ))}
        {isLoading && !streamingMessage && (
          <p className="dh-companion-thinking">法小助正在整理…</p>
        )}
      </div>
      <ConversationComposer compact />
      <p className="dh-companion-hint">完整事实、材料和审批请在左侧工作台处理</p>
    </aside>
  );
}
