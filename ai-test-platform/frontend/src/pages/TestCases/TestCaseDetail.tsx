import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Tag, Spin, message, Divider, Empty } from 'antd';
import { ArrowLeftOutlined, EditOutlined, BugOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { testCaseApi, testCodeApi } from '../../services/api';
import type { TestCase, TestCode } from '../../types';

export function TestCaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [testCase, setTestCase] = useState<TestCase | null>(null);
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
      const [caseRes, codesRes] = await Promise.all([
        testCaseApi.get(id),
        testCodeApi.list({ test_case_id: id }),
      ]);
      setTestCase(caseRes.data);
      setTestCodes(codesRes.data || []);
    } catch {
      message.error('获取用例详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" />;
  if (!testCase) return <div>用例不存在</div>;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/testcases')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card
        title={<Space><BugOutlined /> {testCase.title}</Space>}
        extra={
          <Button icon={<EditOutlined />} onClick={() => navigate(`/testcases/${id}/edit`)}>
            编辑
          </Button>
        }
      >
        <Descriptions column={2}>
          <Descriptions.Item label="类型">{testCase.test_type}</Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag color={
              testCase.priority === 'high' ? 'red' :
              testCase.priority === 'medium' ? 'orange' : 'blue'
            }>
              {testCase.priority}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="状态">{testCase.status}</Descriptions.Item>
          <Descriptions.Item label="前置条件">{testCase.preconditions || '-'}</Descriptions.Item>
        </Descriptions>

        <Divider>测试步骤</Divider>
        <div style={{ whiteSpace: 'pre-wrap' }}>{testCase.steps || '无'}</div>

        <Divider>预期结果</Divider>
        <div style={{ whiteSpace: 'pre-wrap' }}>{testCase.expected_result || '无'}</div>
      </Card>

      <Card style={{ marginTop: 16 }} title="关联的测试代码">
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
          <Empty description="暂无关联代码">
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => navigate('/ai/generate-code')}
            >
              AI生成代码
            </Button>
          </Empty>
        )}
      </Card>
    </div>
  );
}
