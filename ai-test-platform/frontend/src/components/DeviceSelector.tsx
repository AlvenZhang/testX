import { Select, Space, Tag, Badge, Tooltip } from 'antd';
import type { Device } from '../types';

export interface DeviceSelectorProps {
  devices: Device[];
  selectedDeviceId?: string;
  onSelect: (deviceId: string) => void;
  platform?: 'android' | 'ios' | 'all';
  placeholder?: string;
  style?: React.CSSProperties;
}

export function DeviceSelector({
  devices,
  selectedDeviceId,
  onSelect,
  platform = 'all',
  placeholder = '选择设备',
  style,
}: DeviceSelectorProps) {
  const filteredDevices =
    platform === 'all'
      ? devices
      : devices.filter((d) => d.platform === platform);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'busy':
        return 'warning';
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const getPlatformIcon = (platform: string) => {
    return platform === 'android' ? '🤖' : '🍎';
  };

  return (
    <Select
      placeholder={placeholder}
      value={selectedDeviceId}
      onChange={onSelect}
      style={{ width: 320, ...style }}
      allowClear
      showSearch
      optionFilterProp="label"
      options={filteredDevices.map((device) => ({
        value: device.id,
        label: (
          <Space>
            <span>{getPlatformIcon(device.platform)}</span>
            <Tag
              color={device.platform === 'android' ? 'green' : 'blue'}
              style={{ marginRight: 0 }}
            >
              {device.platform.toUpperCase()}
            </Tag>
            <span style={{ fontWeight: 500 }}>{device.name}</span>
            <Badge
              status={getStatusColor(device.status)}
              text={
                <span style={{ color: '#999', fontSize: 12 }}>
                  {device.status === 'online'
                    ? '空闲'
                    : device.status === 'busy'
                    ? '占用'
                    : '离线'}
                </span>
              }
            />
            <Tooltip title={`版本: ${device.version}`}>
              <Tag style={{ marginLeft: 8 }}>{device.version}</Tag>
            </Tooltip>
          </Space>
        ),
      }))}
      notFoundContent={
        <div style={{ padding: 8, textAlign: 'center', color: '#999' }}>
          {platform === 'all' ? '暂无设备' : `暂无${platform === 'android' ? 'Android' : 'iOS'}设备`}
        </div>
      }
    />
  );
}

export interface DeviceListProps {
  devices: Device[];
  selectedDeviceId?: string;
  onSelect: (deviceId: string) => void;
  platform?: 'android' | 'ios' | 'all';
}

export function DeviceList({
  devices,
  selectedDeviceId,
  onSelect,
  platform = 'all',
}: DeviceListProps) {
  const filteredDevices =
    platform === 'all'
      ? devices
      : devices.filter((d) => d.platform === platform);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return '#52c41a';
      case 'busy':
        return '#faad14';
      case 'offline':
        return '#ff4d4f';
      default:
        return '#999';
    }
  };

  return (
    <div
      style={{
        maxHeight: 300,
        overflow: 'auto',
        border: '1px solid #f0f0f0',
        borderRadius: 8,
      }}
    >
      {filteredDevices.length === 0 ? (
        <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>
          暂无设备
        </div>
      ) : (
        filteredDevices.map((device) => (
          <div
            key={device.id}
            onClick={() => onSelect(device.id)}
            style={{
              padding: '12px 16px',
              cursor: 'pointer',
              borderBottom: '1px solid #f0f0f0',
              backgroundColor:
                selectedDeviceId === device.id ? '#f6f8ff' : 'transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <div
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: getStatusColor(device.status),
              }}
            />
            <Tag color={device.platform === 'android' ? 'green' : 'blue'}>
              {device.platform.toUpperCase()}
            </Tag>
            <span style={{ flex: 1, fontWeight: 500 }}>{device.name}</span>
            <span style={{ color: '#999', fontSize: 12 }}>{device.version}</span>
          </div>
        ))
      )}
    </div>
  );
}

export default DeviceSelector;
