'use client';

// 连续音频队列播放器（Phase 1 语音主链路）。
//
// 统一管理：当前音频、待播放队列、播放状态与 requestId 隔离。
// - 一次只播一条，严格按 enqueue 顺序（seq 由后端保证递增）；
// - 新请求 setRequest 立即清空旧队列并停止在播音频，迟到旧请求片段直接丢弃；
// - 单条播放出错跳过继续下一条，不卡死整个队列；
// - primary（后端神经 TTS 音频）与 fallback（浏览器 speechSynthesis）
//   在事件中明确区分（ttsMode 字段），不静默混用。

import { ttsController } from '@/lib/voice/ttsController';

export type AudioPlayerState =
  | 'IDLE'
  | 'BUFFERING'
  | 'PLAYING'
  | 'PAUSED'
  | 'STOPPED'
  | 'ERROR';

export type VoiceTtsMode = 'primary' | 'fallback';

export interface VoiceChunk {
  seq: number;
  requestId: string;
  text: string;
  audioDataUrl?: string | null;
  ttsMode: VoiceTtsMode;
}

export interface StreamingAudioPlayerCallbacks {
  onSpeechStart?: (chunk: VoiceChunk) => void;
  onSpeechEnd?: (chunk: VoiceChunk) => void;
  onSpeechPause?: () => void;
  onSpeechResume?: () => void;
  onSpeechCancelled?: () => void;
  onStateChange?: (state: AudioPlayerState) => void;
  onChunkError?: (chunk: VoiceChunk) => void;
}

export class StreamingAudioPlayer {
  private queue: VoiceChunk[] = [];
  private current: VoiceChunk | null = null;
  private state: AudioPlayerState = 'IDLE';
  private requestId: string | null = null;
  private audioEl: HTMLAudioElement | null = null;
  private callbacks: StreamingAudioPlayerCallbacks;

  constructor(callbacks: StreamingAudioPlayerCallbacks = {}) {
    this.callbacks = callbacks;
  }

  get currentRequestId(): string | null {
    return this.requestId;
  }

  get currentState(): AudioPlayerState {
    return this.state;
  }

  get queueLength(): number {
    return this.queue.length;
  }

  // 切换请求作用域：旧请求的队列与在播音频立即清掉，迟到片段无法进入新队列。
  setRequest(requestId: string): void {
    if (this.requestId === requestId) return;
    this.clear();
    this.requestId = requestId;
  }

  enqueue(chunk: VoiceChunk): void {
    // requestId 隔离：被取消/已切换请求的迟到音频直接丢弃。
    if (chunk.requestId !== this.requestId) return;
    this.queue.push(chunk);
    if (this.state === 'IDLE') this.playNext();
  }

  pause(): void {
    if (this.state !== 'PLAYING' && this.state !== 'BUFFERING') return;
    if (this.current && this.current.ttsMode !== 'primary') {
      // 浏览器语音不支持暂停恢复：停当前段（该段保留，恢复时重读）。
      ttsController.cancel();
      this.setState('PAUSED');
      this.callbacks.onSpeechPause?.();
      return;
    }
    this.audioEl?.pause();
    this.setState('PAUSED');
    this.callbacks.onSpeechPause?.();
  }

  resume(): void {
    if (this.state !== 'PAUSED') return;
    if (this.current && this.current.ttsMode !== 'primary') {
      this.playFallback(this.current);
      return;
    }
    void this.audioEl?.play();
    this.setState('PLAYING');
    this.callbacks.onSpeechResume?.();
  }

  stop(): void {
    if (this.state === 'IDLE' && !this.current) return;
    this.stopCurrent();
    this.setState('STOPPED');
  }

  // 清空队列并停止一切声音（用于停止生成/关闭语音/切会话/新请求）。
  clear(): void {
    this.queue = [];
    this.stopCurrent();
    this.setState('IDLE');
  }

  destroy(): void {
    this.clear();
    if (this.audioEl) {
      this.audioEl.src = '';
      this.audioEl = null;
    }
    this.callbacks = {};
  }

  private playNext(): void {
    const chunk = this.queue.shift();
    if (!chunk) {
      this.current = null;
      this.setState('IDLE');
      return;
    }
    this.current = chunk;
    if (chunk.ttsMode === 'primary' && chunk.audioDataUrl) {
      this.playPrimary(chunk);
    } else {
      this.playFallback(chunk);
    }
  }

  private playPrimary(chunk: VoiceChunk): void {
    if (!this.audioEl) {
      this.audioEl = new Audio();
      this.audioEl.addEventListener('playing', () => {
        this.setState('PLAYING');
      });
      this.audioEl.addEventListener('ended', () => {
        this.finishCurrent();
      });
      this.audioEl.addEventListener('error', () => {
        this.handleChunkError(chunk);
      });
    }
    this.setState('BUFFERING');
    this.audioEl.src = chunk.audioDataUrl as string;
    void this.audioEl.play().catch(() => {
      // 自动播放被拦截等异常：按错误处理，跳下一条不卡死队列。
      this.handleChunkError(chunk);
    });
    this.callbacks.onSpeechStart?.(chunk);
  }

  private playFallback(chunk: VoiceChunk): void {
    this.setState('PLAYING');
    this.callbacks.onSpeechStart?.(chunk);
    ttsController.speak(chunk.text, {
      onStart: () => undefined,
      onEnd: () => this.finishCurrent(),
      onError: () => this.handleChunkError(chunk),
    });
  }

  private finishCurrent(): void {
    const finished = this.current;
    if (finished) {
      this.current = null;
      this.callbacks.onSpeechEnd?.(finished);
    }
    if (this.state === 'STOPPED' || this.state === 'IDLE') return;
    this.playNext();
  }

  private handleChunkError(chunk: VoiceChunk): void {
    // 异常片段跳过，不卡死整个队列。
    if (this.current?.seq === chunk.seq) this.current = null;
    this.setState('ERROR');
    this.callbacks.onChunkError?.(chunk);
    if (this.state !== 'STOPPED' && this.state !== 'IDLE') {
      this.playNext();
    }
  }

  private stopCurrent(): void {
    ttsController.cancel();
    this.audioEl?.pause();
    if (this.current) {
      this.current = null;
      if (this.state === 'PLAYING' || this.state === 'PAUSED' || this.state === 'BUFFERING') {
        this.callbacks.onSpeechCancelled?.();
      }
    }
  }

  private setState(state: AudioPlayerState): void {
    if (this.state === state) return;
    this.state = state;
    this.callbacks.onStateChange?.(state);
  }
}
