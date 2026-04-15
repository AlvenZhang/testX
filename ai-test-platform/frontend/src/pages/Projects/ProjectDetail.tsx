import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Tabs, Table, Tag, Spin, message } from 'antd';
import { ArrowLeftOutlined, EditOutlined, TeamOutlined, SettingOutlined } from '@ant-design/icons';
import { projectApi, requirementApi, testCaseApi, testCodeApi } from '../../services/api';
import type { Project, Requirement, TestCase, TestCode } from '../../types';

const { TabPane } = Tabs;

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [testCodes, setTestCodes] = useState<TestCode[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetchData();
    }
  }, [id]);

  const fetchData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [projectRes, reqRes, caseRes, codeRes] = await Promise.all([
        projectApi.get(id),
        requirementApi.list({ project_id: id }),
        testCaseApi.list({ project_id: id }),
        testCodeApi.list({ project_id: id }),
      ]);
      setProject(projectRes.data);
      setRequirements(reqRes.data || []);
      setTestCases(caseRes.data || []);
      setTestCodes(codeRes.data || []);
    } catch {
      message.error('获取项目详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" />;
  if (!project) return <div>项目不存在</div>;

  const requirementColumns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag>{s}</Tag> },
    { title: '优先级', dataIndex: 'priority', key: 'priority', render: (p: string) => <Tag color={p === 'high' ? 'red' : 'blue'}>{p}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
  ];

  const testCaseColumns = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '类型', dataIndex: 'test_type', key: 'test_type' },
    { title: '优先级', dataIndex: 'priority', key: 'priority' },
    { title: '状态', dataIndex: 'status', key: 'status' },
  ];

  const testCodeColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '框架', dataIndex: 'framework', key: 'framework' },
    { title: '平台', dataIndex: 'platform', key: 'platform' },
    { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
  ];

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card
        title={<Space><SettingOutlined /> {project.name}</Space>}
        extra={
          <Button icon={<EditOutlined />} onClick={() => navigate(`/projects/${id}/edit`)}>
            编辑
          </Button>
        }
      >
        <Descriptions column={2}>
          <Descriptions.Item label="描述">{project.description || '-'}</Descriptions.Item>
          <Descriptions.Item label="Git URL">
            {project.git_url ? <a href={project.git_url} target="_blank" rel="noopener noreferrer">{project.git_url}</a> : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(project.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="配置">{project.config ? JSON.stringify(project.config) : '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs defaultActiveKey="requirements">
          <TabPane tab={<span><TeamOutlined /> 需求 ({requirements.length})</span>} key="requirements">
            <Table
              columns={requirementColumns}
              dataSource={requirements}
              rowKey="id"
              onRow={(record) => ({
                onClick: () => navigate(`/requirements/${record.id}`),
                style: { cursor: 'pointer' },
              })}
            />
          </TabPane>
          <TabPane tab={`用例 (${testCases.length})`} key="testcases">
            <Table
              columns={testCaseColumns}
              dataSource={testCases}
              rowKey="id"
              onRow={(record) => ({
                onClick: () => navigate(`/testcases/${record.id}`),
                style: { cursor: 'pointer' },
              })}
            />
          </TabPane>
          <TabPane tab={`代码 (${testCodes.length})`} key="testcode">
            <Table
              columns={testCodeColumns}
              dataSource={testCodes}
              rowKey="id"
              onRow={(record) => ({
                onClick: () => navigate(`/testcode/${record.id}`),
                style: { cursor: 'pointer' },
              })}
            />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
