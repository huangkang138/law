'use client';

// 浏览器语音转文字控制器（Web Speech SpeechRecognition）。
// 从 VoiceCourtroom.tsx 提取为独立轻量模块：连续中文识别、中间结果预览、
// 结束后自动重启（Chrome 连续识别约 60s 自动结束）、权限/网络错误降级回调。

export interface SttCallbacks {
  onFinal: (transcript: string) => void;
  onInterim: (transcript: string) => void;
  onError: (message: string) => void;
}

type RecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: unknown) => void) | null;
  onerror: ((event: unknown) => void) | null;
  onend: (() => void) | null;
};

export function isSttSupported(): boolean {
  if (typeof window === 'undefined') return false;
  const win = window as unknown as {
    SpeechRecognition?: unknown;
    webkitSpeechRecognition?: unknown;
  };
  return Boolean(win.SpeechRecognition || win.webkitSpeechRecognition);
}

export class SttController {
  private recognition: RecognitionLike | null = null;
  private recording = false;
  private callbacks: SttCallbacks | null = null;
  private lastFinalIndex = -1;

  get isRecording(): boolean {
    return this.recording;
  }

  start(callbacks: SttCallbacks): void {
    if (this.recording) return;
    if (!isSttSupported()) {
      callbacks.onError('当前浏览器不支持语音识别');
      return;
    }
    const win = window as unknown as {
      SpeechRecognition?: new () => RecognitionLike;
      webkitSpeechRecognition?: new () => RecognitionLike;
    };
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      callbacks.onError('当前浏览器不支持语音识别');
      return;
    }
    this.callbacks = callbacks;
    this.recording = true;
    this.lastFinalIndex = -1;
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'zh-CN';
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => this.handleResult(event);
    recognition.onerror = (event) => this.handleError(event);
    recognition.onend = () => {
      // Chrome 连续识别约 60s 自动结束；仍在录音时重启（VoiceCourtroom 已验证）。
      if (this.recording && this.recognition === recognition) {
        // 重启后是全新识别会话，结果下标从 0 重新开始，去重游标必须复位。
        this.lastFinalIndex = -1;
        try {
          recognition.start();
        } catch {
          // 重启失败（如页面隐藏）静默等待，用户可再次点击麦克风。
        }
      }
    };
    this.recognition = recognition;
    try {
      recognition.start();
    } catch {
      this.recording = false;
      this.recognition = null;
      callbacks.onError('语音识别启动失败，请重试');
    }
  }

  stop(): void {
    this.recording = false;
    this.recognition?.stop();
    this.recognition = null;
  }

  abort(): void {
    this.recording = false;
    this.recognition?.abort();
    this.recognition = null;
  }

  private handleResult(event: unknown): void {
    if (!this.callbacks) return;
    const resultEvent = event as {
      resultIndex: number;
      results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }>;
    };
    let final = '';
    let interim = '';
    for (let i = resultEvent.resultIndex; i < resultEvent.results.length; i += 1) {
      const result = resultEvent.results[i];
      const transcript = result[0]?.transcript || '';
      if (result.isFinal) {
        // 停止录音时 Chrome 会重放已确认的最终结果；按结果下标去重，
        // 同一段话只上报一次，避免"我要仲裁我要仲裁"式重复。
        if (i <= this.lastFinalIndex) continue;
        this.lastFinalIndex = i;
        final += transcript;
      } else {
        interim += transcript;
      }
    }
    if (final) this.callbacks.onFinal(final);
    // 中间结果始终上报（空值表示清空），让调用方清掉已固化的预览。
    this.callbacks.onInterim(interim);
  }

  private handleError(event: unknown): void {
    const error = (event as { error?: string })?.error || 'unknown';
    if (error === 'aborted' || error === 'no-speech') return; // 主动停止/未检测到语音：不打扰
    if (error === 'not-allowed') {
      this.recording = false;
      this.recognition = null;
      this.callbacks?.onError('未获得麦克风权限，请在浏览器设置中允许后重试');
      return;
    }
    if (error === 'network') {
      this.recording = false;
      this.recognition = null;
      this.callbacks?.onError('语音识别暂不可用，请检查网络后重试');
      return;
    }
    // 其他识别错误：停止本次识别并轻量提示，不影响文字输入。
    this.recording = false;
    this.recognition = null;
    this.callbacks?.onError('语音识别暂不可用，请稍后重试');
  }
}
