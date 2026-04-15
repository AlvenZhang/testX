import { useEffect, useRef } from 'react';
import { Card, Empty, Badge } from 'antd';
import './ExecutionLog.css';

interface ExecutionLogProps {
  logs: string;
}

interface LogLine {
  timestamp?: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
}

export function ExecutionLog({ logs }: ExecutionLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  if (!logs) {
    return <Empty description="暂无日志" />;
  }

  const parseLogs = (logText: string): LogLine[] => {
    const lines = logText.split('\n').filter(line => line.trim());
    return lines.map(line => {
      // 尝试解析时间戳
      const timeMatch = line.match(/^\[?(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d{3})?)\]?\s*/);
      const timestamp = timeMatch ? timeMatch[1] : undefined;
      const content = timestamp ? line.replace(timeMatch[0], '') : line;

      // 解析日志级别
      let level: LogLine['level'] = 'info';
      if (/\b(ERROR|FATAL|FAILED)\b/i.test(content)) {
        level = 'error';
      } else if (/\b(WARN|WARNING)\b/i.test(content)) {
        level = 'warning';
      } else if (/\b(SUCCESS|PASS|PASSED|✓)\b/i.test(content)) {
        level = 'success';
      }

      return { timestamp, level, message: content };
    });
  };

  const logLines = parseLogs(logs);

  const getLevelColor = (level: LogLine['level']) => {
    switch (level) {
      case 'error': return '#ff4d4f';
      case 'warning': return '#faad14';
      case 'success': return '#52c41a';
      default: return '#8c8c8c';
    }
  };

  return (
    <Card bodyStyle={{ padding: 0 }}>
      <div className="execution-log-container" ref={containerRef}>
        {logLines.map((line, index) => (
          <div key={index} className={`log-line log-${line.level}`}>
            {line.timestamp && (
              <span className="log-timestamp">{line.timestamp}</span>
            )}
            <span className="log-level-indicator" style={{ color: getLevelColor(line.level) }}>
              {line.level === 'error' ? '✗' : line.level === 'warning' ? '⚠' : line.level === 'success' ? '✓' : '•'}
            </span>
            <span className="log-message">{line.message}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
