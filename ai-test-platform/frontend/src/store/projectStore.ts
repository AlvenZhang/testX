import { create } from 'zustand';
import type { Project, Requirement } from '../types';

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  requirements: Requirement[];
  setProjects: (projects: Project[]) => void;
  setCurrentProject: (project: Project | null) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  deleteProject: (id: string) => void;
  setRequirements: (requirements: Requirement[]) => void;
  addRequirement: (requirement: Requirement) => void;
  updateRequirement: (id: string, updates: Partial<Requirement>) => void;
  deleteRequirement: (id: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: [],
  currentProject: null,
  requirements: [],

  setProjects: (projects: Project[]) => set({ projects }),

  setCurrentProject: (project: Project | null) => set({ currentProject: project }),

  addProject: (project: Project) =>
    set((state) => ({ projects: [...state.projects, project] })),

  updateProject: (id: string, updates: Partial<Project>) =>
    set((state) => ({
      projects: state.projects.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
      currentProject:
        state.currentProject?.id === id
          ? { ...state.currentProject, ...updates }
          : state.currentProject,
    })),

  deleteProject: (id: string) =>
    set((state) => ({
      projects: state.projects.filter((p) => p.id !== id),
      currentProject:
        state.currentProject?.id === id ? null : state.currentProject,
    })),

  setRequirements: (requirements: Requirement[]) => set({ requirements }),

  addRequirement: (requirement: Requirement) =>
    set((state) => ({ requirements: [...state.requirements, requirement] })),

  updateRequirement: (id: string, updates: Partial<Requirement>) =>
    set((state) => ({
      requirements: state.requirements.map((r) =>
        r.id === id ? { ...r, ...updates } : r
      ),
    })),

  deleteRequirement: (id: string) =>
    set((state) => ({
      requirements: state.requirements.filter((r) => r.id !== id),
    })),
}));
