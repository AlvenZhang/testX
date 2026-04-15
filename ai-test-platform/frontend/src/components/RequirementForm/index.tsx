import { useEffect } from 'react';
import { Form, Input, Select, Upload, Button, Space, Card, message } from 'antd';
import { UploadOutlined, FileTextOutlined, LinkOutlined } from '@ant-design/icons';
import type { Requirement } from '../../types';

const { TextArea } = Input;
const { Option } = Select;

interface RequirementFormProps {
  initialValues?: Partial<Requirement>;
  onSubmit: (values: RequirementFormValues) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
}

export interface RequirementFormValues {
  title: string;
  description?: string;
  priority?: string;
  type?: string;
  attachments?: Array<{ name: string; url: string; size: number; type: string }>;
}

export function RequirementForm({ initialValues, onSubmit, onCancel, loading }: RequirementFormProps) {
  const [form] = Form.useForm<RequirementFormValues>();

  useEffect(() => {
    if (initialValues) {
      form.setFieldsValue(initialValues);
    }
  }, [initialValues, form]);

  const handleFinish = async (values: RequirementFormValues) => {
    try {
      await onSubmit(values);
      message.success('保存成功');
    } catch {
      message.error('保存失败');
    }
  };

  const normFile = (e: any) => {
    if (Array.isArray(e)) {
      return e;
    }
    return e?.fileList;
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleFinish}
      initialValues={initialValues}
    >
      <Card title={<Space><FileTextOutlined /> 基本信息</Space>}>
        <Form.Item
          name="title"
          label="需求标题"
          rules={[{ required: true, message: '请输入需求标题' }]}
        >
          <Input placeholder="请输入需求标题" maxLength={500} showCount />
        </Form.Item>

        <Form.Item
          name="description"
          label="需求描述"
        >
          <TextArea
            placeholder="请输入需求详细描述"
            rows={6}
            showCount
            maxLength={5000}
          />
        </Form.Item>

        <Form.Item name="type" label="需求类型" initialValue="feature">
          <Select>
            <Option value="feature">
              <span>功能需求</span>
            </Option>
            <Option value="bugfix">
              <span>缺陷修复</span>
            </Option>
            <Option value="improvement">
              <span>优化改进</span>
            </Option>
            <Option value="other">
              <span>其他</span>
            </Option>
          </Select>
        </Form.Item>

        <Form.Item name="priority" label="优先级" initialValue="medium">
          <Select>
            <Option value="critical">紧急</Option>
            <Option value="high">高</Option>
            <Option value="medium">中</Option>
            <Option value="low">低</Option>
          </Select>
        </Form.Item>
      </Card>

      <Card title={<Space><UploadOutlined /> 附件</Space>} style={{ marginTop: 16 }}>
        <Form.Item
          name="attachments"
          valuePropName="fileList"
          getValueFromEvent={normFile}
        >
          <Upload.Dragger
            name="files"
            multiple
            action="/api/v1/requirements/upload"
            accept=".pdf,.doc,.docx,.md,.txt"
            maxCount={10}
            beforeUpload={() => false} // 手动上传
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽上传需求文档</p>
            <p className="ant-upload-hint">支持 PDF、Word、Markdown、TXT 格式，单个文件不超过10MB</p>
          </Upload.Dragger>
        </Form.Item>
      </Card>

      <Card title={<Space><LinkOutlined /> Git关联</Space>} style={{ marginTop: 16 }}>
        <Form.Item name="git_commit_sha" label="Git Commit SHA">
          <Input placeholder="例如: abc123def456..." />
        </Form.Item>

        <Form.Item name="git_pr_number" label="PR/MR 编号">
          <Input type="number" placeholder="例如: 123" />
        </Form.Item>

        <Form.Item name="git_diff_url" label="Diff 链接">
          <Input placeholder="例如: https://github.com/xxx/xxx/pull/123" />
        </Form.Item>
      </Card>

      <Form.Item style={{ marginTop: 16 }}>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            保存
          </Button>
          {onCancel && (
            <Button onClick={onCancel}>
              取消
            </Button>
          )}
        </Space>
      </Form.Item>
    </Form>
  );
}
