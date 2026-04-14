import axios from 'axios';
import type { Project, Requirement, TestCase, TestPlan, TestRun, Report } from '../types';

const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Projects
export const projectApi = {
  list: () => api.get<Project[]>('/projects/'),
  get: (id: string) => api.get<Project>(`/projects/${id}`),
  create: (data: Partial<Project>) => api.post<Project>('/projects/', data),
  update: (id: string, data: Partial<Project>) => api.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
};

// Requirements
export const requirementApi = {
  list: (projectId: string) => api.get<Requirement[]>(`/requirements/?project_id=${projectId}`),
  get: (id: string) => api.get<Requirement>(`/requirements/${id}`),
  create: (data: Partial<Requirement>) => api.post<Requirement>('/requirements/', data),
  update: (id: string, data: Partial<Requirement>) => api.put<Requirement>(`/requirements/${id}`, data),
  delete: (id: string) => api.delete(`/requirements/${id}`),
  getVersions: (id: string) => api.get(`/requirements/${id}/versions`),
};

// Test Cases
export const testCaseApi = {
  list: (requirementId: string) => api.get<TestCase[]>(`/test-cases/?requirement_id=${requirementId}`),
  get: (id: string) => api.get<TestCase>(`/test-cases/${id}`),
  create: (data: Partial<TestCase>) => api.post<TestCase>('/test-cases/', data),
  update: (id: string, data: Partial<TestCase>) => api.put<TestCase>(`/test-cases/${id}`, data),
  delete: (id: string) => api.delete(`/test-cases/${id}`),
};

// Test Plans
export const testPlanApi = {
  list: (requirementId: string) => api.get<TestPlan[]>(`/test-plans/?requirement_id=${requirementId}`),
  get: (id: string) => api.get<TestPlan>(`/test-plans/${id}`),
  create: (data: Partial<TestPlan>) => api.post<TestPlan>('/test-plans/', data),
  update: (id: string, data: Partial<TestPlan>) => api.put<TestPlan>(`/test-plans/${id}`, data),
  delete: (id: string) => api.delete(`/test-plans/${id}`),
};

// Test Runs
export const testRunApi = {
  list: (projectId: string) => api.get<TestRun[]>(`/test-runs/?project_id=${projectId}`),
  get: (id: string) => api.get<TestRun>(`/test-runs/${id}`),
  create: (data: Partial<TestRun>) => api.post<TestRun>('/test-runs/', data),
  update: (id: string, data: Partial<TestRun>) => api.put<TestRun>(`/test-runs/${id}`, data),
  delete: (id: string) => api.delete(`/test-runs/${id}`),
};

// Reports
export const reportApi = {
  list: (testRunId: string) => api.get<Report[]>(`/reports/?test_run_id=${testRunId}`),
  get: (id: string) => api.get<Report>(`/reports/${id}`),
  create: (data: Partial<Report>) => api.post<Report>('/reports/', data),
  update: (id: string, data: Partial<Report>) => api.put<Report>(`/reports/${id}`, data),
  delete: (id: string) => api.delete(`/reports/${id}`),
};

// Workflows
export const workflowApi = {
  generateTests: (requirementId: string) =>
    api.post<{
      requirement_id: string;
      analysis: { test_points: string[]; risk_points: string[]; suggested_test_types: string[] };
      test_cases: Array<{ case_id: string; title: string; priority: string }>;
      test_code_id: string;
      test_code_preview: string;
    }>(`/workflows/generate-tests/${requirementId}`),
};

export default api;
