import { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag } from 'antd';
import { ProjectOutlined, FileTextOutlined, BugOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { projectApi, requirementApi, testCaseApi, testRunApi } from '../services/api';
import type { Project, Requirement, TestCase, TestRun } from '../types';

export function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [p, r, tr] = await Promise.all([
          projectApi.list(),
          Promise.all((await projectApi.list()).data.map((p: Project) => requirementApi.list(p.id))),
          Promise.all((await projectApi.list()).data.map((p: Project) => testRunApi.list(p.id))),
        ]);
        setProjects(p.data);
        setRequirements(r.flatMap((res: { data: Requirement[] }) => res.data));
        setTestRuns(tr.flatMap((res: { data: TestRun[] }) => res.data));

        // Fetch test cases
        const cases = await Promise.all(r.flatMap((res: { data: Requirement[] }) =>
          res.data.map((req: Requirement) => testCaseApi.list(req.id))
        ));
        setTestCases(cases.flatMap((c: { data: TestCase[] }) => c.data));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const successRuns = testRuns.filter(r => r.status === 'success').length;
  const failedRuns = testRuns.filter(r => r.status === 'failed').length;

  const recentRuns = testRuns
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5);

  const runColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', render: (v: string) => v.slice(0, 8) + '...' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={v === 'success' ? 'green' : v === 'failed' ? 'red' : v === 'running' ? 'blue' : 'default'}>
          {v}
        </Tag>
      ),
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
  ];

  return (
    <div>
      <Row gutter={16}>
        <Col span={6}>
          <Card>
            <Statistic
              title="项目"
              value={projects.length}
              prefix={<ProjectOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="需求"
              value={requirements.length}
              prefix={<FileTextOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="测试用例"
              value={testCases.length}
              prefix={<BugOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="测试运行"
              value={testRuns.length}
              prefix={<PlayCircleOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <Card title="通过率">
            <Statistic
              value={testRuns.length > 0 ? (successRuns / testRuns.length * 100).toFixed(1) : 0}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
            <p>成功: {successRuns} | 失败: {failedRuns}</p>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="最近测试运行">
            <Table columns={runColumns} dataSource={recentRuns} rowKey="id" size="small" pagination={false} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
