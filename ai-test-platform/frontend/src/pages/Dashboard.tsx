import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag } from 'antd';
import { ProjectOutlined, FileTextOutlined, BugOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { projectApi, requirementApi, testCaseApi, testRunApi } from '../services/api';
import { TestTrendChart, PassRateChart } from '../components/Charts';
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

  // 生成测试趋势数据
  const trendData = generateTrendData(testRuns);

  // 最近测试运行
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
          <Card loading={loading}>
            <Card.Meta
              title="项目"
              description={projects.length}
              avatar={<ProjectOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Card.Meta
              title="需求"
              description={requirements.length}
              avatar={<FileTextOutlined style={{ fontSize: 24, color: '#52c41a' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Card.Meta
              title="测试用例"
              description={testCases.length}
              avatar={<BugOutlined style={{ fontSize: 24, color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Card.Meta
              title="测试运行"
              description={testRuns.length}
              avatar={<PlayCircleOutlined style={{ fontSize: 24, color: '#f5222d' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={12}>
          <PassRateChart
            passed={successRuns}
            failed={failedRuns}
            title="测试通过率"
          />
        </Col>
        <Col span={12}>
          <TestTrendChart
            data={trendData}
            title="测试趋势"
          />
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="最近测试运行" loading={loading}>
            <Table
              columns={runColumns}
              dataSource={recentRuns}
              rowKey="id"
              size="small"
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

// 生成测试趋势数据（基于最近7天的模拟数据）
function generateTrendData(testRuns: TestRun[]) {
  const days = 7;
  const data = [];
  const now = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    // 统计当天的测试运行
    const dayRuns = testRuns.filter(run => {
      const runDate = new Date(run.created_at).toISOString().split('T')[0];
      return runDate === dateStr;
    });

    const passed = dayRuns.filter(r => r.status === 'success').length;
    const failed = dayRuns.filter(r => r.status === 'failed').length;

    data.push({
      date: date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
      passed: passed,
      failed: failed,
      total: passed + failed,
    });
  }

  return data;
}
