/**
 * 测试相关类型定义
 */

/**
 * 测试类型
 */
export type TestType = 'api' | 'web' | 'mobile' | 'unit' | 'integration';

/**
 * 测试平台
 */
export type TestPlatform = 'android' | 'ios' | 'web' | 'api';

/**
 * 测试框架
 */
export type TestFramework = 'pytest' | 'unittest' | 'playwright' | 'selenium' | 'appium' | 'jest';

/**
 * 测试用例优先级
 */
export type TestPriority = 'critical' | 'high' | 'medium' | 'low';

/**
 * 测试用例状态
 */
export type TestCaseStatus = 'active' | 'inactive' | 'deprecated';

/**
 * 测试执行状态
 */
export type TestRunStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled';

/**
 * 测试步骤
 */
export interface TestStep {
  order: number;
  action: string;
  expected: string;
}

/**
 * 测试用例创建
 */
export interface TestCaseCreate {
  title: string;
  test_type: TestType;
  priority?: TestPriority;
  preconditions?: string;
  steps?: string;
  expected_result?: string;
  test_data?: Record<string, any>;
}

/**
 * 测试用例更新
 */
export interface TestCaseUpdate {
  title?: string;
  test_type?: TestType;
  priority?: TestPriority;
  status?: TestCaseStatus;
  preconditions?: string;
  steps?: string;
  expected_result?: string;
  test_data?: Record<string, any>;
}

/**
 * 测试用例
 */
export interface TestCase {
  id: string;
  project_id: string;
  requirement_id?: string;
  title: string;
  test_type: TestType;
  priority: TestPriority;
  status: TestCaseStatus;
  preconditions?: string;
  steps?: string;
  expected_result?: string;
  test_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * 测试代码创建
 */
export interface TestCodeCreate {
  name: string;
  test_type: TestType;
  framework?: TestFramework;
  platform?: TestPlatform;
  code_content: string;
  test_case_ids?: string[];
}

/**
 * 测试代码更新
 */
export interface TestCodeUpdate {
  name?: string;
  framework?: TestFramework;
  platform?: TestPlatform;
  code_content?: string;
  status?: 'draft' | 'active' | 'deprecated';
}

/**
 * 测试代码
 */
export interface TestCode {
  id: string;
  project_id: string;
  requirement_id?: string;
  name: string;
  test_type: TestType;
  framework: TestFramework;
  platform: TestPlatform;
  code_content: string;
  test_case_ids?: string[];
  status: 'draft' | 'active' | 'deprecated';
  pass_count?: number;
  fail_count?: number;
  last_run_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 测试方案创建
 */
export interface TestPlanCreate {
  name: string;
  description?: string;
  test_type: TestType;
  test_case_ids: string[];
  device_ids?: string[];
}

/**
 * 测试方案
 */
export interface TestPlan {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  test_type: TestType;
  test_case_ids: string[];
  device_ids?: string[];
  status: 'draft' | 'active' | 'completed';
  created_at: string;
  updated_at: string;
}

/**
 * 测试执行创建
 */
export interface TestRunCreate {
  test_code_id?: string;
  test_plan_id?: string;
  device_id?: string;
  platform?: TestPlatform;
  config?: Record<string, any>;
}

/**
 * 测试执行
 */
export interface TestRun {
  id: string;
  project_id: string;
  test_code_id?: string;
  test_plan_id?: string;
  device_id?: string;
  platform?: TestPlatform;
  test_type?: TestType;
  status: TestRunStatus;
  config?: Record<string, any>;
  total_cases?: number;
  passed_cases?: number;
  failed_cases?: number;
  skipped_cases?: number;
  duration?: number;
  logs?: string;
  error_message?: string;
  screenshots?: string[];
  created_at: string;
  updated_at: string;
}
