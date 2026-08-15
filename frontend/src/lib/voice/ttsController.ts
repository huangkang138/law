'use client';

// 浏览器文字转语音控制器（Web Speech speechSynthesis）。
// 从 VoiceCourtroom.tsx 提取为独立轻量模块，不引用模拟法庭业务组件：
// 中文 voice 优先、朗读文本清洗、新朗读先取消旧朗读（打断语义），
// 状态回调驱动 UI，朗读失败静默回退（不打断聊天）。

export interface TtsCallbacks {
  onStart: () => void;
  onEnd: () => void;
  onError?: () => void;
}

export function isTtsSupported(): boolean {
  if (typeof window === 'undefined') return false;
  return 'speechSynthesis' in window;
}

// 朗读文本清洗：去除注释块、Markdown 符号、emoji 与多余空白。
// 回复正文以 Markdown 呈现（加粗、列表、段落），朗读时还原为纯口语文本。
export function filterSpeakableText(text: string): string {
  return text
    .replace(/【[^】]*】/g, '')
    .replace(/\[[^\]]*\]/g, '')
    .replace(/（[^）]*）/g, '')
    .replace(/\([^)]*\)/g, '')
    .replace(/[*+#@]/g, '')
    .replace(/[-]{2,}/g, '')
    .replace(/[•·]/g, '')
    .replace(/(?:[✀-➿]|[☀-⛿]|[←-⇿]|[⌀-⏿]|[⬀-⯿]|[️]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|\uD83E[\uDC00-\uDFFF])/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

let cachedVoices: SpeechSynthesisVoice[] = [];

function refreshVoices(): SpeechSynthesisVoice[] {
  if (!isTtsSupported()) return [];
  const voices = window.speechSynthesis.getVoices();
  if (voices.length) cachedVoices = voices;
  return cachedVoices;
}

// 中文 voice 优先，女声名优先（法小助人设）；无中文 voice 时用系统默认 voice 仍朗读。
function pickChineseVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const zh = voices.filter((voice) => voice.lang.toLowerCase().includes('zh'));
  if (zh.length === 0) return null;
  for (const keyword of ['xiaoxiao', 'xiaoyi', 'huihui', 'xia']) {
    const found = zh.find((voice) => voice.name.toLowerCase().includes(keyword));
    if (found) return found;
  }
  return zh[0];
}

export class TtsController {
  private speaking = false;

  get isSpeaking(): boolean {
    return this.speaking;
  }

  speak(text: string, callbacks: TtsCallbacks): void {
    if (!isTtsSupported()) return;
    const clean = filterSpeakableText(text);
    if (!clean) return;
    // 新朗读先取消旧朗读：新回复、新气泡点击都会打断旧朗读。
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = 'zh-CN';
    utterance.rate = 1;
    const voice = pickChineseVoice(refreshVoices());
    if (voice) utterance.voice = voice;
    utterance.onstart = () => {
      this.speaking = true;
      callbacks.onStart();
    };
    const finish = () => {
      this.speaking = false;
      callbacks.onEnd();
    };
    utterance.onend = finish;
    utterance.onerror = () => {
      // 朗读失败静默回退为文字，不追加错误气泡。
      finish();
      callbacks.onError?.();
    };
    window.speechSynthesis.speak(utterance);
  }

  cancel(): void {
    if (!isTtsSupported()) return;
    this.speaking = false;
    window.speechSynthesis.cancel();
  }
}

export const ttsController = new TtsController();

// 浏览器语音列表异步加载（voiceschanged），朗读时用缓存兜底。
if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = refreshVoices;
}
