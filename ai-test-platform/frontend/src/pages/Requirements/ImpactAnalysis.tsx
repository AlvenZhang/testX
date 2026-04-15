import { useState } from 'react';
import { Card, Button, Space, Tag, List, Spin, message, Collapse, Empty, Divider, Alert } from 'antd';
import { ThunderboltOutlined, WarningOutlined, InfoCircleOutlined, CaretRightOutlined } from '@ant-design/icons';
import { impactAnalysisApi } from '../../services/api';
import { DiffViewer } from '../../components/DiffViewer';

const { Panel } = Collapse;

interface ImpactAnalysisResult {
  impacted_requirements: Array<{
    id: string;
    title: string;
    impact_level: 'high' | 'medium' | 'low';
    impact_description: string;
  }>;
  impacted_test_codes: Array<{
    id: string;
    name: string;
    impact_level: 'high' | 'medium' | 'low';
    changes_needed: string;
  }>;
  fix_suggestions: string[];
  summary: string;
}

interface ImpactAnalysisProps {
  requirementId: string;
  requirementTitle: string;
  onFixComplete?: () => void;
}

export function ImpactAnalysis({ requirementId, requirementTitle, onFixComplete }: ImpactAnalysisProps) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImpactAnalysisResult | null>(null);
  const [fixing, setFixing] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await impactAnalysisApi.analyze(requirementId);
      setResult(res.data);
      message.success('影响分析完成');
    } catch {
      message.error('影响分析失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFix = async (testCodeId: string) => {
    setFixing(true);
    try {
      await impactAnalysisApi.fixTestCode(requirementId, testCodeId);
      message.success('代码修复完成');
      onFixComplete?.();
    } catch {
      message.error('代码修复失败');
    } finally {
      setFixing(false);
    }
  };

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const getImpactIcon = (level: string) => {
    switch (level) {
      case 'high': return <WarningOutlined />;
      case 'medium': return <InfoCircleOutlined />;
      default: return null;
    }
  };

  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>正在进行AI影响分析...</div>
        </div>
      </Card>
    );
  }

  return (
    <div>
      <Card
        title={<Space><ThunderboltOutlined /> AI影响分析</Space>}
        extra={
          !result && (
            <Button type="primary" onClick={handleAnalyze}>
              开始分析
            </Button>
          )
        }
      >
        {!result ? (
          <Empty description="点击「开始分析」查看需求变更对现有测试代码的影响" />
        ) : (
          <div>
            <Alert
              type="info"
              message="分析完成"
              description={result.summary}
              style={{ marginBottom: 16 }}
              showIcon
            />

            <Divider orientation="left">受影响的旧需求 ({result.impacted_requirements.length})</Divider>
            {result.impacted_requirements.length > 0 ? (
              <List
                dataSource={result.impacted_requirements}
                renderItem={(item) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          {item.title}
                          <Tag color={getImpactColor(item.impact_level)} icon={getImpactIcon(item.impact_level)}>
                            {item.impact_level.toUpperCase()}
                          </Tag>
                        </Space>
                      }
                      description={item.impact_description}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="没有受影响的旧需求" />
            )}

            <Divider orientation="left">受影响的测试代码 ({result.impacted_test_codes.length})</Divider>
            {result.impacted_test_codes.length > 0 ? (
              <Collapse>
                {result.impacted_test_codes.map((code) => (
                  <Panel
                    key={code.id}
                    header={
                      <Space>
                        <span>{code.name}</span>
                        <Tag color={getImpactColor(code.impact_level)} icon={getImpactIcon(code.impact_level)}>
                          {code.impact_level.toUpperCase()}
                        </Tag>
                      </Space>
                    }
                  >
                    <div>
                      <p><strong>需要修改:</strong> {code.changes_needed}</p>
                      <Space>
                        <Button
                          type="primary"
                          loading={fixing}
                          onClick={() => handleAutoFix(code.id)}
                        >
                          AI自动修复
                        </Button>
                        <Button onClick={() => window.open(`/testcode/${code.id}`, '_blank')}>
                          查看代码
                        </Button>
                      </Space>
                    </div>
                  </Panel>
                ))}
              </Collapse>
            ) : (
              <Empty description="没有受影响的测试代码" />
            )}

            {result.fix_suggestions.length > 0 && (
              <>
                <Divider orientation="left">修复建议</Divider>
                <List
                  size="small"
                  dataSource={result.fix_suggestions}
                  renderItem={(suggestion) => (
                    <List.Item>
                      <CaretRightOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                      {suggestion}
                    </List.Item>
                  )}
                />
              </>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
