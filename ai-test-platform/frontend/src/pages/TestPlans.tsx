import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { testPlanApi, requirementApi } from '../services/api';
import type { TestPlan, Requirement } from '../types';

export function TestPlansPage() {
  const [data, setData] = useState<TestPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [requirements, setRequirements] = useState<Requirement[]>([]);

  const fetchRequirements = async () => {
    const res = await requirementApi.list('all');
    setRequirements(res.data);
  };

  const fetchData = async () => {
    if (requirements.length === 0) return;
    setLoading(true);
    try {
      const plans = await Promise.all(requirements.map(r => testPlanApi.list(r.id)));
      setData(plans.flatMap(p => p.data));
    } catch {
      message.error('获取方案列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRequirements(); }, []);
  useEffect(() => { if (requirements.length > 0) fetchData(); }, [requirements]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingId) {
        await testPlanApi.update(editingId, values);
        message.success('更新成功');
      } else {
        await testPlanApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingId(null);
      fetchData();
    } catch { /* validation failed */ }
  };

  const handleEdit = (record: TestPlan) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    await testPlanApi.delete(id);
    message.success('删除成功');
    fetchData();
  };

  const columns: ColumnsType<TestPlan> = [
    { title: '需求', dataIndex: 'requirement_id', key: 'requirement_id', render: (v) => requirements.find(r => r.id === v)?.title || v },
    { title: '测试范围', dataIndex: 'test_scope', key: 'test_scope', ellipsis: true },
    { title: '测试类型', dataIndex: 'test_types', key: 'test_types', render: (v) => Array.isArray(v) ? v.join(', ') : v },
    { title: '测试策略', dataIndex: 'test_strategy', key: 'test_strategy', ellipsis: true },
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
          新建方案
        </Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingId ? '编辑方案' : '新建方案'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => { setModalVisible(false); form.resetFields(); }}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="requirement_id" label="需求" rules={[{ required: true }]}>
            <Select>
              {requirements.map(r => <Select.Option key={r.id} value={r.id}>{r.title}</Select.Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="test_scope" label="测试范围">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="test_types" label="测试类型">
            <Select mode="multiple" options={[
              { value: 'web', label: 'Web' },
              { value: 'api', label: 'API' },
              { value: 'mobile', label: 'Mobile' },
            ]} />
          </Form.Item>
          <Form.Item name="test_strategy" label="测试策略">
            <Input />
          </Form.Item>
          <Form.Item name="risk_points" label="风险点">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
