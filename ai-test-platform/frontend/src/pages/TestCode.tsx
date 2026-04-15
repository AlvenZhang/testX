import { useState, useEffect } from 'react';
import { Table, Button, message, Space, Tag, Drawer, Select, Modal, Spin } from 'antd';
import { PlayCircleOutlined, CodeOutlined } from '@ant-design/icons';
import { testCodeApi, projectApi, executionApi } from '../services/api';
import { MonacoEditor } from '../components/MonacoEditor';
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

interface StreamMessage {
  type: 'progress' | 'log' | 'done' | 'error';
  content?: string;
  status?: string;
  exit_code?: number;
  duration_ms?: number;
  logs?: string;
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
  const [editorLanguage, setEditorLanguage] = useState('python');
  const [streamLogs, setStreamLogs] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);

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
    // 如果正在执行，点击切换显示/隐藏弹窗
    if (running === id) {
      setLogVisible(prev => !prev);
      return;
    }

    setRunning(id);
    setIsExecuting(true);
    setStreamLogs('正在连接执行服务...\n');
    setLogVisible(true);

    try {
      const response = await executionApi.runStream(id);
      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const msg: StreamMessage = JSON.parse(line.slice(6));

              switch (msg.type) {
                case 'progress':
                  setStreamLogs(prev => prev + msg.content + '\n');
                  break;
                case 'log':
                  setStreamLogs(prev => prev + msg.content + '\n');
                  break;
                case 'done':
                  setStreamLogs(prev => prev + '\n✅ 执行完成!\n');
                  setExecResult({
                    logs: msg.logs || '',
                    status: msg.status || 'unknown',
                    duration_ms: msg.duration_ms || 0,
                  });
                  setIsExecuting(false);
                  message.success('执行完成');
                  break;
                case 'error':
                  setStreamLogs(prev => prev + '\n❌ 错误: ' + msg.content + '\n');
                  setIsExecuting(false);
                  message.error(msg.content || '执行失败');
                  break;
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }
    } catch (err: unknown) {
      const errorMsg = (err as { message?: string })?.message || '执行失败';
      setStreamLogs(prev => prev + '\n❌ ' + errorMsg + '\n');
      setIsExecuting(false);
      message.error(errorMsg);
    } finally {
      setRunning(null);
    }
  };

  const handleViewCode = async (id: string) => {
    const res = await testCodeApi.get(id);
    const code = res.data.code_content || res.data;
    setCodeContent(typeof code === 'string' ? code : JSON.stringify(code, null, 2));
    setSelectedCode(id);
    // 根据框架设置语言
    const item = data.find(d => d.id === id);
    if (item?.framework) {
      if (item.framework.includes('pytest') || item.framework.includes('python')) {
        setEditorLanguage('python');
      } else if (item.framework.includes('jest') || item.framework.includes('javascript')) {
        setEditorLanguage('javascript');
      } else if (item.framework.includes('junit') || item.framework.includes('java')) {
        setEditorLanguage('java');
      } else {
        setEditorLanguage('python');
      }
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', render: (v: string) => v.slice(0, 8) + '...' },
    { title: '框架', dataIndex: 'framework', key: 'framework', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => <Tag color={v === 'active' ? 'green' : 'red'}>{v}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => new Date(v).toLocaleString() },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: TestCodeItem) => (
        <Space>
          <Button
            size="small"
            type="primary"
            icon={<PlayCircleOutlined />}
            loading={running === record.id && isExecuting}
            onClick={() => handleRun(record.id)}
          >
            {running === record.id && !isExecuting ? '查看' : '执行'}
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

      {/* 代码查看抽屉 - 使用 MonacoEditor */}
      <Drawer
        title="测试代码"
        open={!!selectedCode}
        onClose={() => setSelectedCode(null)}
        width={800}
        extra={
          <Select
            value={editorLanguage}
            onChange={setEditorLanguage}
            style={{ width: 120 }}
            options={[
              { value: 'python', label: 'Python' },
              { value: 'javascript', label: 'JavaScript' },
              { value: 'java', label: 'Java' },
              { value: 'json', label: 'JSON' },
            ]}
          />
        }
      >
        <MonacoEditor
          value={codeContent}
          language={editorLanguage}
          readOnly={true}
          height="500px"
        />
      </Drawer>

      {/* 执行日志弹窗 */}
      <Modal
        title={isExecuting ? "🔄 执行中..." : "✅ 执行结果"}
        open={logVisible}
        onCancel={() => !isExecuting && setLogVisible(false)}
        closable={!isExecuting}
        maskClosable={!isExecuting}
        footer={[
          <Button key="close" onClick={() => setLogVisible(false)} disabled={isExecuting}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <div style={{ maxHeight: 500, overflow: 'auto', marginBottom: 16 }}>
          <pre style={{
            whiteSpace: 'pre-wrap',
            fontSize: 13,
            background: '#1e1e1e',
            color: '#d4d4d4',
            padding: 16,
            borderRadius: 4,
            fontFamily: 'Menlo, Monaco, Consolas, monospace',
            lineHeight: 1.6,
            margin: 0
          }}>
            {streamLogs}
            {isExecuting && <Spin size="small" style={{ marginLeft: 8 }} />}
          </pre>
        </div>
        {execResult && !isExecuting && (
          <div>
            <Tag color={execResult.status === 'success' ? 'green' : 'red'} style={{ marginBottom: 8 }}>
              状态: {execResult.status}
            </Tag>
            <Tag style={{ marginBottom: 8 }}>耗时: {execResult.duration_ms}ms</Tag>
            {execResult.logs && (
              <>
                <h4>详细日志:</h4>
                <MonacoEditor
                  value={execResult.logs}
                  language="plaintext"
                  readOnly={true}
                  height="200px"
                />
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
