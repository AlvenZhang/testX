/**
 * AI 服务封装
 * 提供 AI 对话、需求分析、测试生成等功能
 */
import { aiApi } from './api';

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface AnalysisResult {
  test_points: string[];
  risk_points: string[];
  suggested_test_types: string[];
}

export interface TestCaseGenerated {
  case_id: string;
  title: string;
  steps?: string;
  expected_result?: string;
  priority?: string;
}

class AIService {
  /**
   * AI 对话
   */
  async chat(messages: ChatMessage[]): Promise<string> {
    const res = await aiApi.chat({ messages });
    return res.data;
  }

  /**
   * 分析需求
   */
  async analyzeRequirement(requirementId: string): Promise<AnalysisResult> {
    const res = await aiApi.analyzeRequirement({ requirement_id: requirementId });
    return res.data;
  }

  /**
   * 生成测试用例
   */
  async generateTestCases(requirementId: string): Promise<TestCaseGenerated[]> {
    const res = await aiApi.generateTestCases({ requirement_id: requirementId });
    return res.data;
  }

  /**
   * 生成测试代码
   */
  async generateTestCode(
    requirementId: string,
    testCases: TestCaseGenerated[]
  ): Promise<string> {
    const res = await aiApi.generateTestCode({
      requirement_id: requirementId,
      test_cases: testCases,
    });
    return res.data;
  }

  /**
   * 分析代码影响
   */
  async analyzeCodeImpact(codeChanges: Array<{ file: string; diff: string }>): Promise<string[]> {
    const res = await aiApi.analyzeCodeImpact({
      code_changes: codeChanges,
    });
    return res.data;
  }

  /**
   * 修复测试代码
   */
  async fixTestCode(
    failedCode: string,
    errorMessage: string,
    testType: 'api' | 'web' | 'mobile' = 'api'
  ): Promise<{ fixed_code: string; explanation: string }> {
    const res = await aiApi.fixTestCode({
      failed_code: failedCode,
      error_message: errorMessage,
      test_type: testType,
    });
    return res.data;
  }
}

export const aiService = new AIService();
export default aiService;
