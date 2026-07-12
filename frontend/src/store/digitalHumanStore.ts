import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import {
  DigitalHumanEmotion,
  DigitalHumanAgentRun,
  DigitalHumanSessionSummary,
  deleteDigitalHumanSession,
  getDigitalHumanMessages,
  getDigitalHumanSessions,
  resetDigitalHumanSession,
  sendDigitalHumanMessage,
  startDigitalHumanAgentRun,
  resumeDigitalHumanAgentRun,
  cancelDigitalHumanAgentRun,
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
  agentRun: DigitalHumanAgentRun | null;
  isAgentLoading: boolean;
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
  startAgentDemo: (goal: string) => Promise<void>;
  decideAgentApproval: (approved: boolean) => Promise<void>;
  cancelAgentRun: () => Promise<void>;
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
      agentRun: null,
      isAgentLoading: false,

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

          set((state) => ({
            messages: [...state.messages, assistantMessage],
            sessionId: response.session_id,
            emotion: response.emotion,
            isLoading: false,
          }));
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
        });
        void get().loadSessions();
      },

      loadSessions: async () => {
        try { set({ sessions: await getDigitalHumanSessions() }); } catch { /* 保留当前界面 */ }
      },

      loadSession: async (sessionId) => {
        try {
          const history = await getDigitalHumanMessages(sessionId);
          set({
            sessionId,
            messages: history.length ? history.map((item) => ({
              id: item.id, role: item.role, content: item.content,
              createdAt: item.created_at ? Date.parse(item.created_at) : 0,
            })) : [WELCOME_MESSAGE],
            emotion: 'idle',
          });
        } catch { /* 会话可能已从其他页面删除 */ }
      },

      deleteSession: async (sessionId) => {
        await deleteDigitalHumanSession(sessionId);
        if (get().sessionId === sessionId) {
          set({ sessionId: null, messages: [WELCOME_MESSAGE], emotion: 'welcome' });
        }
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
        });
      },

      cancelRequest: () => {
        activeRequest?.abort();
        activeRequest = null;
        set({ isLoading: false, emotion: 'idle' });
      },

      startAgentDemo: async (goal) => {
        // Agent 任务与普通聊天分别维护 loading，避免阻塞历史消息操作。
        if (get().isAgentLoading) return;
        set({ isAgentLoading: true, emotion: 'thinking' });
        try {
          const agentRun = await startDigitalHumanAgentRun(goal, get().sessionId);
          set({ agentRun, isAgentLoading: false, emotion: agentRun.status === 'awaiting_approval' ? 'serious' : 'success' });
        } catch {
          set({ isAgentLoading: false, emotion: 'error' });
        }
      },

      decideAgentApproval: async (approved) => {
        // 只对当前待审批任务提交决定，结果以服务端返回快照为准。
        const run = get().agentRun;
        if (!run || get().isAgentLoading) return;
        set({ isAgentLoading: true, emotion: 'thinking' });
        try {
          const agentRun = await resumeDigitalHumanAgentRun(run.run_id, approved);
          set({ agentRun, isAgentLoading: false, emotion: approved ? 'success' : 'idle' });
        } catch {
          set({ isAgentLoading: false, emotion: 'error' });
        }
      },

      cancelAgentRun: async () => {
        // 本地不直接伪造 cancelled 状态，等待后端完成持久化后再更新。
        const run = get().agentRun;
        if (!run) return;
        const agentRun = await cancelDigitalHumanAgentRun(run.run_id);
        set({ agentRun, emotion: 'idle' });
      },
    }),
    {
      name: 'yys-law-digital-human',
      partialize: (state) => ({
        sessionId: state.sessionId,
      }),
    },
  ),
);
