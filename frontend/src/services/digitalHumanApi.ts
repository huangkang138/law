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
): Promise<DigitalHumanChatResponse> {
  const response = await fetch('/api/digital-human/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      ...(sessionId ? { session_id: sessionId } : {}),
    }),
  });

  return readJson<DigitalHumanChatResponse>(response);
}

export async function resetDigitalHumanSession(sessionId: string): Promise<void> {
  const response = await fetch('/api/digital-human/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });

  await readJson<{ success: boolean }>(response);
}
