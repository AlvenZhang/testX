import { useState, useEffect } from 'react';
import { Table, Tag, message } from 'antd';
import { testRunApi, projectApi } from '../services/api';
import type { TestRun, Project } from '../types';

const statusColors: Record<string, string> = {
  pending: 'default',
  running: 'processing',
  success: 'success',
  failed: 'error',
  cancelled: 'warning',
};

export function TestRunsPage() {
  const [data, setData] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]);

  const fetchProjects = async () => {
    const res = await projectApi.list();
    setProjects(res.data);
  };

  const fetchData = async () => {
    if (projects.length === 0) return;
    setLoading(true);
    try {
      const runs = await Promise.all(projects.map(p => testRunApi.list(p.id)));
      setData(runs.flatMap(r => r.data));
    } catch {
      message.error('获取运行记录失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);
  useEffect(() => { if (projects.length > 0) fetchData(); }, [projects]);

  const columns = [
    { title: '项目', dataIndex: 'project_id', key: 'project_id', render: (v: string) => projects.find(p => p.id === v)?.name || v },
    { title: '测试代码ID', dataIndex: 'test_code_id', key: 'test_code_id', ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={statusColors[v]}>{v}</Tag> },
    { title: '开始时间', dataIndex: 'started_at', key: 'started_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    { title: '完成时间', dataIndex: 'completed_at', key: 'completed_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    { title: '容器ID', dataIndex: 'container_id', key: 'container_id', ellipsis: true },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
  ];

  return <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />;
}
