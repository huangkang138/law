import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import {
  DigitalHumanAgentRun,
  DigitalHumanEmotion,
  DigitalHumanSessionSummary,
  ConversationPresentation,
  DigitalHumanStreamError,
  DigitalHumanWorkspaceContext,
  LaborTriageSnapshot,
  cancelDigitalHumanChatRequest,
  createDigitalHumanWorkspaceSession,
  deleteDigitalHumanSession,
  getDigitalHumanMessages,
  getDigitalHumanSessions,
  getDigitalHumanWorkspace,
  resetDigitalHumanSession,
  selectDigitalHumanWorkspaceMatter,
  sendDigitalHumanMessageStream,
} from '@/services/digitalHumanApi';
import { ttsController } from '@/lib/voice/ttsController';
import { StreamingAudioPlayer } from '@/lib/voice/streamingAudioPlayer';

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
  workspacePresentation: ConversationPresentation | null;
  workspaceVersion: number;
  workspaceLoading: boolean;
  workspaceError: string;
  streamingMessage: DigitalHumanMessage | null;
  streamFallbackNotice: string;
  voiceEnabled: boolean;
  voiceSpeaking: boolean;
  speakingMessageId: string | null;
  voiceMode: 'primary' | 'fallback' | null;
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
  ensureWorkspaceSession: () => Promise<string>;
  loadSession: (sessionId: string) => Promise<boolean>;
  refreshWorkspace: (sessionId: string) => Promise<boolean>;
  applyWorkspaceContext: (workspace: DigitalHumanWorkspaceContext) => boolean;
  deleteSession: (sessionId: string) => Promise<void>;
  refreshHistory: () => Promise<void>;
  startNewConversation: () => void;
  cancelRequest: () => void;
  toggleVoice: () => void;
  speakMessage: (messageId: string, content: string) => void;
  stopSpeaking: () => void;
  setLaborContext: (context: {
    matterId?: string | null;
    triage?: LaborTriageSnapshot | null;
    run?: DigitalHumanAgentRun | null;
    loading?: boolean;
    error?: string;
  }) => void;
  selectCurrentMatter: (matterId: string | null) => Promise<void>;
  setCurrentAgentRun: (run: DigitalHumanAgentRun | null) => void;
}

let activeRequest: AbortController | null = null;
let activeRequestId: string | null = null;
let hydrationSequence = 0;
let conversationOperationSequence = 0;
let workspaceSelectionTail: Promise<void> = Promise.resolve();
let voicePlayer: StreamingAudioPlayer;

function invalidateConversationRequest() {
  conversationOperationSequence += 1;
  activeRequest?.abort();
  activeRequest = null;
}

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
      workspacePresentation: null,
      workspaceVersion: 0,
      workspaceLoading: false,
      workspaceError: '',
      streamingMessage: null,
      streamFallbackNotice: '',
      voiceEnabled: false,
      voiceSpeaking: false,
      speakingMessageId: null,
      voiceMode: null,
      laborContextBySession: {},

      open: () => {
        const openOperation = conversationOperationSequence;
        set((state) => ({
          isOpen: true,
          emotion: state.messages.length === 0 ? 'welcome' : state.emotion,
          messages: state.messages.length === 0 ? [WELCOME_MESSAGE] : state.messages,
        }));
        void get().loadSessions().then(async () => {
          if (openOperation !== conversationOperationSequence) return;
          const sessions = get().sessions;
          const current = get().sessionId;
          const target = sessions.some((item) => item.id === current)
            ? current
            : sessions[0]?.id || null;
          if (target) await get().loadSession(target);
        });
      },

      close: () => {
        ttsController.cancel();
        voicePlayer.clear();
        set({ isOpen: false, emotion: 'idle', voiceSpeaking: false, speakingMessageId: null });
      },

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

        // 新输入打断旧朗读（语音与键盘输入一致）。
        ttsController.cancel();
        const voiceRequested = get().voiceEnabled;
        set((state) => ({
          messages: [...state.messages, userMessage],
          streamingMessage: null,
          streamFallbackNotice: '',
          isLoading: true,
          emotion: 'thinking',
          voiceSpeaking: false,
          speakingMessageId: null,
        }));

        const operation = ++conversationOperationSequence;
        const controller = new AbortController();
        const requestId = `dhr_${crypto.randomUUID()}`;
        activeRequestId = requestId;
        // 播放器切到新请求作用域：清旧队列、停在播音频，
        // 被取消/被替换请求的迟到音频一律不得进入新队列。
        voicePlayer.setRequest(requestId);
        try {
          activeRequest = controller;
          const response = await sendDigitalHumanMessageStream(
            question, get().sessionId, requestId, {
              onDelta: (text) => {
                if (operation !== conversationOperationSequence) return;
                if (!text) return;
                set((state) => ({
                  streamingMessage: state.streamingMessage
                    ? {
                        ...state.streamingMessage,
                        content: state.streamingMessage.content + text,
                      }
                    : {
                        id: createMessageId('assistant'),
                        role: 'assistant',
                        content: text,
                        createdAt: Date.now(),
                      },
                }));
              },
              onVoice: (payload) => {
                // 句级语音：按发送时与当前的语音开关双重守卫；
                // 关闭语音后即使事件迟到也不产生声音。
                if (operation !== conversationOperationSequence) return;
                if (!voiceRequested || !get().voiceEnabled) return;
                voicePlayer.enqueue({
                  seq: payload.seq,
                  requestId: payload.requestId,
                  text: payload.text,
                  audioDataUrl: payload.audioDataUrl,
                  ttsMode: payload.ttsMode,
                });
                set({
                  voiceSpeaking: true,
                  speakingMessageId: get().streamingMessage?.id || null,
                  voiceMode: payload.ttsMode,
                });
              },
              onStreamFallback: () => {
                if (operation !== conversationOperationSequence) return;
                set({ streamFallbackNotice: '当前浏览器不支持增量显示，已切换为普通回复。' });
              },
            },
            controller.signal,
            voiceRequested,
          );
          if (operation !== conversationOperationSequence) return;
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
              streamingMessage: null,
              currentMatterId: matterId || state.currentMatterId,
              currentTriage: matterId && matterId !== state.currentMatterId
                ? null : state.currentTriage,
              currentAgentRun: matterId && matterId !== state.currentMatterId
                ? null : state.currentAgentRun,
              laborContextBySession,
            };
          });
          void get().loadSessions();
          void get().refreshWorkspace(response.session_id);
        } catch (error) {
          if (operation !== conversationOperationSequence) return;
          if (error instanceof DigitalHumanStreamError && error.code === 'CANCELLED') {
            // 服务端已确认停止：不追加错误气泡，只给出轻量提示。
            set({
              isLoading: false,
              emotion: 'idle',
              streamingMessage: null,
              streamFallbackNotice: '已停止回复',
            });
            return;
          }
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
            streamingMessage: null,
          }));
        } finally {
          if (activeRequest === controller) activeRequest = null;
          if (activeRequestId === requestId) activeRequestId = null;
        }
      },

      reset: async () => {
        invalidateConversationRequest();
        ttsController.cancel();
        voicePlayer.clear();
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
          workspacePresentation: null,
          workspaceVersion: 0,
          workspaceError: '',
          streamingMessage: null,
          streamFallbackNotice: '',
          voiceSpeaking: false,
          speakingMessageId: null,
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

      ensureWorkspaceSession: async () => {
        const existing = get().sessionId;
        if (existing) return existing;
        const workspace = await createDigitalHumanWorkspaceSession();
        set({
          sessionId: workspace.session_id,
          currentMatterId: null,
          currentTriage: null,
          currentAgentRun: null,
          workspacePresentation: workspace.presentation,
          workspaceVersion: workspace.workspace_version,
          workspaceLoading: false,
          workspaceError: '',
        });
        void get().loadSessions();
        return workspace.session_id;
      },

      loadSession: async (sessionId) => {
        invalidateConversationRequest();
        ttsController.cancel();
        voicePlayer.clear();
        const sequence = ++hydrationSequence;
        set({
          isLoading: false,
          workspaceLoading: true,
          workspaceError: '',
          streamingMessage: null,
          voiceSpeaking: false,
          speakingMessageId: null,
        });
        try {
          const [history, workspace] = await Promise.all([
            getDigitalHumanMessages(sessionId),
            getDigitalHumanWorkspace(sessionId),
          ]);
          if (sequence !== hydrationSequence) return false;
          const matterId = workspace.matter?.matter_id || null;
          set({
            sessionId,
            messages: history.length ? history.map((item) => ({
              id: item.id, role: item.role, content: item.content,
              createdAt: item.created_at ? Date.parse(item.created_at) : 0,
            })) : [WELCOME_MESSAGE],
            emotion: 'idle',
            currentMatterId: matterId,
            currentTriage: workspace.triage,
            currentAgentRun: workspace.run,
            laborTriageError: '',
            workspacePresentation: workspace.presentation,
            workspaceVersion: workspace.workspace_version,
            workspaceLoading: false,
            workspaceError: '',
            laborContextBySession: matterId ? {
              ...get().laborContextBySession,
              [sessionId]: {
                matterId,
                runId: workspace.run?.run_id || null,
                triageStarted: workspace.triage !== null,
              },
            } : get().laborContextBySession,
          });
          return true;
        } catch (error) {
          if (sequence === hydrationSequence) {
            set({
              workspaceLoading: false,
              workspaceError: error instanceof Error
                ? `案件状态恢复失败：${error.message}`
                : '案件状态恢复失败',
            });
          }
          return false;
        }
      },

      refreshWorkspace: async (sessionId) => {
        try {
          const workspace = await getDigitalHumanWorkspace(sessionId);
          return get().applyWorkspaceContext(workspace);
        } catch (error) {
          if (get().sessionId === sessionId) {
            set({
              workspaceError: error instanceof Error
                ? `案件状态恢复失败：${error.message}`
              : '案件状态恢复失败',
            });
          }
          return false;
        }
      },

      applyWorkspaceContext: (workspace) => {
        const sessionId = workspace.session_id;
        const state = get();
        if (
          state.sessionId !== sessionId
          || workspace.workspace_version < state.workspaceVersion
        ) return false;
        const matterId = workspace.matter?.matter_id || null;
        set((current) => {
          const contexts = { ...current.laborContextBySession };
          if (matterId) {
            contexts[sessionId] = {
              matterId,
              runId: workspace.run?.run_id || null,
              triageStarted: workspace.triage !== null,
            };
          } else {
            delete contexts[sessionId];
          }
          return {
            currentMatterId: matterId,
            currentTriage: workspace.triage,
            currentAgentRun: workspace.run,
            workspacePresentation: workspace.presentation,
            workspaceVersion: workspace.workspace_version,
            workspaceLoading: false,
            workspaceError: '',
            laborTriageError: '',
            laborContextBySession: contexts,
          };
        });
        return true;
      },

      deleteSession: async (sessionId) => {
        if (get().sessionId === sessionId) {
          invalidateConversationRequest();
          ttsController.cancel();
          voicePlayer.clear();
        }
        await deleteDigitalHumanSession(sessionId);
        if (get().sessionId === sessionId) {
          set({
            sessionId: null, messages: [WELCOME_MESSAGE], emotion: 'welcome',
            currentMatterId: null, currentTriage: null, currentAgentRun: null,
            workspacePresentation: null, workspaceError: '',
            workspaceVersion: 0,
            streamingMessage: null,
            streamFallbackNotice: '',
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
        invalidateConversationRequest();
        ttsController.cancel();
        voicePlayer.clear();
        hydrationSequence += 1;
        set({
          sessionId: null,
          messages: [WELCOME_MESSAGE],
          emotion: 'welcome',
          isLoading: false,
          currentMatterId: null,
          currentTriage: null,
          currentAgentRun: null,
          laborTriageError: '',
          workspacePresentation: null,
          workspaceVersion: 0,
          workspaceLoading: false,
          workspaceError: '',
          streamingMessage: null,
          streamFallbackNotice: '',
          voiceSpeaking: false,
          speakingMessageId: null,
        });
      },

      cancelRequest: () => {
        // 真正的服务端取消：先通知服务端中断在途模型执行，再本地停止读取。
        const requestId = activeRequestId;
        activeRequestId = null;
        if (requestId) {
          void cancelDigitalHumanChatRequest(requestId).catch(() => undefined);
        }
        invalidateConversationRequest();
        // 停止按钮同时取消旧朗读：停止 = 取消 LLM + 取消 TTS + 清空音频队列。
        ttsController.cancel();
        voicePlayer.clear();
        // 操作序列已失效，sendMessage 的异步 CANCELLED 分支不会再执行：
        // 停止提示必须在这里同步给出，不能依赖该分支，也不能清空。
        set({
          isLoading: false,
          emotion: 'idle',
          streamingMessage: null,
          streamFallbackNotice: '已停止回复',
          voiceSpeaking: false,
          speakingMessageId: null,
        });
      },

      toggleVoice: () => {
        const enabled = !get().voiceEnabled;
        if (!enabled) get().stopSpeaking();
        set({ voiceEnabled: enabled });
      },

      speakMessage: (messageId, content) => {
        if (get().speakingMessageId === messageId && get().voiceSpeaking) {
          // 同一气泡再次点击 = 停止朗读。
          get().stopSpeaking();
          return;
        }
        // 气泡回放：走播放器队列（无后端 Provider 时明确以 fallback 模式朗读）。
        voicePlayer.setRequest(`bubble_${messageId}`);
        voicePlayer.enqueue({
          seq: 1,
          requestId: `bubble_${messageId}`,
          text: content,
          audioDataUrl: null,
          ttsMode: 'fallback',
        });
        set({ voiceSpeaking: true, speakingMessageId: messageId, voiceMode: 'fallback' });
      },

      stopSpeaking: () => {
        ttsController.cancel();
        voicePlayer.clear();
        set({ voiceSpeaking: false, speakingMessageId: null });
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

      selectCurrentMatter: (matterId) => {
        invalidateConversationRequest();
        const sessionId = get().sessionId;
        if (!sessionId) {
          set({
            currentMatterId: matterId,
            currentTriage: null,
            currentAgentRun: null,
            laborTriageError: '',
            isLoading: false,
            emotion: 'idle',
          });
          return Promise.resolve();
        }
        const select = async () => {
          if (get().sessionId !== sessionId) return;
          set({
            workspaceLoading: true,
            workspaceError: '',
            isLoading: false,
            emotion: 'idle',
            streamingMessage: null,
          });
          try {
            const workspace: DigitalHumanWorkspaceContext =
              await selectDigitalHumanWorkspaceMatter(
                sessionId,
                matterId,
                get().workspaceVersion,
              );
            if (get().sessionId !== sessionId) return;
            const selectedId = workspace.matter?.matter_id || null;
            set((state) => {
              const contexts = { ...state.laborContextBySession };
              if (selectedId) {
                contexts[sessionId] = {
                  matterId: selectedId,
                  runId: workspace.run?.run_id || null,
                  triageStarted: workspace.triage !== null,
                };
              } else {
                delete contexts[sessionId];
              }
              return {
                currentMatterId: selectedId,
                currentTriage: workspace.triage,
                currentAgentRun: workspace.run,
                workspacePresentation: workspace.presentation,
                workspaceVersion: workspace.workspace_version,
                workspaceLoading: false,
                workspaceError: '',
                laborTriageError: '',
                laborContextBySession: contexts,
              };
            });
          } catch (error) {
            if (get().sessionId === sessionId) {
              set({
                workspaceLoading: false,
                workspaceError: error instanceof Error
                  ? `案件切换失败：${error.message}`
                  : '案件切换失败',
              });
            }
            throw error;
          }
        };
        const result = workspaceSelectionTail.then(select, select);
        workspaceSelectionTail = result.catch(() => undefined);
        return result;
      },

      setCurrentAgentRun: (run) => {
        get().setLaborContext({ run });
        const sessionId = get().sessionId;
        if (sessionId) void get().refreshWorkspace(sessionId);
      },

    }),
    {
      name: 'yys-law-digital-human',
      partialize: (state) => ({
        sessionId: state.sessionId,
        voiceEnabled: state.voiceEnabled,
      }),
    },
  ),
);

// 语音播放器实例：所有音频播放统一经它排队（primary/fallback 明确区分），
// 回调把播放状态同步回 store，驱动头像与气泡按钮状态。
voicePlayer = new StreamingAudioPlayer({
  onSpeechStart: (chunk) => {
    useDigitalHumanStore.setState({ voiceSpeaking: true, voiceMode: chunk.ttsMode });
  },
  onSpeechEnd: () => {
    if (voicePlayer.queueLength === 0) {
      useDigitalHumanStore.setState({ voiceSpeaking: false, speakingMessageId: null });
    }
  },
  onSpeechCancelled: () => {
    useDigitalHumanStore.setState({ voiceSpeaking: false, speakingMessageId: null });
  },
});
