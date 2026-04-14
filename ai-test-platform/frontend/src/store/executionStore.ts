import { create } from 'zustand';

export interface ExecutionLog {
  id: string;
  timestamp: number;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning';
}

export interface Execution {
  id: string;
  testCodeId: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  startTime?: number;
  endTime?: number;
  duration?: number;
  exitCode?: number;
  logs: ExecutionLog[];
}

interface ExecutionState {
  executions: Record<string, Execution>;
  currentExecution: Execution | null;
  setExecution: (execution: Execution) => void;
  updateExecution: (id: string, updates: Partial<Execution>) => void;
  addLog: (executionId: string, log: Omit<ExecutionLog, 'id'>) => void;
  clearExecution: (id: string) => void;
  clearAll: () => void;
  setCurrentExecution: (execution: Execution | null) => void;
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  executions: {},
  currentExecution: null,

  setExecution: (execution: Execution) =>
    set((state) => ({
      executions: { ...state.executions, [execution.id]: execution },
    })),

  updateExecution: (id: string, updates: Partial<Execution>) =>
    set((state) => {
      const existing = state.executions[id];
      if (!existing) return state;
      return {
        executions: {
          ...state.executions,
          [id]: { ...existing, ...updates },
        },
      };
    }),

  addLog: (executionId: string, log: Omit<ExecutionLog, 'id'>) =>
    set((state) => {
      const execution = state.executions[executionId];
      if (!execution) return state;
      const newLog: ExecutionLog = {
        ...log,
        id: `${executionId}-${Date.now()}`,
      };
      return {
        executions: {
          ...state.executions,
          [executionId]: {
            ...execution,
            logs: [...execution.logs, newLog],
          },
        },
      };
    }),

  clearExecution: (id: string) =>
    set((state) => {
      const { [id]: _, ...rest } = state.executions;
      return {
        executions: rest,
        currentExecution:
          state.currentExecution?.id === id ? null : state.currentExecution,
      };
    }),

  clearAll: () => set({ executions: {}, currentExecution: null }),

  setCurrentExecution: (execution: Execution | null) =>
    set({ currentExecution: execution }),
}));
