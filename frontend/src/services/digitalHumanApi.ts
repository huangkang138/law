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

export type AgentRunStatus =
  | 'planning' | 'executing' | 'retrying' | 'awaiting_approval'
  | 'completed' | 'failed' | 'cancelled';

export interface DigitalHumanAgentRun {
  // 后端持久化任务的完整 UI 快照；刷新后可按 run_id 重新获取。
  success: boolean;
  run_id: string;
  matter_id: string;
  status: AgentRunStatus;
  current_step_id: string | null;
  steps: Array<{ id: string; name: string; status: string; tool_name: string | null }>;
  approval: { id: string; prompt: string; status: string } | null;
  final_output: { summary?: string; notice?: string } | null;
  error_code: string | null;
}

export interface MatterMaterial {
  document_id: string;
  filename: string;
  content_hash: string;
  character_count: number;
  fragment_count: number;
}

export interface LocatedLegalFact {
  fact_id: string;
  fact_type: string;
  fact_text: string;
  confidence: number;
  material_ref: {
    document_id: string;
    fragment_id: string;
    start_offset: number;
    end_offset: number;
    page_number: number | null;
    quote: string;
  };
}

export interface MatterAnalysisResult {
  facts: LocatedLegalFact[];
  timeline: Array<{ date: string; fact_id: string; event: string }>;
  checklist: {
    available: Array<{ document_id: string; filename: string }>;
    missing: string[];
    located_fact_count: number;
    warning: string;
  };
}

export interface DigitalHumanMatterSummary {
  matter_id: string;
  title: string;
  goal: string;
  created_at: string | null;
  updated_at: string | null;
}

export interface DigitalHumanMatterDetail {
  matter_id: string;
  title: string;
  goal: string;
  jurisdiction: null | {
    country_code: string;
    subdivision_code: string | null;
    language: string;
    effective_at: string;
    confirmed_by_user: boolean;
  };
}

export interface LaborCompensationResult {
  compensation: number;
  monthly_salary: number;
  years: number;
  months: number;
  formula: string;
  calculation: string;
  warning: string;
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

export async function startDigitalHumanAgentRun(goal: string, sessionId: string | null): Promise<DigitalHumanAgentRun> {
  // 创建后端任务后，接口会同步推进到等待审批或终态。
  const response = await request('/api/digital-human/agent/runs', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goal, ...(sessionId ? { session_id: sessionId } : {}) }),
  });
  return readJson<DigitalHumanAgentRun>(response);
}

export async function resumeDigitalHumanAgentRun(runId: string, approved: boolean): Promise<DigitalHumanAgentRun> {
  // approved 是显式用户决定，前端不能替用户默认确认。
  const response = await request(`/api/digital-human/agent/runs/${encodeURIComponent(runId)}/resume`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ approved }),
  });
  return readJson<DigitalHumanAgentRun>(response);
}

export async function cancelDigitalHumanAgentRun(runId: string): Promise<DigitalHumanAgentRun> {
  // 取消操作同时终止当前步骤，返回取消后的权威快照。
  const response = await request(`/api/digital-human/agent/runs/${encodeURIComponent(runId)}/cancel`, { method: 'POST' });
  return readJson<DigitalHumanAgentRun>(response);
}

export async function createDigitalHumanMatter(goal: string): Promise<{ matter_id: string; title: string; goal: string }> {
  const response = await request('/api/digital-human/agent/matters', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ goal }),
  });
  return readJson(response);
}

export async function confirmMatterJurisdiction(matterId: string, subdivisionCode: string): Promise<void> {
  const response = await request(`/api/digital-human/agent/matters/${encodeURIComponent(matterId)}/jurisdiction`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      country_code: 'CN', subdivision_code: subdivisionCode || null,
      effective_at: new Date().toISOString(), confirmed_by_user: true,
    }),
  });
  await readJson(response);
}

export async function addMatterMaterial(
  matterId: string, filename: string, text: string,
): Promise<MatterMaterial> {
  const response = await request(`/api/digital-human/agent/matters/${encodeURIComponent(matterId)}/materials`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename, text, media_type: 'text/plain' }),
  });
  return readJson(response);
}

export async function analyzeMatterMaterial(
  matterId: string, documentId: string,
): Promise<MatterAnalysisResult> {
  const base = `/api/digital-human/agent/matters/${encodeURIComponent(matterId)}`;
  const factsResponse = await request(`${base}/materials/${encodeURIComponent(documentId)}/facts`, { method: 'POST' });
  const facts = (await readJson<{ facts: LocatedLegalFact[] }>(factsResponse)).facts;
  const [timelineResponse, checklistResponse] = await Promise.all([
    request(`${base}/timeline`), request(`${base}/evidence-checklist`),
  ]);
  const timeline = (await readJson<{ timeline: MatterAnalysisResult['timeline'] }>(timelineResponse)).timeline;
  const checklist = await readJson<MatterAnalysisResult['checklist']>(checklistResponse);
  return { facts, timeline, checklist };
}

export async function getDigitalHumanMatters(): Promise<DigitalHumanMatterSummary[]> {
  const response = await request('/api/digital-human/agent/matters');
  return (await readJson<{ matters: DigitalHumanMatterSummary[] }>(response)).matters;
}

export async function deleteDigitalHumanMatter(matterId: string): Promise<void> {
  const response = await request(`/api/digital-human/agent/matters/${encodeURIComponent(matterId)}`, { method: 'DELETE' });
  await readJson(response);
}

export async function getDigitalHumanMatter(matterId: string): Promise<DigitalHumanMatterDetail> {
  const response = await request(`/api/digital-human/agent/matters/${encodeURIComponent(matterId)}`);
  return readJson(response);
}

export async function calculateMatterLaborCompensation(
  matterId: string, monthlySalary: number, years: number, months: number,
): Promise<LaborCompensationResult> {
  const response = await request(`/api/digital-human/agent/matters/${encodeURIComponent(matterId)}/tools/labor-compensation`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ monthly_salary: monthlySalary, years, months }),
  });
  return (await readJson<{ data: LaborCompensationResult }>(response)).data;
}
