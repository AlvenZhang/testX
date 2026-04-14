import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { testCaseApi, requirementApi } from '../services/api';
import type { TestCase, Requirement } from '../types';

export function TestCasesPage() {
  const [data, setData] = useState<TestCase[]>([]);
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
      const cases = await Promise.all(requirements.map(r => testCaseApi.list(r.id)));
      setData(cases.flatMap(c => c.data));
    } catch {
      message.error('获取用例列表失败');
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
        await testCaseApi.update(editingId, values);
        message.success('更新成功');
      } else {
        await testCaseApi.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingId(null);
      fetchData();
    } catch { /* validation failed */ }
  };

  const handleEdit = (record: TestCase) => {
    setEditingId(record.id);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    await testCaseApi.delete(id);
    message.success('删除成功');
    fetchData();
  };

  const columns: ColumnsType<TestCase> = [
    { title: '用例编号', dataIndex: 'case_id', key: 'case_id' },
    { title: '标题', dataIndex: 'title', key: 'title' },
    { title: '优先级', dataIndex: 'priority', key: 'priority' },
    { title: '状态', dataIndex: 'status', key: 'status' },
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
          新建用例
        </Button>
      </div>
      <Table columns={columns} dataSource={data} rowKey="id" loading={loading} />
      <Modal
        title={editingId ? '编辑用例' : '新建用例'}
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
          <Form.Item name="case_id" label="用例编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="title" label="标题" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="steps" label="步骤">
            <Input.TextArea />
          </Form.Item>
          <Form.Item name="expected_result" label="预期结果">
            <Input />
          </Form.Item>
          <Form.Item name="priority" label="优先级" initialValue="medium">
            <Select options={[
              { value: 'low', label: '低' },
              { value: 'medium', label: '中' },
              { value: 'high', label: '高' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
