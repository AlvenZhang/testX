import { useState, useEffect } from 'react';
import { Table, Tag, Progress, message } from 'antd';
import { reportApi, testRunApi, projectApi } from '../services/api';
import type { Report, TestRun, Project } from '../types';

export function ReportsPage() {
  const [data, setData] = useState<Report[]>([]);
  const [loading, setLoading] = useState(false);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  const fetchProjects = async () => {
    const res = await projectApi.list();
    setProjects(res.data);
  };

  const fetchTestRuns = async () => {
    if (projects.length === 0) return;
    const runs = await Promise.all(projects.map(p => testRunApi.list(p.id)));
    setTestRuns(runs.flatMap(r => r.data));
  };

  const fetchData = async () => {
    if (testRuns.length === 0) return;
    setLoading(true);
    try {
      const reports = await Promise.all(testRuns.map(r => reportApi.list(r.id)));
      setData(reports.flatMap(r => r.data));
    } catch {
      message.error('获取报告列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);
  useEffect(() => { if (projects.length > 0) fetchTestRuns(); }, [projects]);
  useEffect(() => { if (testRuns.length > 0) fetchData(); }, [testRuns]);

  const getTestRunName = (id: string) => {
    const run = testRuns.find(r => r.id === id);
    if (!run) return id;
    const project = projects.find(p => p.id === run.project_id);
    return project?.name || id;
  };

  const columns = [
    { title: '测试运行', dataIndex: 'test_run_id', key: 'test_run_id', render: (v: string) => getTestRunName(v) },
    { title: '总用例', dataIndex: 'total_cases', key: 'total_cases' },
    { title: '通过', dataIndex: 'passed_cases', key: 'passed_cases', render: (v: number) => <Tag color="green">{v}</Tag> },
    { title: '失败', dataIndex: 'failed_cases', key: 'failed_cases', render: (v: number) => <Tag color={v > 0 ? 'red' : 'green'}>{v}</Tag> },
    {
      title: '通过率',
      key: 'pass_rate',
      render: (_: unknown, record: Report) => {
        const rate = record.total_cases > 0 ? (record.passed_cases / record.total_cases) * 100 : 0;
        return <Progress percent={Math.round(rate)} size="small" />;
      },
    },
    { title: '执行时长', dataIndex: 'duration_ms', key: 'duration_ms', render: (v: number) => `${v}ms` },
    { title: '报告类型', dataIndex: 'report_type', key: 'report_type', render: (v: string) => v === 'new_feature' ? '新功能' : '回归' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
  ];

  return <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />;
}
