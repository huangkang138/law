import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface DisputeSession {
  id: string;
  title: string;
  customTitle?: string;
  isPinned: boolean;
  createdAt: number;
  updatedAt: number;
  disputeId?: string;
  organizedData?: any;
  inputType?: string;
}

interface DisputeStore {
  sessions: DisputeSession[];
  currentSessionId: string | null;
  
  createSession: (title: string, disputeId?: string) => string;
  deleteSession: (id: string) => void;
  renameSession: (id: string, customTitle: string) => void;
  togglePin: (id: string) => void;
  setCurrentSession: (id: string | null) => void;
  setOrganizedData: (id: string, organizedData: any) => void;
  getSortedSessions: () => DisputeSession[];
}

export const useDisputeStore = create<DisputeStore>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,
      
      createSession: (title: string, disputeId?: string) => {
        const id = `dispute_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const now = Date.now();
        set((state) => ({
          sessions: [
            {
              id,
              title,
              isPinned: false,
              createdAt: now,
              updatedAt: now,
              disputeId,
            },
            ...state.sessions,
          ],
          currentSessionId: id,
        }));
        return id;
      },
      
      deleteSession: (id: string) => {
        set((state) => ({
          sessions: state.sessions.filter((s) => s.id !== id),
          currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
        }));
      },
      
      renameSession: (id: string, customTitle: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, customTitle, updatedAt: Date.now() } : s
          ),
        }));
      },
      
      togglePin: (id: string) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, isPinned: !s.isPinned, updatedAt: Date.now() } : s
          ),
        }));
      },
      
      setCurrentSession: (id: string | null) => {
        set({ currentSessionId: id });
      },
      
      setOrganizedData: (id: string, organizedData: any) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, organizedData, updatedAt: Date.now() } : s
          ),
        }));
      },
      
      getSortedSessions: () => {
        const { sessions } = get();
        return [...sessions].sort((a, b) => {
          if (a.isPinned && !b.isPinned) return -1;
          if (!a.isPinned && b.isPinned) return 1;
          return b.updatedAt - a.updatedAt;
        });
      },
    }),
    {
      name: 'dispute-sessions',
    }
  )
);
