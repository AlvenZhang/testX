import { Card } from 'antd';
import Editor, { OnMount } from '@monaco-editor/react';
import { useRef } from 'react';
import type { editor } from 'monaco-editor';

export interface MonacoEditorProps {
  value: string;
  onChange?: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  height?: string | number;
  theme?: 'vs' | 'vs-dark';
}

export function MonacoEditor({
  value,
  onChange,
  language = 'python',
  readOnly = false,
  height = 400,
  theme = 'vs-dark',
}: MonacoEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  const handleEditorMount: OnMount = (editor) => {
    editorRef.current = editor;
    // 设置编辑器选项
    editor.updateOptions({
      readOnly,
      minimap: { enabled: false },
      fontSize: 14,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      automaticLayout: true,
      tabSize: 4,
      wordWrap: 'on',
      folding: true,
      renderLineHighlight: 'all',
      scrollbar: {
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10,
      },
    });
  };

  const handleChange = (newValue: string | undefined) => {
    onChange?.(newValue || '');
  };

  return (
    <Card bodyStyle={{ padding: 0, overflow: 'hidden' }}>
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={handleChange}
        onMount={handleEditorMount}
        theme={theme}
        loading={
          <div style={{ padding: 20, color: '#999' }}>加载编辑器中...</div>
        }
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

export default MonacoEditor;
