import { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, message, Space, Popconfirm } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { testCaseApi, requirementApi, projectApi } from '../services/api';
import type { TestCase, Requirement, Project } from '../types';

export function TestCasesPage() {
  const [data, setData] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form] = Form.useForm();
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedRequirementId, setSelectedRequirementId] = useState<string | null>(null);
  const [allTestCases, setAllTestCases] = useState<TestCase[]>([]);

  const fetchProjects = async () => {
    const res = await projectApi.list();
    setProjects(res.data);
  };

  const fetchRequirements = async () => {
    if (projects.length === 0) return;
    try {
      const reqs = await Promise.all(projects.map(p => requirementApi.list(p.id)));
      setRequirements(reqs.flatMap(r => r.data));
    } catch {
      message.error('获取需求列表失败');
    }
  };

  const fetchData = async () => {
    if (requirements.length === 0) return;
    setLoading(true);
    try {
      const cases = await Promise.all(requirements.map(r => testCaseApi.list(r.id)));
      const allCases = cases.flatMap(c => c.data);
      setAllTestCases(allCases);
      // 根据筛选条件过滤
      filterTestCases(allCases, selectedProjectId, selectedRequirementId);
    } catch {
      message.error('获取用例列表失败');
    } finally {
      setLoading(false);
    }
  };

  const filterTestCases = (cases: TestCase[], projectId: string | null, reqId: string | null) => {
    let filtered = cases;
    if (projectId) {
      const reqIds = requirements.filter(r => r.project_id === projectId).map(r => r.id);
      filtered = filtered.filter(c => reqIds.includes(c.requirement_id));
    }
    if (reqId) {
      filtered = filtered.filter(c => c.requirement_id === reqId);
    }
    setData(filtered);
  };

  useEffect(() => { fetchProjects(); }, []);
  useEffect(() => { if (projects.length > 0) fetchRequirements(); }, [projects]);
  useEffect(() => { if (requirements.length > 0) fetchData(); }, [requirements]);

  // 处理项目筛选变化
  const handleProjectChange = (projectId: string | null) => {
    setSelectedProjectId(projectId);
    setSelectedRequirementId(null); // 重置需求筛选
    filterTestCases(allTestCases, projectId, null);
  };

  // 处理需求筛选变化
  const handleRequirementChange = (reqId: string | null) => {
    setSelectedRequirementId(reqId);
    filterTestCases(allTestCases, selectedProjectId, reqId);
  };

  // 获取当前项目下的需求选项
  const availableRequirements = selectedProjectId
    ? requirements.filter(r => r.project_id === selectedProjectId)
    : requirements;

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
      <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditingId(null); form.resetFields(); setModalVisible(true); }}>
          新建用例
        </Button>
        <span>项目:</span>
        <Select
          style={{ width: 150 }}
          placeholder="全部项目"
          allowClear
          value={selectedProjectId}
          onChange={handleProjectChange}
        >
          {projects.map(p => (
            <Select.Option key={p.id} value={p.id}>{p.name}</Select.Option>
          ))}
        </Select>
        <span>需求:</span>
        <Select
          style={{ width: 200 }}
          placeholder="全部需求"
          allowClear
          value={selectedRequirementId}
          onChange={handleRequirementChange}
        >
          {availableRequirements.map(r => (
            <Select.Option key={r.id} value={r.id}>{r.title}</Select.Option>
          ))}
        </Select>
        <span style={{ color: '#999' }}>共 {data.length} 条</span>
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
