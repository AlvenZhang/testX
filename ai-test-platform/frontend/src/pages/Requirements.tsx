import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { requirementApi, projectApi } from '../services/api';
import type { Requirement, Project } from '../types';

const priorityOptions = [
  { value: 'low', label: '低' },
  { value: 'medium', label: '中' },
  { value: 'high', label: '高' },
  { value: 'critical', label: '紧急' },
];

const statusOptions = [
  { value: 'pending', label: '待处理' },
  { value: 'cases_generated', label: '用例已生成' },
  { value: 'code_generated', label: '代码已生成' },
  { value: 'tested', label: '已测试' },
];

export function RequirementsPage() {
  const [data, setData] = useState<Requirement[]>([]);
  const [loading, setLoading] = useState(false);
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

  const columns: ColumnsType<Requirement> = [
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    { title: '优先级', dataIndex: 'priority', key: 'priority', render: (v) => priorityOptions.find(o => o.value === v)?.label },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v) => statusOptions.find(o => o.value === v)?.label },
    { title: '版本', dataIndex: 'version', key: 'version' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v) => new Date(v).toLocaleString() },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
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
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select options={priorityOptions} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
