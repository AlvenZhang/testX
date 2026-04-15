import axios from 'axios';
import type { Project, Requirement, TestCase, TestPlan, TestRun, Report, Device, MobileExecutionResult, CodeChange } from '../types';

// 项目成员类型
export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: 'viewer' | 'editor' | 'executor' | 'admin';
  created_at: string;
  updated_at: string;
}

// 影响分析类型
export interface ImpactAnalysis {
  affected_requirements: string[];
  new_test_cases_needed: string[];
  tests_to_modify: string[];
  impact_level: 'high' | 'medium' | 'low';
  reason: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post<{ access_token: string; user: { id: string; email: string; name: string } }>('/auth/login', { email, password }),
  register: (email: string, name: string, password: string) =>
    api.post<{ access_token: string; user: { id: string; email: string; name: string } }>('/auth/register', { email, name, password }),
};

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
  list: (projectId?: string, requirementId?: string) => {
    let url = '/test-runs/?';
    if (projectId) url += `project_id=${projectId}&`;
    if (requirementId) url += `requirement_id=${requirementId}&`;
    return api.get<TestRun[]>(url);
  },
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
  generateTestsStream: (requirementId: string) => {
    const token = localStorage.getItem('token');
    return fetch(`${API_BASE}/workflows/generate-tests-stream/${requirementId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  },
};

// Test Code
export const testCodeApi = {
  list: (projectId: string) => api.get<Array<{ id: string; project_id: string; requirement_id: string; framework: string; code_content: string; status: string; created_at: string }>>(`/test-code/?project_id=${projectId}`),
  get: (id: string) => api.get(`/test-code/${id}`),
  listByRequirement: (requirementId: string) => api.get(`/test-code/?requirement_id=${requirementId}`),
};

// Executions
export const executionApi = {
  run: (testCodeId: string) =>
    api.post<{
      run_id: string;
      status: string;
      exit_code: number;
      logs: string;
      duration_ms: number;
    }>(`/executions/run/${testCodeId}`),
  runStream: (testCodeId: string) => {
    const token = localStorage.getItem('token');
    return fetch(`${API_BASE}/executions/run-stream/${testCodeId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  },
};

// Mobile Executions
export const mobileExecutionApi = {
  run: (data: {
    code_content: string;
    device_id: string;
    platform: 'android' | 'ios';
    test_type?: string;
  }) =>
    api.post<MobileExecutionResult>('/mobile-executions/run', data),

  listDevices: (platform?: 'android' | 'ios') =>
    api.get<{ devices: Device[]; total: number }>('/mobile-executions/devices', {
      params: platform ? { platform } : {},
    }),

  getStatus: (runId: string) =>
    api.get<{ run_id: string; status: string; message?: string }>(`/mobile-executions/status/${runId}`),

  getLogs: (runId: string) =>
    api.get<{ run_id: string; logs: string }>(`/mobile-executions/logs/${runId}`),
};

// AI
export const aiApi = {
  chat: (data: { messages: Array<{ role: string; content: string }> }) =>
    api.post<string>('/ai/chat', data),

  analyzeRequirement: (data: { requirement_id: string }) =>
    api.post<{ test_points: string[]; risk_points: string[]; suggested_test_types: string[] }>('/ai/analyze-requirement', data),

  generateTestCases: (data: { requirement_id: string }) =>
    api.post<Array<{ case_id: string; title: string; steps?: string; expected_result?: string; priority?: string }>>('/ai/generate-test-cases', data),

  generateTestCode: (data: { requirement_id: string; test_cases: Array<{ case_id: string; title: string }> }) =>
    api.post<string>('/ai/generate-test-code', data),

  analyzeCodeImpact: (data: { code_changes: Array<{ file: string; diff: string }> }) =>
    api.post<string[]>('/ai/analyze-code-impact', data),

  fixTestCode: (data: { failed_code: string; error_message: string; test_type: string }) =>
    api.post<{ fixed_code: string; explanation: string }>('/ai/fix-test-code', data),
};

// Devices
export const deviceApi = {
  list: (platform?: 'android' | 'ios') =>
    api.get<Device[]>('/devices/', { params: platform ? { platform } : {} }),
  discover: (platform: 'android' | 'ios') =>
    api.post<{ discovered_count: number; saved_count: number; devices: Device[] }>('/devices/discover', null, { params: { platform } }),
  getScreenshot: (deviceId: string) =>
    api.get<{ device_id: string; screenshot: string }>(`/devices/${deviceId}/screenshot`),
  delete: (deviceId: string) => api.delete(`/devices/${deviceId}`),
};

// Code Changes
export const codeChangeApi = {
  list: (requirementId: string, skip = 0, limit = 100) =>
    api.get<CodeChange[]>('/code-changes/', { params: { requirement_id: requirementId, skip, limit } }),
  get: (id: string) => api.get<CodeChange>(`/code-changes/${id}`),
  create: (data: Partial<CodeChange>) => api.post<CodeChange>('/code-changes/', data),
  delete: (id: string) => api.delete(`/code-changes/${id}`),
};

// 项目成员类型
export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  role: 'viewer' | 'editor' | 'executor' | 'admin';
  created_at: string;
  updated_at: string;
}

// 影响分析类型
export interface ImpactAnalysis {
  affected_requirements: string[];
  new_test_cases_needed: string[];
  tests_to_modify: string[];
  impact_level: 'high' | 'medium' | 'low';
  reason: string;
}

// Project Members
export const projectMemberApi = {
  list: (projectId: string) => api.get<ProjectMember[]>(`/project-members/project/${projectId}`),
  add: (data: { project_id: string; user_id: string; role: string }) =>
    api.post<ProjectMember>('/project-members/', data),
  update: (memberId: string, role: string) =>
    api.put<ProjectMember>(`/project-members/${memberId}`, { role }),
  delete: (memberId: string) => api.delete(`/project-members/${memberId}`),
};

// Impact Analysis
export const impactAnalysisApi = {
  analyzeRequirement: (requirementId: string) =>
    api.post<{ requirement_id: string; analysis: ImpactAnalysis }>(
      `/impact-analysis/requirement/${requirementId}`
    ),
  suggestRegression: (projectId: string, changedFiles: string[]) =>
    api.post<{ project_id: string; changed_files: string[]; suggested_test_codes: string[] }>(
      '/impact-analysis/regression-suggest',
      changedFiles,
      { params: { project_id: projectId } }
    ),
};

// Exports
export const exportApi = {
  reportCsv: (reportId: string) =>
    api.get(`/exports/report/${reportId}/csv`, { responseType: 'blob' }),
  testCasesCsv: (projectId: string) =>
    api.get(`/exports/test-cases/${projectId}/csv`, { responseType: 'blob' }),
};

export default api;
