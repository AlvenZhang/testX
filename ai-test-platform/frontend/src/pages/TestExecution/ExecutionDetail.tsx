import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Tag, Spin, message, Timeline, Collapse, Empty } from 'antd';
import { ArrowLeftOutlined, PlayCircleOutlined, ApiOutlined, MobileOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { testRunApi } from '../../services/api';
import { ExecutionLog } from '../../components/ExecutionLog';
import type { TestRun } from '../../types';

const { Panel } = Collapse;

export function ExecutionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [testRun, setTestRun] = useState<TestRun | null>(null);
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
      const res = await testRunApi.get(id);
      setTestRun(res.data);
    } catch {
      message.error('获取执行详情失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <PlayCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'android':
      case 'ios':
        return <MobileOutlined />;
      default:
        return <ApiOutlined />;
    }
  };

  if (loading) return <Spin size="large" />;
  if (!testRun) return <div>执行记录不存在</div>;

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/testruns')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card
        title={
          <Space>
            {getStatusIcon(testRun.status)}
            <span>执行详情</span>
          </Space>
        }
        extra={
          testRun.status === 'pending' && (
            <Button danger onClick={() => testRunApi.cancel(testRun.id)}>
              取消执行
            </Button>
          )
        }
      >
        <Descriptions column={3}>
          <Descriptions.Item label="状态">
            <Tag color={
              testRun.status === 'success' ? 'success' :
              testRun.status === 'failed' ? 'error' : 'processing'
            }>
              {testRun.status}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="平台">
            <Space>{getPlatformIcon(testRun.platform)} {testRun.platform}</Space>
          </Descriptions.Item>
          <Descriptions.Item label="测试类型">{testRun.test_type || '-'}</Descriptions.Item>
          <Descriptions.Item label="开始时间">{new Date(testRun.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="耗时">{testRun.duration ? `${testRun.duration}ms` : '-'}</Descriptions.Item>
          <Descriptions.Item label="通过率">
            {testRun.total_cases && testRun.passed_cases
              ? `${((testRun.passed_cases / testRun.total_cases) * 100).toFixed(1)}%`
              : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }} title="执行统计">
        <Descriptions column={4}>
          <Descriptions.Item label="总用例">{testRun.total_cases || 0}</Descriptions.Item>
          <Descriptions.Item label="通过">{testRun.passed_cases || 0}</Descriptions.Item>
          <Descriptions.Item label="失败">{testRun.failed_cases || 0}</Descriptions.Item>
          <Descriptions.Item label="跳过">{testRun.skipped_cases || 0}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card style={{ marginTop: 16 }} title="执行日志">
        {testRun.logs ? (
          <ExecutionLog logs={testRun.logs} />
        ) : (
          <Empty description="暂无日志" />
        )}
      </Card>

      {testRun.error_message && (
        <Card style={{ marginTop: 16 }} title="错误信息" bordered={false}>
          <pre style={{ color: '#ff4d4f', whiteSpace: 'pre-wrap' }}>{testRun.error_message}</pre>
        </Card>
      )}

      {testRun.screenshots && testRun.screenshots.length > 0 && (
        <Card style={{ marginTop: 16 }} title="截图记录">
          <Collapse>
            {testRun.screenshots.map((screenshot, index) => (
              <Panel header={`截图 ${index + 1}`} key={index}>
                <img src={screenshot} alt={`Screenshot ${index + 1}`} style={{ maxWidth: '100%' }} />
              </Panel>
            ))}
          </Collapse>
        </Card>
      )}
    </div>
  );
}
