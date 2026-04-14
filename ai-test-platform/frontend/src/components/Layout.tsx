import { Layout as AntLayout, Menu } from 'antd';
import { ProjectOutlined, FileTextOutlined, ApiOutlined, BugOutlined, ExperimentOutlined, FileSearchOutlined, CodeOutlined } from '@ant-design/icons';
import { useState } from 'react';

const { Header, Content, Sider } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
  selectedKey: string;
  onMenuClick: (key: string) => void;
}

export function Layout({ children, selectedKey, onMenuClick }: LayoutProps) {
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { key: 'projects', icon: <ProjectOutlined />, label: '项目' },
    { key: 'requirements', icon: <FileTextOutlined />, label: '需求' },
    { key: 'testcases', icon: <BugOutlined />, label: '用例' },
    { key: 'testcode', icon: <CodeOutlined />, label: '代码' },
    { key: 'testplans', icon: <ExperimentOutlined />, label: '方案' },
    { key: 'testruns', icon: <ApiOutlined />, label: '运行' },
    { key: 'reports', icon: <FileSearchOutlined />, label: '报告' },
  ];

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ color: 'white', fontSize: 18, fontWeight: 'bold' }}>
        AI 自动化测试平台
      </Header>
      <AntLayout>
        <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
          <Menu
            theme="dark"
            selectedKeys={[selectedKey]}
            mode="inline"
            items={menuItems}
            onClick={({ key }) => onMenuClick(key)}
          />
        </Sider>
        <Content style={{ padding: 24 }}>{children}</Content>
      </AntLayout>
    </AntLayout>
  );
}
