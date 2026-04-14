import { useState, useEffect } from 'react';
import { Table, Button, Tag, message, Space, Card, Row, Col } from 'antd';
import { MobileOutlined, TabletOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

interface Device {
  id: string;
  name: string;
  platform: string;
  device_type: string;
  serial: string;
  status: string;
  os_version?: string;
  manufacturer?: string;
  model?: string;
}

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [discovering, setDiscovering] = useState(false);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/devices/`);
      setDevices(res.data);
    } catch {
      message.error('获取设备列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDiscover = async (platform: string) => {
    setDiscovering(true);
    try {
      const res = await axios.post(`${API_BASE}/devices/discover?platform=${platform}`);
      message.success(`发现 ${res.data.discovered_count} 个设备`);
      fetchDevices();
    } catch {
      message.error('发现设备失败');
    } finally {
      setDiscovering(false);
    }
  };

  useEffect(() => { fetchDevices(); }, []);

  const columns = [
    {
      title: '设备',
      key: 'device',
      render: (_: unknown, record: Device) => (
        <Space>
          {record.platform === 'android' ? <MobileOutlined /> : <TabletOutlined />}
          <span>{record.name || record.model || record.serial}</span>
        </Space>
      ),
    },
    { title: '平台', dataIndex: 'platform', key: 'platform' },
    { title: '类型', dataIndex: 'device_type', key: 'device_type' },
    { title: '序列号', dataIndex: 'serial', key: 'serial', ellipsis: true },
    { title: '系统', dataIndex: 'os_version', key: 'os_version' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={v === 'online' ? 'green' : v === 'busy' ? 'orange' : 'red'}>{v}</Tag>
      ),
    },
    { title: '厂商', dataIndex: 'manufacturer', key: 'manufacturer' },
  ];

  const androidDevices = devices.filter(d => d.platform === 'android');
  const iosDevices = devices.filter(d => d.platform === 'ios');

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card
            title="Android 设备"
            extra={
              <Button icon={<ReloadOutlined />} loading={discovering} onClick={() => handleDiscover('android')}>
                发现设备
              </Button>
            }
          >
            <p>在线: {androidDevices.filter(d => d.status === 'online').length}</p>
            <p>忙碌: {androidDevices.filter(d => d.status === 'busy').length}</p>
          </Card>
        </Col>
        <Col span={12}>
          <Card
            title="iOS 设备"
            extra={
              <Button icon={<ReloadOutlined />} loading={discovering} onClick={() => handleDiscover('ios')}>
                发现设备
              </Button>
            }
          >
            <p>在线: {iosDevices.filter(d => d.status === 'online').length}</p>
            <p>忙碌: {iosDevices.filter(d => d.status === 'busy').length}</p>
          </Card>
        </Col>
      </Row>

      <Table columns={columns} dataSource={devices} rowKey="id" loading={loading} />
    </div>
  );
}
