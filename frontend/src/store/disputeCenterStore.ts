import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface DisputeCenterSession {
  id: string;
  title: string;
  customTitle?: string;
  isPinned: boolean;
  createdAt: number;
  updatedAt: number;
  disputeId?: string;
  currentStep?: number;
  organizedData?: any;
  evidenceData?: any;
  protectionData?: any;
  documentData?: any;
  predictionData?: any;
  reminderData?: any;
  warningData?: any;
}

interface DisputeCenterStore {
  sessions: DisputeCenterSession[];
  currentSessionId: string | null;
  
  createSession: (title: string, disputeId?: string) => string;
  deleteSession: (id: string) => void;
  renameSession: (id: string, customTitle: string) => void;
  togglePin: (id: string) => void;
  setCurrentSession: (id: string | null) => void;
  updateSessionData: (id: string, data: Partial<DisputeCenterSession>) => void;
  getSortedSessions: () => DisputeCenterSession[];
}

export const useDisputeCenterStore = create<DisputeCenterStore>()(
  persist(
    (set, get) => ({
      sessions: [],
      currentSessionId: null,
      
      createSession: (title: string, disputeId?: string) => {
        const id = `dispute_center_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
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
              currentStep: 0,
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
      
      updateSessionData: (id: string, data: Partial<DisputeCenterSession>) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === id ? { ...s, ...data, updatedAt: Date.now() } : s
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
      name: 'dispute-center-sessions',
    }
  )
);
