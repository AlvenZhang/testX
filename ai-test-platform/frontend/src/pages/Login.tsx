import { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

interface LoginProps {
  onLogin: (token: string, user: { id: string; email: string; name: string }) => void;
}

export function LoginPage({ onLogin }: LoginProps) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, values);
      const { access_token, user } = res.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      message.success('登录成功');
      onLogin(access_token, user);
    } catch (err: unknown) {
      message.error((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: { email: string; name: string; password: string }) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/auth/register`, values);
      const { access_token, user } = res.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      message.success('注册成功');
      onLogin(access_token, user);
    } catch (err: unknown) {
      message.error((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
      <Card title="AI 自动化测试平台" style={{ width: 400 }}>
        <Form layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
        </Form>
        <Button type="link" onClick={() => handleRegister({ email: 'test@example.com', name: 'Test User', password: 'password123' })} block>
          注册测试账号
        </Button>
      </Card>
    </div>
  );
}
