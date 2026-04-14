import { useState, useEffect } from 'react';
import { Table, Button, message, Space, Tag, Drawer } from 'antd';
import { PlayCircleOutlined, CodeOutlined } from '@ant-design/icons';
import { testCodeApi, projectApi, executionApi } from '../services/api';
import type { Project } from '../types';

interface TestCodeItem {
  id: string;
  project_id: string;
  requirement_id?: string;
  framework: string;
  code_content: string;
  status: string;
  created_at: string;
}

export function TestCodePage() {
  const [data, setData] = useState<TestCodeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [codeContent, setCodeContent] = useState('');
  const [logVisible, setLogVisible] = useState(false);
  const [execResult, setExecResult] = useState<{ logs: string; status: string; duration_ms: number } | null>(null);

  const fetchProjects = async () => {
    const res = await projectApi.list();
    setProjects(res.data);
  };

  const fetchData = async () => {
    if (projects.length === 0) return;
    setLoading(true);
    try {
      const codes = await Promise.all(projects.map(p => testCodeApi.list(p.id)));
      setData(codes.flatMap(c => c.data));
    } catch {
      message.error('获取测试代码失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);
  useEffect(() => { if (projects.length > 0) fetchData(); }, [projects]);

  const handleRun = async (id: string) => {
    setRunning(id);
    try {
      const res = await executionApi.run(id);
      setExecResult(res.data);
      setLogVisible(true);
      message.success('执行完成');
    } catch (err: unknown) {
      message.error((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '执行失败');
    } finally {
      setRunning(null);
    }
  };

  const handleViewCode = async (id: string) => {
    const res = await testCodeApi.get(id);
    setCodeContent(res.data.code_content);
    setSelectedCode(id);
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', render: (v: string) => v.slice(0, 8) + '...' },
    { title: '框架', dataIndex: 'framework', key: 'framework' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={v === 'active' ? 'green' : 'red'}>{v}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: TestCodeItem) => (
        <Space>
          <Button size="small" type="primary" icon={<PlayCircleOutlined />} loading={running === record.id} onClick={() => handleRun(record.id)}>
            执行
          </Button>
          <Button size="small" icon={<CodeOutlined />} onClick={() => handleViewCode(record.id)}>
            查看代码
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />

      {/* 代码查看抽屉 */}
      <Drawer title="测试代码" open={!!selectedCode} onClose={() => setSelectedCode(null)} width={700}>
        <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
          {codeContent}
        </pre>
      </Drawer>

      {/* 执行日志抽屉 */}
      <Drawer title="执行结果" open={logVisible} onClose={() => setLogVisible(false)} width={700}>
        {execResult && (
          <div>
            <p><Tag color={execResult.status === 'success' ? 'green' : 'red'}>状态: {execResult.status}</Tag> 耗时: {execResult.duration_ms}ms</p>
            <h4>日志:</h4>
            <pre style={{ fontSize: 11, background: '#f5f5f5', padding: 16, maxHeight: 400, overflow: 'auto' }}>
              {execResult.logs || '无日志输出'}
            </pre>
          </div>
        )}
      </Drawer>
    </div>
  );
}
