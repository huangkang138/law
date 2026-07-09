/**
 * YYS-Law Contract Review History Store
 * 使用 Zustand + Persist 中间件实现合同审查历史的持久化
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface ContractReviewSession {
  id: string;
  filename: string;
  customFilename?: string;
  isPinned: boolean;
  createdAt: number;
  updatedAt: number;
  contractId?: string;
  reviewResult?: any;
}

interface ContractStore {
  sessions: ContractReviewSession[];
  currentSessionId: string | null;
  
  // Actions
  createSession: (filename: string, contractId?: string) => string;
  deleteSession: (id: string) => void;
  renameSession: (id: string, customFilename: string) => void;
  togglePin: (id: string) => void;
  setCurrentSession: (id: string) => void;
  setReviewResult: (id: string, reviewResult: any) => void;
  getSortedSessions: () => ContractReviewSession[];
}

export const useContractStore = create<ContractStore>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,

      createSession: (filename: string, contractId?: string) => {
        const newSession: ContractReviewSession = {
          id: `contract_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          filename,
          contractId,
          isPinned: false,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };

        set((state) => ({
          sessions: [...state.sessions, newSession],
          currentSessionId: newSession.id,
        }));

        return newSession.id;
      },

      deleteSession: (id: string) => {
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== id),
          currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
        }));
      },

      renameSession: (id: string, customFilename: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id
              ? { ...s, customFilename, updatedAt: Date.now() }
              : s
          ),
        }));
      },

      togglePin: (id: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id
              ? { ...s, isPinned: !s.isPinned, updatedAt: Date.now() }
              : s
          ),
        }));
      },

      setCurrentSession: (id: string) => {
        set({ currentSessionId: id });
      },

      setReviewResult: (id: string, reviewResult: any) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id
              ? { ...s, reviewResult, updatedAt: Date.now() }
              : s
          ),
        }));
      },

      getSortedSessions: () => {
        const { sessions } = get();
        
        const pinned = sessions.filter((s) => s.isPinned);
        const unpinned = sessions.filter((s) => !s.isPinned);
        
        const sortByUpdated = (a: ContractReviewSession, b: ContractReviewSession) => b.updatedAt - a.updatedAt;
        
        return [
          ...pinned.sort(sortByUpdated),
          ...unpinned.sort(sortByUpdated),
        ];
      },
    }),
    {
      name: 'sparklaw-contract-storage',
      version: 1,
    }
  )
);
