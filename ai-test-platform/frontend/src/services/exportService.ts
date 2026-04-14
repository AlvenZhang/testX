/**
 * 导出服务
 * 提供测试报告、用例等导出功能
 */
import type { Report, TestCase } from '../types';

export type ExportFormat = 'json' | 'csv' | 'excel' | 'html' | 'markdown';

class ExportService {
  /**
   * 导出测试报告
   */
  async exportReport(report: Report, format: ExportFormat = 'json'): Promise<Blob> {
    switch (format) {
      case 'json':
        return this.exportAsJson(report);

      case 'csv':
        return this.exportReportAsCsv(report);

      case 'html':
        return this.exportReportAsHtml(report);

      case 'markdown':
        return this.exportReportAsMarkdown(report);

      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * 导出测试用例
   */
  async exportTestCases(
    testCases: TestCase[],
    format: ExportFormat = 'csv'
  ): Promise<Blob> {
    switch (format) {
      case 'json':
        return this.exportAsJson(testCases);

      case 'csv':
        return this.exportTestCasesAsCsv(testCases);

      case 'markdown':
        return this.exportTestCasesAsMarkdown(testCases);

      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * 下载文件
   */
  downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ==================== Private Methods ====================

  private exportAsJson(data: unknown): Blob {
    const json = JSON.stringify(data, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  private exportReportAsCsv(report: Report): Blob {
    const rows = [
      ['Test Report'],
      ['ID', report.id],
      ['Test Run ID', report.test_run_id],
      ['Total Cases', report.total_cases.toString()],
      ['Passed Cases', report.passed_cases.toString()],
      ['Failed Cases', report.failed_cases.toString()],
      ['Duration (ms)', report.duration_ms.toString()],
      ['Report Type', report.report_type],
      ['Created At', report.created_at],
      [],
      ['Log Content:'],
      [report.log_content || ''],
    ];

    const csv = rows.map((r) => r.join(',')).join('\n');
    return new Blob([csv], { type: 'text/csv;charset=utf-8' });
  }

  private exportReportAsHtml(report: Report): Blob {
    const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Test Report - ${report.id}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #333; }
    .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
    .passed { color: #52c41a; }
    .failed { color: #ff4d4f; }
    pre { background: #f5f5f5; padding: 10px; overflow: auto; }
  </style>
</head>
<body>
  <h1>Test Report</h1>
  <div class="summary">
    <p><strong>ID:</strong> ${report.id}</p>
    <p><strong>Total:</strong> ${report.total_cases}</p>
    <p><strong class="passed">Passed:</strong> ${report.passed_cases}</p>
    <p><strong class="failed">Failed:</strong> ${report.failed_cases}</p>
    <p><strong>Duration:</strong> ${report.duration_ms}ms</p>
    <p><strong>Type:</strong> ${report.report_type}</p>
  </div>
  <h2>Logs</h2>
  <pre>${report.log_content || 'No logs'}</pre>
</body>
</html>
    `.trim();

    return new Blob([html], { type: 'text/html' });
  }

  private exportReportAsMarkdown(report: Report): Blob {
    const passRate = report.total_cases > 0
      ? ((report.passed_cases / report.total_cases) * 100).toFixed(1)
      : 0;

    const markdown = `
# Test Report

## Summary

| Field | Value |
|-------|-------|
| ID | ${report.id} |
| Total | ${report.total_cases} |
| Passed | ${report.passed_cases} |
| Failed | ${report.failed_cases} |
| Pass Rate | ${passRate}% |
| Duration | ${report.duration_ms}ms |
| Type | ${report.report_type} |
| Created | ${report.created_at} |

## Logs

\`\`\`
${report.log_content || 'No logs'}
\`\`\`
    `.trim();

    return new Blob([markdown], { type: 'text/markdown' });
  }

  private exportTestCasesAsCsv(testCases: TestCase[]): Blob {
    const headers = ['ID', 'Case ID', 'Title', 'Steps', 'Expected Result', 'Priority', 'Status'];
    const rows = testCases.map((tc) => [
      tc.id,
      tc.case_id,
      `"${(tc.title || '').replace(/"/g, '""')}"`,
      `"${(tc.steps || '').replace(/"/g, '""')}"`,
      `"${(tc.expected_result || '').replace(/"/g, '""')}"`,
      tc.priority,
      tc.status,
    ]);

    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    return new Blob([csv], { type: 'text/csv;charset=utf-8' });
  }

  private exportTestCasesAsMarkdown(testCases: TestCase[]): Blob {
    const rows = testCases.map((tc) =>
      `| ${tc.case_id} | ${tc.title} | ${tc.priority} | ${tc.status} |`
    );

    const markdown = `
# Test Cases

| Case ID | Title | Priority | Status |
|---------|-------|----------|--------|
${rows.join('\n')}
    `.trim();

    return new Blob([markdown], { type: 'text/markdown' });
  }
}

export const exportService = new ExportService();
export default exportService;
