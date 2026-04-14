import { useMemo } from 'react';
import { Card, Tag } from 'antd';

export interface DiffViewerProps {
  original: string;
  modified: string;
  title?: string;
  language?: string;
}

interface DiffLine {
  type: 'added' | 'removed' | 'unchanged';
  content: string;
  lineNumber: number;
}

export function DiffViewer({
  original,
  modified,
  title = '代码对比',
  language = 'python',
}: DiffViewerProps) {
  const diffLines = useMemo(() => {
    const originalLines = original.split('\n');
    const modifiedLines = modified.split('\n');
    const result: DiffLine[] = [];

    // 简单的行对比算法
    let oIndex = 0;
    let mIndex = 0;
    let lineNum = 1;

    while (oIndex < originalLines.length || mIndex < modifiedLines.length) {
      if (oIndex >= originalLines.length) {
        // 剩余的行都是新增
        result.push({
          type: 'added',
          content: modifiedLines[mIndex],
          lineNumber: lineNum++,
        });
        mIndex++;
      } else if (mIndex >= modifiedLines.length) {
        // 剩余的行都是删除
        result.push({
          type: 'removed',
          content: originalLines[oIndex],
          lineNumber: lineNum++,
        });
        oIndex++;
      } else if (originalLines[oIndex] === modifiedLines[mIndex]) {
        // 相同的行
        result.push({
          type: 'unchanged',
          content: originalLines[oIndex],
          lineNumber: lineNum++,
        });
        oIndex++;
        mIndex++;
      } else {
        // 不相同，先尝试匹配后面的行
        const oRemaining = originalLines.slice(oIndex);
        const mRemaining = modifiedLines.slice(mIndex);
        let matchIndex = -1;

        // 找下一个匹配的行
        for (let i = 0; i < Math.min(oRemaining.length, mRemaining.length); i++) {
          if (oRemaining[i] === mRemaining[i]) {
            matchIndex = i;
            break;
          }
        }

        if (matchIndex > 0) {
          // 有部分匹配
          for (let i = 0; i < matchIndex; i++) {
            result.push({
              type: 'removed',
              content: originalLines[oIndex + i],
              lineNumber: lineNum++,
            });
            result.push({
              type: 'added',
              content: modifiedLines[mIndex + i],
              lineNumber: lineNum++,
            });
          }
          oIndex += matchIndex;
          mIndex += matchIndex;
        } else {
          // 完全不匹配
          result.push({
            type: 'removed',
            content: originalLines[oIndex],
            lineNumber: lineNum++,
          });
          oIndex++;
        }
      }
    }

    return result;
  }, [original, modified]);

  const stats = useMemo(() => {
    const added = diffLines.filter((l) => l.type === 'added').length;
    const removed = diffLines.filter((l) => l.type === 'removed').length;
    return { added, removed };
  }, [diffLines]);

  const getLineStyle = (type: DiffLine['type']) => {
    switch (type) {
      case 'added':
        return { backgroundColor: '#f6ffed', color: '#52c41a' };
      case 'removed':
        return { backgroundColor: '#fff1f0', color: '#ff4d4f' };
      default:
        return { backgroundColor: 'transparent', color: '#666' };
    }
  };

  const getLinePrefix = (type: DiffLine['type']) => {
    switch (type) {
      case 'added':
        return '+';
      case 'removed':
        return '-';
      default:
        return ' ';
    }
  };

  return (
    <Card
      title={title}
      extra={
        <div style={{ display: 'flex', gap: 8 }}>
          <Tag color="green">+{stats.added}</Tag>
          <Tag color="red">-{stats.removed}</Tag>
        </div>
      }
      styles={{ body: { padding: 0 } }}
    >
      <div
        style={{
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace',
          fontSize: 13,
          lineHeight: 1.6,
          overflow: 'auto',
          maxHeight: 500,
        }}
      >
        {diffLines.map((line, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              ...getLineStyle(line.type),
            }}
          >
            <span
              style={{
                width: 50,
                textAlign: 'right',
                paddingRight: 12,
                color: '#999',
                userSelect: 'none',
                borderRight: '1px solid #eee',
                flexShrink: 0,
              }}
            >
              {line.lineNumber}
            </span>
            <span
              style={{
                width: 20,
                textAlign: 'center',
                userSelect: 'none',
                flexShrink: 0,
              }}
            >
              {getLinePrefix(line.type)}
            </span>
            <span
              style={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all',
                paddingLeft: 8,
              }}
            >
              {line.content || ' '}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default DiffViewer;
