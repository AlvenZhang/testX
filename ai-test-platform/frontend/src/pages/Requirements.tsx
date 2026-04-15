import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm, Tag, Spin } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined, RocketOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { requirementApi, projectApi, workflowApi } from '../services/api';
import { MonacoEditor } from '../components/MonacoEditor';
import type { Requirement, Project } from '../types';

const priorityOptions = [
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
  { value: 'critical', label: '紧急' },
];

const statusOptions = [
  { value: 'pending', label: '待处理', color: 'default' },
  { value: 'cases_generated', label: '用例已生成', color: 'processing' },
  { value: 'code_generated', label: '代码已生成', color: 'success' },
  { value: 'tested', label: '已测试', color: 'green' },
];

interface StreamMessage {
  type: 'progress' | 'analysis' | 'chunk' | 'test_cases' | 'code_chunk' | 'done' | 'error';
  content?: string;
  test_code_id?: string;
  requirement_id?: string;
}

export function RequirementsPage() {
  const [data, setData] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(false);
  const [generatingIds, setGeneratingIds] = useState<Set<string>>(new Set());
  const [modalVisible, setModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [projects, setProjects] = useState<Project[]>([]);

  // 流式生成弹窗状态
  const [streamModalVisible, setStreamModalVisible] = useState(false);
  const [streamContent, setStreamContent] = useState('');
  const [testCasesContent, setTestCasesContent] = useState<any[]>([]);
  const [codeContent, setCodeContent] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastGeneratedId, setLastGeneratedId] = useState<string | null>(null);
  const [hasResults, setHasResults] = useState(false);

  const fetchProjects = async () => {
    const res = await projectApi.list();
    setProjects(res.data);
  };

  const fetchData = async () => {
    if (projects.length === 0) return;
    setLoading(true);
    try {
      const reqs = await Promise.all(projects.map(p => requirementApi.list(p.id)));
      setData(reqs.flatMap(r => r.data));
    } catch {
      message.error('获取需求列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);
  useEffect(() => { if (projects.length > 0) fetchData(); }, [projects]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingId) {
        await requirementApi.update(editingId, values);
        message.success('更新成功');
      } else {
        await requirementApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingId(null);
      fetchData();
    } catch { /* validation failed */ }
  };

  const handleEdit = (record: Requirement) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    await requirementApi.delete(id);
    message.success('删除成功');
    fetchData();
  };

  const handleGenerateTestsStream = async (id: string) => {
    // 如果已有结果，直接显示
    if (hasResults && lastGeneratedId === id) {
      setStreamModalVisible(true);
      return;
    }

    setGeneratingIds(prev => new Set(prev).add(id));
    setStreamModalVisible(true);
    setStreamContent('正在连接 AI 服务...');
    setTestCasesContent([]);
    setCodeContent('');
    setIsGenerating(true);
    setHasResults(false);
    setLastGeneratedId(null);

    try {
      const response = await workflowApi.generateTestsStream(id);
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
                  setStreamContent(prev => prev + '\n' + msg.content);
                  break;
                case 'analysis':
                  try {
                    const analysis = JSON.parse(msg.content || '{}');
                    setStreamContent(prev => prev + `\n分析完成！\n测试要点: ${(analysis.test_points || []).length} 项\n风险点: ${(analysis.risk_points || []).length} 项`);
                  } catch {
                    setStreamContent(prev => prev + '\n分析完成');
                  }
                  break;
                case 'chunk':
                  setTestCasesContent(prev => [...prev, msg.content]);
                  break;
                case 'test_cases':
                  try {
                    const cases = JSON.parse(msg.content || '[]');
                    setTestCasesContent(cases);
                    setStreamContent(prev => prev + `\n生成测试用例完成！共 ${cases.length} 个用例`);
                  } catch {
                    setStreamContent(prev => prev + '\n用例生成完成');
                  }
                  break;
                case 'code_chunk':
                  setCodeContent(prev => prev + (msg.content || ''));
                  break;
                case 'done':
                  setStreamContent(prev => prev + '\n\n✅ 测试代码生成完成！');
                  setIsGenerating(false);
                  setHasResults(true);
                  setLastGeneratedId(id);
                  message.success('生成完成！');
                  break;
                case 'error':
                  setStreamContent(prev => prev + '\n❌ 错误: ' + msg.content);
                  setIsGenerating(false);
                  message.error(msg.content || '生成失败');
                  break;
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }
    } catch (err: unknown) {
      message.error((err as Error)?.message || '生成失败');
      setIsGenerating(false);
    } finally {
      setGeneratingIds(prev => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const columns: ColumnsType<Requirement> = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '优先级', dataIndex: 'priority', key: 'priority', render: (v) => priorityOptions.find(o => o.value === v)?.label },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v) => {
        const opt = statusOptions.find(o => o.value === v);
        return <Tag color={opt?.color}>{opt?.label}</Tag>;
      },
    },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v) => new Date(v).toLocaleString() },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            type="primary"
            icon={<RocketOutlined />}
            loading={generatingIds.has(record.id)}
            onClick={() => handleGenerateTestsStream(record.id)}
          >
            AI 生成
          </Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm title="确认删除?" onConfirm={() => handleDelete(record.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalVisible(true); }}>
          新建需求
        </Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingId ? '编辑需求' : '新建需求'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => { setModalVisible(false); form.resetFields(); }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="project_id" label="项目" rules={[{ required: true }]}>
            <Select>
              {projects.map(p => <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={4} placeholder="请详细描述需求，包括功能点、业务流程、约束条件等，AI将根据描述生成测试用例" />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select options={priorityOptions} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 流式生成弹窗 */}
      <Modal
        title={isGenerating ? "AI 正在生成测试..." : "AI 测试生成结果"}
        open={streamModalVisible}
        footer={[
          <Button key="close" onClick={() => { setStreamModalVisible(false); }}>
            关闭
          </Button>
        ]}
        onCancel={() => { setStreamModalVisible(false); }}
        closable={!isGenerating}
        maskClosable={!isGenerating}
        width={800}
      >
        <div style={{ maxHeight: 400, overflow: 'auto', marginBottom: 16 }}>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, background: '#f5f5f5', padding: 12 }}>
            {streamContent}
            {isGenerating && <Spin size="small" />}
          </pre>
        </div>

        {testCasesContent.length > 0 && (
          <div style={{ marginBottom: 16 }}>
            <h4>生成的测试用例 ({testCasesContent.length})</h4>
            <ul>
              {testCasesContent.map((tc, i) => (
                <li key={i}>{tc.title || tc.case_id || `用例${i + 1}`} - {tc.priority}</li>
              ))}
            </ul>
          </div>
        )}

        {codeContent && (
          <div>
            <h4>生成的测试代码</h4>
            <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 11, background: '#f5f5f5', padding: 12 }}>
              {codeContent}
            </pre>
          </div>
        )}
      </Modal>
    </div>
  );
}
