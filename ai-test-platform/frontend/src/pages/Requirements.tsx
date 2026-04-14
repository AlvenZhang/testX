import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm, Tag } from 'antd';
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

export function RequirementsPage() {
  const [data, setData] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [projects, setProjects] = useState<Project[]>([]);

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

  const handleGenerateTests = async (id: string) => {
    setGenerating(true);
    try {
      const res = await workflowApi.generateTests(id);
      const { analysis, test_cases, test_code_preview } = res.data;
      message.success(`生成完成！生成 ${test_cases.length} 个测试用例`);
      Modal.info({
        title: 'AI 测试生成结果',
        width: 600,
        content: (
          <div>
            <h4>测试要点 ({analysis.test_points.length})</h4>
            <Space style={{ marginBottom: 16 }}>
              {analysis.test_points.slice(0, 3).map((p, i) => (
                <Tag key={i}>{p.slice(0, 30)}...</Tag>
              ))}
            </Space>
            <h4>生成用例 ({test_cases.length})</h4>
            <ul>
              {test_cases.slice(0, 5).map((c, i) => (
                <li key={i}>{c.case_id}: {c.title} ({c.priority})</li>
              ))}
            </ul>
            <h4>测试代码预览</h4>
            <pre style={{ maxHeight: 200, overflow: 'auto', fontSize: 11 }}>
              {test_code_preview}
            </pre>
          </div>
        ),
      });
      fetchData();
    } catch (err: unknown) {
      message.error((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '生成失败');
    } finally {
      setGenerating(false);
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
            loading={generating}
            onClick={() => handleGenerateTests(record.id)}
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
    </div>
  );
}
