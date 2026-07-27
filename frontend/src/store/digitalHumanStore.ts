import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import {
  DigitalHumanAgentRun,
  DigitalHumanEmotion,
  DigitalHumanSessionSummary,
  LaborTriageSnapshot,
  deleteDigitalHumanSession,
  getDigitalHumanMessages,
  getDigitalHumanSessions,
  resetDigitalHumanSession,
  sendDigitalHumanMessage,
} from '@/services/digitalHumanApi';

export interface DigitalHumanMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  route?: string | null;
  routeLabel?: string | null;
  createdAt: number;
}

interface DigitalHumanStore {
  isOpen: boolean;
  emotion: DigitalHumanEmotion;
  messages: DigitalHumanMessage[];
  sessionId: string | null;
  isLoading: boolean;
  sessions: DigitalHumanSessionSummary[];
  historyError: string;
  currentMatterId: string | null;
  currentTriage: LaborTriageSnapshot | null;
  currentAgentRun: DigitalHumanAgentRun | null;
  laborTriageLoading: boolean;
  laborTriageError: string;
  laborContextBySession: Record<string, {
    matterId: string;
    runId: string | null;
    triageStarted: boolean;
  }>;
  open: () => void;
  close: () => void;
  toggle: () => void;
  setEmotion: (emotion: DigitalHumanEmotion) => void;
  sendMessage: (question: string) => Promise<void>;
  reset: () => Promise<void>;
  loadSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  refreshHistory: () => Promise<void>;
  startNewConversation: () => void;
  cancelRequest: () => void;
  setLaborContext: (context: {
    matterId?: string | null;
    triage?: LaborTriageSnapshot | null;
    run?: DigitalHumanAgentRun | null;
    loading?: boolean;
    error?: string;
  }) => void;
  selectCurrentMatter: (matterId: string | null) => void;
  setCurrentAgentRun: (run: DigitalHumanAgentRun | null) => void;
}

let activeRequest: AbortController | null = null;

const WELCOME_MESSAGE: DigitalHumanMessage = {
  id: 'digital-human-welcome',
  role: 'assistant',
  content: '你好呀！我是法小助。你可以直接告诉我想解决什么问题，我来帮你找到合适的功能。',
  createdAt: 0,
};

function createMessageId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export const useDigitalHumanStore = create<DigitalHumanStore>()(
  persist(
    (set, get) => ({
      isOpen: false,
      emotion: 'idle',
      messages: [],
      sessionId: null,
      isLoading: false,
      sessions: [],
      historyError: '',
      currentMatterId: null,
      currentTriage: null,
      currentAgentRun: null,
      laborTriageLoading: false,
      laborTriageError: '',
      laborContextBySession: {},

      open: () => {
        set((state) => ({
          isOpen: true,
          emotion: state.messages.length === 0 ? 'welcome' : state.emotion,
          messages: state.messages.length === 0 ? [WELCOME_MESSAGE] : state.messages,
        }));
        void get().loadSessions();
        if (get().sessionId) void get().loadSession(get().sessionId as string);
      },

      close: () => set({ isOpen: false, emotion: 'idle' }),

      toggle: () => {
        if (get().isOpen) {
          get().close();
        } else {
          get().open();
        }
      },

      setEmotion: (emotion) => set({ emotion }),

      sendMessage: async (rawQuestion) => {
        const question = rawQuestion.trim();
        if (!question || get().isLoading) return;

        const userMessage: DigitalHumanMessage = {
          id: createMessageId('user'),
          role: 'user',
          content: question,
          createdAt: Date.now(),
        };

        set((state) => ({
          messages: [...state.messages, userMessage],
          isLoading: true,
          emotion: 'thinking',
        }));

        try {
          activeRequest = new AbortController();
          const response = await sendDigitalHumanMessage(
            question, get().sessionId, `dhr_${crypto.randomUUID()}`, activeRequest.signal,
          );
          const assistantMessage: DigitalHumanMessage = {
            id: createMessageId('assistant'),
            role: 'assistant',
            content: response.reply,
            route: response.route,
            routeLabel: response.route_label,
            createdAt: Date.now(),
          };

          set((state) => {
            const matterId = response.context?.matter_id || null;
            const runId = response.context?.run_id || null;
            const laborContextBySession = matterId ? {
              ...state.laborContextBySession,
              [response.session_id]: {
                matterId,
                runId,
                triageStarted: response.decision?.route === 'labor_triage'
                  || response.action?.type === 'start_agent'
                  || Boolean(state.laborContextBySession[response.session_id]?.triageStarted),
              },
            } : state.laborContextBySession;
            return {
              messages: [...state.messages, assistantMessage],
              sessionId: response.session_id,
              emotion: response.emotion,
              isLoading: false,
              currentMatterId: matterId || state.currentMatterId,
              currentTriage: matterId && matterId !== state.currentMatterId
                ? null : state.currentTriage,
              currentAgentRun: matterId && matterId !== state.currentMatterId
                ? null : state.currentAgentRun,
              laborContextBySession,
            };
          });
          void get().loadSessions();
        } catch (error) {
          const message = error instanceof Error ? error.message : '数字人服务暂时不可用';
          set((state) => ({
            messages: [
              ...state.messages,
              {
                id: createMessageId('error'),
                role: 'assistant',
                content: `${message}，请稍后再试。`,
                createdAt: Date.now(),
              },
            ],
            emotion: 'error',
            isLoading: false,
          }));
        } finally {
          activeRequest = null;
        }
      },

      reset: async () => {
        const sessionId = get().sessionId;
        if (sessionId) {
          try {
            await resetDigitalHumanSession(sessionId);
          } catch {
            // 本地会话仍应允许清空，下一次发送会创建新的会话。
          }
        }
        set({
          messages: [WELCOME_MESSAGE],
          sessionId: null,
          emotion: 'welcome',
          isLoading: false,
          currentMatterId: null,
          currentTriage: null,
          currentAgentRun: null,
          laborTriageError: '',
        });
        void get().loadSessions();
      },

      loadSessions: async () => {
        try {
          set({ sessions: await getDigitalHumanSessions(), historyError: '' });
        } catch (error) {
          set({
            historyError: error instanceof Error
              ? `历史会话读取失败：${error.message}`
              : '历史会话读取失败，请稍后重试',
          });
        }
      },

      loadSession: async (sessionId) => {
        try {
          const history = await getDigitalHumanMessages(sessionId);
          const context = get().laborContextBySession[sessionId];
          set({
            sessionId,
            messages: history.length ? history.map((item) => ({
              id: item.id, role: item.role, content: item.content,
              createdAt: item.created_at ? Date.parse(item.created_at) : 0,
            })) : [WELCOME_MESSAGE],
            emotion: 'idle',
            currentMatterId: context?.matterId || null,
            currentTriage: null,
            currentAgentRun: null,
            laborTriageError: '',
          });
        } catch { /* 会话可能已从其他页面删除 */ }
      },

      deleteSession: async (sessionId) => {
        await deleteDigitalHumanSession(sessionId);
        if (get().sessionId === sessionId) {
          set({
            sessionId: null, messages: [WELCOME_MESSAGE], emotion: 'welcome',
            currentMatterId: null, currentTriage: null, currentAgentRun: null,
          });
        }
        set((state) => {
          const contexts = { ...state.laborContextBySession };
          delete contexts[sessionId];
          return { laborContextBySession: contexts };
        });
        await get().loadSessions();
      },

      refreshHistory: async () => {
        await get().loadSessions();
        const currentSessionId = get().sessionId;
        if (currentSessionId) await get().loadSession(currentSessionId);
      },

      startNewConversation: () => {
        set({
          sessionId: null,
          messages: [WELCOME_MESSAGE],
          emotion: 'welcome',
          isLoading: false,
          currentMatterId: null,
          currentTriage: null,
          currentAgentRun: null,
          laborTriageError: '',
        });
      },

      cancelRequest: () => {
        activeRequest?.abort();
        activeRequest = null;
        set({ isLoading: false, emotion: 'idle' });
      },

      setLaborContext: (context) => set((state) => {
        const matterId = context.matterId !== undefined ? context.matterId : state.currentMatterId;
        const run = context.run !== undefined ? context.run : state.currentAgentRun;
        const contexts = { ...state.laborContextBySession };
        if (state.sessionId && context.matterId === null) delete contexts[state.sessionId];
        if (state.sessionId && matterId) {
          const previous = contexts[state.sessionId];
          contexts[state.sessionId] = {
            matterId,
            runId: run?.run_id || null,
            triageStarted: previous?.matterId === matterId
              ? previous.triageStarted || context.triage != null
              : context.triage != null,
          };
        }
        return {
          currentMatterId: matterId,
          currentTriage: context.triage !== undefined ? context.triage : state.currentTriage,
          currentAgentRun: run,
          laborTriageLoading: context.loading !== undefined ? context.loading : state.laborTriageLoading,
          laborTriageError: context.error !== undefined ? context.error : state.laborTriageError,
          laborContextBySession: contexts,
        };
      }),

      selectCurrentMatter: (matterId) => set((state) => {
        if (matterId && state.currentMatterId === matterId) return { currentMatterId: matterId };
        const contexts = { ...state.laborContextBySession };
        if (state.sessionId && matterId) {
          contexts[state.sessionId] = { matterId, runId: null, triageStarted: false };
        }
        if (state.sessionId && !matterId) delete contexts[state.sessionId];
        return {
          currentMatterId: matterId,
          currentTriage: null,
          currentAgentRun: null,
          laborTriageError: '',
          laborContextBySession: contexts,
        };
      }),

      setCurrentAgentRun: (run) => get().setLaborContext({ run }),

    }),
    {
      name: 'yys-law-digital-human',
      partialize: (state) => ({
        sessionId: state.sessionId,
        laborContextBySession: state.laborContextBySession,
      }),
    },
  ),
);
