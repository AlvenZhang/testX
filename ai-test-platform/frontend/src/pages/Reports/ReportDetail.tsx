import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Descriptions, Button, Space, Tag, Spin, message, Row, Col, Table, Divider } from 'antd';
import { ArrowLeftOutlined, FileSearchOutlined, DownloadOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { reportApi } from '../../services/api';
import { PassRateChart, TestTrendChart } from '../../components/Charts';
import type { Report } from '../../types';

export function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<Report | null>(null);
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
      const res = await reportApi.get(id);
      setReport(res.data);
    } catch {
      message.error('获取报告详情失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Spin size="large" />;
  if (!report) return <div>报告不存在</div>;

  const passedCount = report.summary?.passed || 0;
  const failedCount = report.summary?.failed || 0;
  const totalCount = passedCount + failedCount;

  const failedCases = report.details?.filter((d: any) => d.status === 'failed') || [];

  const failedCaseColumns = [
    { title: '用例名称', dataIndex: 'name', key: 'name' },
    { title: '错误类型', dataIndex: 'error_type', key: 'error_type' },
    { title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
  ];

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/reports')} style={{ marginBottom: 16 }}>
        返回列表
      </Button>

      <Card
        title={<Space><FileSearchOutlined /> {report.name || '测试报告'}</Space>}
        extra={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={() => reportApi.export(report.id, 'html')}>
              导出HTML
            </Button>
            <Button icon={<DownloadOutlined />} onClick={() => reportApi.export(report.id, 'pdf')}>
              导出PDF
            </Button>
          </Space>
        }
      >
        <Descriptions column={4}>
          <Descriptions.Item label="报告类型">
            <Tag color={report.report_type === 'new_feature' ? 'blue' : 'green'}>
              {report.report_type === 'new_feature' ? '新功能测试' : '回归测试'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="测试类型">{report.test_type}</Descriptions.Item>
          <Descriptions.Item label="执行时间">{new Date(report.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="通过率">
            {totalCount > 0 ? `${((passedCount / totalCount) * 100).toFixed(1)}%` : '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <PassRateChart passed={passedCount} failed={failedCount} />
        </Col>
        <Col span={12}>
          <Card title="测试统计">
            <Row gutter={16}>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#52c41a' }}>{passedCount}</div>
                  <div><CheckCircleOutlined style={{ color: '#52c41a' }} /> 通过</div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#ff4d4f' }}>{failedCount}</div>
                  <div><CloseCircleOutlined style={{ color: '#ff4d4f' }} /> 失败</div>
                </div>
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#1890ff' }}>{totalCount}</div>
                  <div>总计</div>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {failedCases.length > 0 && (
        <Card style={{ marginTop: 16 }} title="失败用例详情" bordered={false}>
          <Table
            columns={failedCaseColumns}
            dataSource={failedCases}
            rowKey="id"
            pagination={false}
          />
        </Card>
      )}

      {report.metadata && (
        <>
          <Divider>执行环境</Divider>
          <Descriptions column={3}>
            <Descriptions.Item label="平台">{report.metadata.platform || '-'}</Descriptions.Item>
            <Descriptions.Item label="框架">{report.metadata.framework || '-'}</Descriptions.Item>
            <Descriptions.Item label="执行时长">{report.metadata.duration || '-'}ms</Descriptions.Item>
          </Descriptions>
        </>
      )}
    </div>
  );
}
