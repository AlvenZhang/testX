# AI 自动化测试平台 - 阶段实现详细计划

> 本文件包含所有待实现功能的详细实现方案，供 AI 助手读取并实现。

---

## 阶段二：AI 服务增强

### 2.1 AI 代码修复服务

**文件**: `backend/app/services/code_fix_service.py`

```python
"""AI 代码修复服务 - 自动修复测试代码错误"""
from typing import Dict, Optional
import json

class CodeFixService:
    """AI 代码修复服务"""

    def __init__(self):
        self.ai_service = AIService()

    async def fix_test_code(
        self,
        failed_code: str,
        error_message: str,
        test_type: str = "api"  # api/web/mobile
    ) -> Dict:
        """
        分析测试失败原因并生成修复后的代码

        Args:
            failed_code: 失败的测试代码
            error_message: 错误信息
            test_type: 测试类型

        Returns:
            {
                "fixed_code": "修复后的代码",
                "explanation": "修复说明",
                "original_error": "原错误"
            }
        """
        prompt = f"""分析以下测试代码的错误并修复：

错误信息：
{error_message}

失败的测试代码：
{failed_code}

测试类型：{test_type}

请分析错误原因并生成修复后的代码。返回 JSON 格式：
{{
    "fixed_code": "修复后的完整代码",
    "explanation": "修复说明",
    "original_error": "错误原因分析"
}}
"""
        response = await self.ai_service.chat([
            {"role": "system", "content": "你是一个专业的测试工程师，擅长修复测试代码问题。"},
            {"role": "user", "content": prompt}
        ])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "fixed_code": failed_code,
                "explanation": "无法解析AI响应",
                "original_error": error_message
            }

    async def suggest_fixes(
        self,
        code: str,
        test_type: str
    ) -> list[str]:
        """获取代码改进建议"""
        # ... 返回建议列表
```

### 2.2 AI 服务优化

**文件**: `backend/app/services/ai_service.py` (需增强)

需要添加以下功能：

1. **Redis 缓存**
```python
# 在 AIService.__init__ 中添加
self.redis_client = redis.from_url(settings.redis_url)
self.cache_ttl = 3600  # 缓存1小时

async def chat_with_cache(self, messages: list, cache_key: str = None) -> str:
    """带缓存的 chat"""
    if cache_key:
        cached = await self.redis_client.get(cache_key)
        if cached:
            return cached.decode()

    response = await self.chat(messages)

    if cache_key and response:
        await self.redis_client.setex(cache_key, self.cache_ttl, response)

    return response
```

2. **重试机制**
```python
async def chat_with_retry(self, messages: list, max_attempts: int = 3) -> str:
    """带指数退避的重试"""
    for attempt in range(max_attempts):
        try:
            return await self.chat(messages)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数退避
```

---

## 阶段三：前端能力提升

### 3.1 Monaco Editor 组件

**文件**: `frontend/src/components/MonacoEditor.tsx`

```typescript
import Editor from '@monaco-editor/react';
import { Card } from 'antd';

interface MonacoEditorProps {
  value: string;
  onChange?: (value: string) => void;
  language?: string;  // python, javascript, json, etc.
  readOnly?: boolean;
  height?: string | number;
}

export function MonacoEditor({
  value,
  onChange,
  language = 'python',
  readOnly = false,
  height = 400
}: MonacoEditorProps) {
  return (
    <Card bodyStyle={{ padding: 0 }}>
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={(v) => onChange?.(v || '')}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />
    </Card>
  );
}
```

**安装依赖**: `npm install @monaco-editor/react`

### 3.2 DiffViewer 组件

**文件**: `frontend/src/components/DiffViewer.tsx`

```typescript
import { Card, Tag } from 'antd';

interface DiffViewerProps {
  original: string;  // 原始代码
  modified: string;  // 修改后代码
  title?: string;
}

export function DiffViewer({ original, modified, title }: DiffViewerProps) {
  // 使用 diff 算法计算差异
  // 可使用: npm install diff

  const renderDiff = () => {
    // 实现行级别的 diff 显示
    // 绿色: 新增行, 红色: 删除行
  };

  return (
    <Card title={title || '代码对比'}>
      <div style={{ fontFamily: 'monospace', fontSize: 13 }}>
        {renderDiff()}
      </div>
    </Card>
  );
}
```

**安装依赖**: `npm install diff`

### 3.3 DeviceSelector 组件

**文件**: `frontend/src/components/DeviceSelector.tsx`

```typescript
import { Select, Space, Tag, Badge } from 'antd';
import type { Device } from '../types';

interface DeviceSelectorProps {
  devices: Device[];
  selectedDeviceId?: string;
  onSelect: (deviceId: string) => void;
  platform?: 'android' | 'ios' | 'all';
}

export function DeviceSelector({
  devices,
  selectedDeviceId,
  onSelect,
  platform = 'all'
}: DeviceSelectorProps) {
  const filteredDevices = platform === 'all'
    ? devices
    : devices.filter(d => d.platform === platform);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'success';
      case 'busy': return 'warning';
      case 'offline': return 'error';
      default: return 'default';
    }
  };

  return (
    <Select
      placeholder="选择设备"
      value={selectedDeviceId}
      onChange={onSelect}
      style={{ width: 300 }}
    >
      {filteredDevices.map(device => (
        <Select.Option key={device.id} value={device.id}>
          <Space>
            <Tag color={device.platform === 'android' ? 'green' : 'blue'}>
              {device.platform.toUpperCase()}
            </Tag>
            <span>{device.name}</span>
            <Badge status={getStatusColor(device.status)} />
            <span style={{ color: '#999' }}>{device.version}</span>
          </Space>
        </Select.Option>
      ))}
    </Select>
  );
}
```

### 3.4 Charts 图表组件

**文件**: `frontend/src/components/Charts.tsx`

```typescript
import { Card } from 'antd';
import ReactECharts from 'echarts-for-react';

interface TestTrendChartProps {
  data: Array<{
    date: string;
    passed: number;
    failed: number;
    total: number;
  }>;
}

export function TestTrendChart({ data }: TestTrendChartProps) {
  const option = {
    title: { text: '测试趋势' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['通过', '失败', '总计'] },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date)
    },
    yAxis: { type: 'value' },
    series: [
      { name: '通过', type: 'line', data: data.map(d => d.passed), itemStyle: { color: '#52c41a' } },
      { name: '失败', type: 'line', data: data.map(d => d.failed), itemStyle: { color: '#ff4d4f' } },
      { name: '总计', type: 'bar', data: data.map(d => d.total) }
    ]
  };

  return (
    <Card>
      <ReactECharts option={option} style={{ height: 300 }} />
    </Card>
  );
}

interface PassRateChartProps {
  passed: number;
  failed: number;
}

export function PassRateChart({ passed, failed }: PassRateChartProps) {
  const total = passed + failed;
  const rate = total > 0 ? (passed / total * 100).toFixed(1) : 0;

  const option = {
    title: { text: `通过率 ${rate}%`, left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: passed, name: '通过', itemStyle: { color: '#52c41a' } },
        { value: failed, name: '失败', itemStyle: { color: '#ff4d4f' } }
      ]
    }]
  };

  return (
    <Card>
      <ReactECharts option={option} style={{ height: 250 }} />
    </Card>
  );
}
```

**安装依赖**: `npm install echarts echarts-for-react`

---

## 阶段四：移动端设备管理

### 4.1 ADB 设备管理

**文件**: `android-device-farm/adb_manager.py`

```python
"""Android 设备管理 - ADB"""
import subprocess
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AndroidDevice:
    udid: str
    name: str
    version: str
    status: str  # online/offline
    ip: Optional[str] = None

class ADBManager:
    """ADB 设备管理器"""

    def list_devices(self) -> List[AndroidDevice]:
        """列出所有连接的 Android 设备"""
        result = subprocess.run(
            ['adb', 'devices', '-l'],
            capture_output=True,
            text=True
        )
        devices = []
        for line in result.stdout.strip().split('\n')[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    udid = parts[0]
                    status = parts[1]
                    # 解析设备信息
                    info = self._get_device_info(udid)
                    devices.append(AndroidDevice(
                        udid=udid,
                        name=info.get('model', 'Unknown'),
                        version=info.get('version', 'Unknown'),
                        status=status
                    ))
        return devices

    def _get_device_info(self, udid: str) -> dict:
        """获取设备详细信息"""
        info = {}
        # adb shell getprop ...
        return info

    def connect_wifi(self, ip: str, port: int = 5555) -> bool:
        """通过网络连接设备"""
        result = subprocess.run(
            ['adb', 'connect', f'{ip}:{port}'],
            capture_output=True,
            text=True
        )
        return 'connected' in result.stdout

    def screenshot(self, udid: str, output_path: str) -> bool:
        """截图"""
        result = subprocess.run(
            ['adb', '-s', udid, 'exec-out', 'screenshot', '-'],
            capture_output=True
        )
        if result.returncode == 0:
            with open(output_path, 'wb') as f:
                f.write(result.stdout)
            return True
        return False
```

### 4.2 Appium Android 服务

**文件**: `android-device-farm/appium_android.py`

```python
"""Appium Android 测试服务"""
from appium import webdriver
from appium.webdriver.webdriver import WebDriver
from .adb_manager import ADBManager

class AppiumAndroidService:
    """Appium Android 服务"""

    def __init__(self):
        self.adb = ADBManager()
        self.driver: Optional[WebDriver] = None

    def create_driver(self, udid: str) -> WebDriver:
        """创建 Appium WebDriver"""
        caps = {
            "platformName": "Android",
            "automationName": "UiAutomator2",
            "udid": udid,
            "noReset": True,
        }
        self.driver = webdriver.Remote(
            "http://localhost:4723/wd/hub",
            desired_capabilities=caps
        )
        return self.driver

    def execute_test(self, udid: str, test_script: str) -> dict:
        """执行 Android UI 测试"""
        driver = self.create_driver(udid)
        try:
            # 执行测试脚本
            exec(test_script)
            return {"status": "passed"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            driver.quit()
```

### 4.3 XCRun 模拟器管理

**文件**: `ios-device-farm/xcrun_manager.py`

```python
"""iOS 模拟器管理 - XCRun"""
import subprocess
import plistlib
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class iOSDevice:
    udid: str
    name: str
    version: str
    is_simulator: bool

class XCRunManager:
    """XCRun 模拟器管理器"""

    def list_devices(self) -> List[iOSDevice]:
        """列出所有 iOS 设备/模拟器"""
        result = subprocess.run(
            ['xcrun', 'simctl', 'list', 'devices', 'available'],
            capture_output=True,
            text=True
        )
        devices = []
        # 解析输出...
        return devices

    def boot_device(self, udid: str) -> bool:
        """启动模拟器"""
        result = subprocess.run(
            ['xcrun', 'simctl', 'boot', udid],
            capture_output=True
        )
        return result.returncode == 0

    def install_app(self, udid: str, app_path: str) -> bool:
        """安装应用到模拟器"""
        result = subprocess.run(
            ['xcrun', 'simctl', 'install', udid, app_path],
            capture_output=True
        )
        return result.returncode == 0

    def screenshot(self, udid: str, output_path: str) -> bool:
        """截图"""
        result = subprocess.run(
            ['xcrun', 'simctl', 'io', udid, 'screenshot', output_path],
            capture_output=True
        )
        return result.returncode == 0
```

### 4.4 Appium iOS 服务

**文件**: `ios-device-farm/appium_ios.py`

```python
"""Appium iOS 测试服务"""
from appium import webdriver
from appium.webdriver.webdriver import WebDriver
from .xcrun_manager import XCRunManager

class AppiumIOSService:
    """Appium iOS 服务"""

    def __init__(self):
        self.xcrun = XCRunManager()
        self.driver: Optional[WebDriver] = None

    def create_driver(self, udid: str, is_simulator: bool = True) -> WebDriver:
        """创建 Appium WebDriver"""
        caps = {
            "platformName": "iOS",
            "automationName": "XCUITest",
            "udid": udid,
            "noReset": True,
            "useNewWDA": True,
        }
        if is_simulator:
            caps["simulator"] = True

        self.driver = webdriver.Remote(
            "http://localhost:4723/wd/hub",
            desired_capabilities=caps
        )
        return self.driver

    def execute_test(self, udid: str, test_script: str, is_simulator: bool = True) -> dict:
        """执行 iOS UI 测试"""
        driver = self.create_driver(udid, is_simulator)
        try:
            exec(test_script)
            return {"status": "passed"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            driver.quit()
```

---

## 阶段五：部署与运维

### 5.1 Frontend Dockerfile

**文件**: `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 5.2 nginx.conf

**文件**: `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5.3 更新 docker-compose.yml

在现有 `docker-compose.yml` 中添加：

```yaml
services:
  # ... 现有服务 ...

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - aitest-network

networks:
  aitest-network:
    external: true  # 改为使用已有网络
```

---

## 类型定义补充

**文件**: `frontend/src/types/index.ts` 或在现有 types.ts 中添加

```typescript
// 设备类型
export interface Device {
  id: string;
  name: string;
  platform: 'android' | 'ios';
  version: string;
  status: 'online' | 'offline' | 'busy';
  capabilities?: Record<string, any>;
}

// 移动端执行结果
export interface MobileExecutionResult {
  run_id: string;
  status: 'success' | 'failed' | 'error';
  exit_code: number;
  logs: string;
  duration_ms: number;
  device_udid: string;
  platform: 'android' | 'ios';
}
```

---

## API 集成补充

**文件**: `frontend/src/services/api.ts`

添加移动端执行 API：

```typescript
// Mobile Executions
export const mobileExecutionApi = {
  run: (data: {
    code_content: string;
    device_id: string;
    platform: 'android' | 'ios';
    test_type?: string;
  }) => api.post<MobileExecutionResult>('/mobile-executions/run', data),

  listDevices: (platform?: 'android' | 'ios') =>
    api.get<{ devices: Device[]; total: number }>('/mobile-executions/devices', {
      params: platform ? { platform } : {}
    }),

  getStatus: (runId: string) =>
    api.get(`/mobile-executions/status/${runId}`),

  getLogs: (runId: string) =>
    api.get(`/mobile-executions/logs/${runId}`),
};
```

---

## 注意事项

1. **AI 服务需要配置**: 确保 `AI_API_KEY` 环境变量已设置
2. **Appium 需要独立运行**: 移动端测试需要先启动 Appium 服务器
3. **iOS 测试仅限 macOS**: XCRun 命令只能在 macOS 上运行
4. **Docker 网络**: 使用 `docker network create aitest-network` 预先创建网络
5. **前端组件按需引入**: Monaco Editor 等组件较大，按需加载
