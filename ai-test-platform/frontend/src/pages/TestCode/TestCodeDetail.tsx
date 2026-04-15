import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Tag, Spin, message, Divider, Row, Col } from 'antd';
import { ArrowLeftOutlined, EditOutlined, PlayCircleOutlined, CodeOutlined, HistoryOutlined } from '@ant-design/icons';
import { testCodeApi, testRunApi } from '../../services/api';
import { MonacoEditor } from '../../components/MonacoEditor';
import type { TestCode, TestRun } from '../../types';

export function TestCodeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [testCode, setTestCode] = useState<TestCode | null>(null);
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
      const [codeRes, runsRes] = await Promise.all([
        testCodeApi.get(id),
        testRunApi.list({ test_code_id: id }),
      ]);
      setTestCode(codeRes.data);
      setTestRuns(runsRes.data || []);
    } catch {
      message.error('获取代码详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" />;
  if (!testCode) return <div>代码不存在</div>;

  const successCount = testRuns.filter(r => r.status === 'success').length;
  const failedCount = testRuns.filter(r => r.status === 'failed').length;
  const passRate = testRuns.length > 0 ? ((successCount / testRuns.length) * 100).toFixed(1) : '-';

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/testcode')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card
        title={<Space><CodeOutlined /> {testCode.name}</Space>}
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => navigate(`/testruns/new?test_code_id=${id}`)}
            >
              执行测试
            </Button>
            <Button icon={<EditOutlined />} onClick={() => navigate(`/testcode/${id}/edit`)}>
              编辑
            </Button>
          </Space>
        }
      >
        <Descriptions column={3}>
          <Descriptions.Item label="框架">{testCode.framework}</Descriptions.Item>
          <Descriptions.Item label="平台">{testCode.platform}</Descriptions.Item>
          <Descriptions.Item label="测试类型">{testCode.test_type}</Descriptions.Item>
          <Descriptions.Item label="通过率">{passRate}%</Descriptions.Item>
          <Descriptions.Item label="执行次数">{testRuns.length}</Descriptions.Item>
          <Descriptions.Item label="更新时间">
            {testCode.updated_at ? new Date(testCode.updated_at).toLocaleString() : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }} title="测试代码">
        <MonacoEditor
          value={testCode.code_content}
          language="python"
          readOnly={true}
          height={400}
        />
      </Card>

      <Card style={{ marginTop: 16 }} title="执行历史">
        {testRuns.length > 0 ? (
          <Row gutter={16}>
            {testRuns.slice(0, 5).map(run => (
              <Col span={24} key={run.id} style={{ marginBottom: 8 }}>
                <Card
                  size="small"
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/testruns/${run.id}`)}
                >
                  <Space>
                    <span>{new Date(run.created_at).toLocaleString()}</span>
                    <Tag color={run.status === 'success' ? 'success' : run.status === 'failed' ? 'error' : 'processing'}>
                      {run.status}
                    </Tag>
                    {run.duration && <span>耗时: {run.duration}ms</span>}
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <div style={{ textAlign: 'center', color: '#999' }}>暂无执行记录</div>
        )}
      </Card>
    </div>
  );
}
