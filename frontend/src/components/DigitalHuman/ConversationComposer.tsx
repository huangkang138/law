'use client';

import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Send, Square, Volume2, VolumeX } from 'lucide-react';

import { useDigitalHumanStore } from '@/store/digitalHumanStore';
import { isSttSupported, SttController } from '@/lib/voice/sttController';
import { isTtsSupported } from '@/lib/voice/ttsController';
import { useVoiceReady } from '@/lib/voice/useVoiceReady';

interface ConversationComposerProps {
  compact?: boolean;
  // 外部预填问题（如助手快捷操作）：只填入输入框，发送前仍由用户确认。
  preset?: string | null;
  onPresetConsumed?: () => void;
  // 外部聚焦请求（如"继续提问"）：变化时聚焦输入框。
  focusSignal?: number;
}

export default function ConversationComposer({
  compact = false,
  preset = null,
  onPresetConsumed,
  focusSignal = 0,
}: ConversationComposerProps) {
  const [question, setQuestion] = useState('');
  const [sttActive, setSttActive] = useState(false);
  const [sttError, setSttError] = useState('');
  const sttControllerRef = useRef<SttController | null>(null);
  const sttBaseRef = useRef('');
  const sttInterimRef = useRef('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (preset) {
      setQuestion(preset);
      onPresetConsumed?.();
      textareaRef.current?.focus();
    }
  }, [preset, onPresetConsumed]);

  useEffect(() => {
    if (focusSignal > 0) textareaRef.current?.focus();
  }, [focusSignal]);
  const {
    cancelRequest,
    isLoading,
    sendMessage,
    stopSpeaking,
    toggleVoice,
    voiceEnabled,
  } = useDigitalHumanStore();
  const voiceReady = useVoiceReady();

  useEffect(() => () => sttControllerRef.current?.abort(), []);

  // 不支持语音的浏览器：按钮不渲染，文字聊天完全不受影响（水合后判定）。
  const sttSupported = voiceReady && isSttSupported();
  const ttsSupported = voiceReady && isTtsSupported();

  const finishStt = (): string => {
    sttControllerRef.current?.stop();
    sttControllerRef.current = null;
    // 停止时把最后一段中间结果并入，已确认文本不丢。
    const text = (sttBaseRef.current + sttInterimRef.current).trim();
    sttBaseRef.current = '';
    sttInterimRef.current = '';
    setSttActive(false);
    return text;
  };

  const startStt = () => {
    stopSpeaking(); // 说话打断旧朗读
    setSttError('');
    sttBaseRef.current = question;
    sttInterimRef.current = '';
    const controller = new SttController();
    sttControllerRef.current = controller;
    controller.start({
      onFinal: (transcript) => {
        sttBaseRef.current += transcript;
        setQuestion(sttBaseRef.current + sttInterimRef.current);
      },
      onInterim: (transcript) => {
        sttInterimRef.current = transcript;
        setQuestion(sttBaseRef.current + transcript);
      },
      onError: (message) => {
        setSttError(message);
        sttControllerRef.current = null;
        setQuestion(sttBaseRef.current);
        sttBaseRef.current = '';
        sttInterimRef.current = '';
        setSttActive(false);
      },
    });
    setSttActive(true);
  };

  const toggleStt = () => {
    if (sttActive) {
      setQuestion(finishStt());
      return;
    }
    startStt();
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    // 识别中点击发送：先停识别、并入已确认文本，再走正常发送（转写文本须用户确认）。
    const value = (sttActive ? finishStt() : question).trim();
    if (sttActive) setQuestion(value);
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
    <>
      <form
        className={`dh-composer ${compact ? 'dh-companion-composer' : ''}`}
        onSubmit={submit}
      >
        <textarea
          ref={textareaRef}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={compact ? '围绕当前案件继续提问…' : '告诉法小助，你想解决什么问题…'}
          rows={1}
          maxLength={1000}
          disabled={isLoading}
          aria-label="输入问题"
        />
        {sttSupported && (
          <button
            type="button"
            className={`dh-mic-button ${sttActive ? 'dh-mic-button-active' : ''}`}
            onClick={toggleStt}
            disabled={isLoading}
            aria-label={sttActive ? '停止语音输入' : '语音输入'}
            title={sttActive ? '停止语音输入' : '语音输入'}
          >
            {sttActive ? <MicOff size={17} /> : <Mic size={17} />}
          </button>
        )}
        {ttsSupported && (
          <button
            type="button"
            className={`dh-voice-toggle ${voiceEnabled ? 'dh-voice-toggle-on' : ''}`}
            onClick={toggleVoice}
            aria-label={voiceEnabled ? '关闭自动朗读新回复' : '开启自动朗读新回复'}
            title={voiceEnabled ? '关闭自动朗读' : '自动朗读新回复'}
          >
            {voiceEnabled ? <Volume2 size={17} /> : <VolumeX size={17} />}
          </button>
        )}
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
      {sttError && <p className="dh-stt-error-hint">{sttError}</p>}
    </>
  );
}
