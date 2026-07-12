export type DigitalHumanEmotion =
  | 'idle'
  | 'welcome'
  | 'thinking'
  | 'talk_normal'
  | 'serious'
  | 'success'
  | 'error'
  | 'handoff';

export interface DigitalHumanChatResponse {
  success: boolean;
  reply: string;
  intent: string;
  emotion: DigitalHumanEmotion;
  confidence: number;
  route: string | null;
  route_label: string | null;
  session_id: string;
}

interface ApiErrorResponse {
  error?: string;
}

export interface DigitalHumanSessionSummary {
  id: string;
  title: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface DigitalHumanHistoryMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  emotion?: DigitalHumanEmotion | null;
  created_at: string | null;
}

const CLIENT_ID_KEY = 'yys-law-digital-human-client-id';

function getClientId(): string {
  const existing = window.localStorage.getItem(CLIENT_ID_KEY);
  if (existing?.startsWith('dhc_')) return existing;
  const value = `dhc_${crypto.randomUUID()}`;
  window.localStorage.setItem(CLIENT_ID_KEY, value);
  return value;
}

async function request(path: string, init: RequestInit = {}, timeoutMs = 45000) {
  const controller = new AbortController();
  const abort = () => controller.abort();
  init.signal?.addEventListener('abort', abort, { once: true });
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(path, {
      ...init,
      signal: controller.signal,
      headers: {
        'X-Digital-Human-Client-ID': getClientId(),
        ...init.headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('请求已取消或等待超时');
    }
    throw error;
  } finally {
    init.signal?.removeEventListener('abort', abort);
    window.clearTimeout(timer);
  }
}

async function readJson<T>(response: Response): Promise<T> {
  const data = (await response.json().catch(() => ({}))) as T & ApiErrorResponse;
  if (!response.ok) {
    throw new Error(data.error || '数字人服务暂时不可用');
  }
  return data;
}

export async function sendDigitalHumanMessage(
  question: string,
  sessionId: string | null,
  requestId: string,
  signal?: AbortSignal,
): Promise<DigitalHumanChatResponse> {
  const response = await request('/api/digital-human/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question, request_id: requestId,
      ...(sessionId ? { session_id: sessionId } : {}),
    }), signal,
  });

  return readJson<DigitalHumanChatResponse>(response);
}

export async function resetDigitalHumanSession(sessionId: string): Promise<void> {
  const response = await request('/api/digital-human/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });

  await readJson<{ success: boolean }>(response);
}

export async function getDigitalHumanSessions(): Promise<DigitalHumanSessionSummary[]> {
  const response = await request('/api/digital-human/sessions');
  return (await readJson<{ success: boolean; sessions: DigitalHumanSessionSummary[] }>(response)).sessions;
}

export async function getDigitalHumanMessages(sessionId: string): Promise<DigitalHumanHistoryMessage[]> {
  const response = await request(`/api/digital-human/sessions/${encodeURIComponent(sessionId)}/messages`);
  return (await readJson<{ success: boolean; messages: DigitalHumanHistoryMessage[] }>(response)).messages;
}

export async function deleteDigitalHumanSession(sessionId: string): Promise<void> {
  const response = await request(`/api/digital-human/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
  await readJson<{ success: boolean }>(response);
}
