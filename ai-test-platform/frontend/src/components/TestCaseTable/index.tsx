import { useState } from 'react';
import { Table, Button, Space, Tag, Dropdown, Modal, message, Tooltip } from 'antd';
import type { ColumnsType, TablePaginationConfig } from 'antd/es/table';
import type { MenuProps } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, MoreOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import type { TestCase } from '../../types';

interface TestCaseTableProps {
  dataSource: TestCase[];
  loading?: boolean;
  total?: number;
  page?: number;
  pageSize?: number;
  onChange?: (page: number, pageSize: number) => void;
  onEdit?: (testCase: TestCase) => void;
  onDelete?: (testCase: TestCase) => void;
  onRun?: (testCase: TestCase) => void;
  onBatchRun?: (testCases: TestCase[]) => void;
  selectedRowKeys?: string[];
  onSelectionChange?: (keys: string[]) => void;
}

export function TestCaseTable({
  dataSource,
  loading,
  total,
  page = 1,
  pageSize = 10,
  onChange,
  onEdit,
  onDelete,
  onRun,
  onBatchRun,
  selectedRowKeys = [],
  onSelectionChange,
}: TestCaseTableProps) {
  const [selectedKeys, setSelectedKeys] = useState<string[]>(selectedRowKeys);

  const handleTableChange = (
    pagination: TablePaginationConfig,
  ) => {
    if (pagination.current && pagination.pageSize && onChange) {
      onChange(pagination.current, pagination.pageSize);
    }
  };

  const handleSelectionChange = (keys: React.Key[]) => {
    setSelectedKeys(keys as string[]);
    onSelectionChange?.(keys as string[]);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'blue';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'inactive': return 'default';
      case 'deprecated': return 'red';
      default: return 'default';
    }
  };

  const columns: ColumnsType<TestCase> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      ellipsis: true,
      render: (id: string) => (
        <Tooltip title={id}>
          <code style={{ fontSize: 12 }}>{id.slice(0, 8)}</code>
        </Tooltip>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'test_type',
      key: 'test_type',
      width: 100,
      render: (type: string) => <Tag>{type || '-'}</Tag>,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>{priority || 'medium'}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{status || 'active'}</Tag>
      ),
    },
    {
      title: '前置条件',
      dataIndex: 'preconditions',
      key: 'preconditions',
      width: 150,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => {
        const items: MenuProps['items'] = [
          {
            key: 'edit',
            icon: <EditOutlined />,
            label: '编辑',
            onClick: () => onEdit?.(record),
          },
          {
            key: 'run',
            icon: <PlayCircleOutlined />,
            label: '执行',
            onClick: () => onRun?.(record),
          },
          { type: 'divider' },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: '删除',
            danger: true,
            onClick: () => {
              Modal.confirm({
                title: '确认删除',
                content: `确定删除用例「${record.title}」吗？`,
                onOk: () => onDelete?.(record),
              });
            },
          },
        ];

        return (
          <Space size="small">
            <Button
              size="small"
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => onRun?.(record)}
            />
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => onEdit?.(record)}
            />
            <Dropdown menu={{ items }} trigger={['click']}>
              <Button size="small" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  const rowSelection = onSelectionChange ? {
    selectedRowKeys: selectedKeys,
    onChange: handleSelectionChange,
  } : undefined;

  return (
    <div>
      {selectedKeys.length > 0 && onBatchRun && (
        <div style={{ marginBottom: 16 }}>
          <Space>
            <span>已选择 {selectedKeys.length} 项</span>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={() => {
                const selectedCases = dataSource.filter(c => selectedKeys.includes(c.id));
                onBatchRun(selectedCases);
              }}
            >
              批量执行
            </Button>
            <Button onClick={() => setSelectedKeys([])}>
              清空选择
            </Button>
          </Space>
        </div>
      )}

      <Table
        columns={columns}
        dataSource={dataSource}
        rowKey="id"
        loading={loading}
        rowSelection={rowSelection}
        pagination={{
          current: page,
          pageSize,
          total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条`,
        }}
        onChange={handleTableChange}
        scroll={{ x: 1000 }}
      />
    </div>
  );
}
