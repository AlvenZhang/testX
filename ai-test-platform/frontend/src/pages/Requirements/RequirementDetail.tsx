import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Tabs, Timeline, Tag, Spin, message, Empty } from 'antd';
import { ArrowLeftOutlined, EditOutlined, FileTextOutlined, HistoryOutlined } from '@ant-design/icons';
import { requirementApi, testCaseApi, testCodeApi, testRunApi } from '../../services/api';
import type { Requirement, TestCase, TestCode, TestRun } from '../../types';

const { TabPane } = Tabs;

export function RequirementDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [requirement, setRequirement] = useState<Requirement | null>(null);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [testCodes, setTestCodes] = useState<TestCode[]>([]);
  const [testRuns, setTestRuns] = useState<TestRun[]>([]);
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
      const [reqRes, casesRes, codesRes, runsRes] = await Promise.all([
        requirementApi.get(id),
        testCaseApi.list(id),
        testCodeApi.list(id),
        testRunApi.list(undefined, id),
      ]);
      setRequirement(reqRes.data);
      setTestCases(casesRes.data || []);
      setTestCodes(codesRes.data || []);
      setTestRuns(runsRes.data || []);
    } catch {
      message.error('获取需求详情失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status: string) => {
    const colorMap: Record<string, string> = {
      pending: 'default',
      'test_cases_generated': 'processing',
      'code_generated': 'blue',
      'tested': 'success',
    };
    return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
  };

  const getStatusLabel = (status: string) => {
    const labelMap: Record<string, string> = {
      pending: '待分析',
      'test_cases_generated': '已生成用例',
      'code_generated': '已生成代码',
      'tested': '已测试',
    };
    return labelMap[status] || status;
  };

  if (loading) return <Spin size="large" />;
  if (!requirement) return <div>需求不存在</div>;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/requirements')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card
        title={<Space><FileTextOutlined /> {requirement.title}</Space>}
        extra={
          <Button icon={<EditOutlined />} onClick={() => navigate(`/requirements/${id}/edit`)}>
            编辑
          </Button>
        }
      >
        <Descriptions column={2}>
          <Descriptions.Item label="状态">{getStatusTag(requirement.status)} {getStatusLabel(requirement.status)}</Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag color={requirement.priority === 'high' ? 'red' : requirement.priority === 'medium' ? 'orange' : 'blue'}>
              {requirement.priority}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="类型">{requirement.type || '-'}</Descriptions.Item>
          <Descriptions.Item label="创建时间">{new Date(requirement.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>{requirement.description || '-'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Tabs defaultActiveKey="testcases">
          <TabPane tab={`关联用例 (${testCases.length})`} key="testcases">
            {testCases.length > 0 ? (
              <div>
                {testCases.map(tc => (
                  <Card
                    key={tc.id}
                    size="small"
                    style={{ marginBottom: 8, cursor: 'pointer' }}
                    onClick={() => navigate(`/testcases/${tc.id}`)}
                  >
                    <Space>
                      <span>{tc.title}</span>
                      <Tag>{tc.test_type}</Tag>
                      <Tag color={tc.priority === 'high' ? 'red' : 'blue'}>{tc.priority}</Tag>
                    </Space>
                  </Card>
                ))}
              </div>
            ) : (
              <Empty description="暂无关联用例" />
            )}
          </TabPane>

          <TabPane tab={`关联代码 (${testCodes.length})`} key="testcode">
            {testCodes.length > 0 ? (
              <div>
                {testCodes.map(code => (
                  <Card
                    key={code.id}
                    size="small"
                    style={{ marginBottom: 8, cursor: 'pointer' }}
                    onClick={() => navigate(`/testcode/${code.id}`)}
                  >
                    <Space>
                      <span>{code.name}</span>
                      <Tag>{code.framework}</Tag>
                      <Tag>{code.platform}</Tag>
                    </Space>
                  </Card>
                ))}
              </div>
            ) : (
              <Empty description="暂无关联代码" />
            )}
          </TabPane>

          <TabPane tab={`执行记录 (${testRuns.length})`} key="testruns">
            {testRuns.length > 0 ? (
              <Timeline
                items={testRuns.map(run => ({
                  color: run.status === 'success' ? 'green' : run.status === 'failed' ? 'red' : 'blue',
                  children: (
                    <div>
                      <Space>
                        <span>{new Date(run.created_at).toLocaleString()}</span>
                        <Tag color={run.status === 'success' ? 'success' : run.status === 'failed' ? 'error' : 'processing'}>
                          {run.status}
                        </Tag>
                      </Space>
                    </div>
                  ),
                }))}
              />
            ) : (
              <Empty description="暂无执行记录" />
            )}
          </TabPane>

          <TabPane tab={<span><HistoryOutlined /> 版本历史</span>} key="history">
            <Empty description="版本历史功能开发中" />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
}
