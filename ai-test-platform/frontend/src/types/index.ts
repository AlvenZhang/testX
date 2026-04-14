export interface Project {
  id: string;
  name: string;
  description?: string;
  git_url?: string;
  config?: {
    test_types?: string[];
    default_framework?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface Requirement {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'cases_generated' | 'code_generated' | 'tested';
  version: number;
  extra?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TestCase {
  id: string;
  requirement_id: string;
  case_id: string;
  title: string;
  steps?: string;
  expected_result?: string;
  priority: 'low' | 'medium' | 'high';
  status: 'active' | 'deprecated';
  created_at: string;
  updated_at: string;
}

export interface TestPlan {
  id: string;
  requirement_id: string;
  test_scope?: string;
  test_types?: string[];
  test_strategy?: string;
  risk_points?: string;
  created_at: string;
}

export interface TestRun {
  id: string;
  project_id: string;
  test_code_id: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  started_at?: string;
  completed_at?: string;
  container_id?: string;
  created_at: string;
}

export interface Report {
  id: string;
  test_run_id: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  duration_ms: number;
  report_type: 'new_feature' | 'regression';
  report_data?: Record<string, unknown>;
  log_content?: string;
  screenshots?: string[];
  created_at: string;
}
