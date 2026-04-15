import { useState, useCallback, useRef } from 'react';
import { message } from 'antd';

interface AsyncRunOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  onFinally?: () => void;
}

interface AsyncRunResult<T> {
  run: (...args: any[]) => Promise<T | undefined>;
  loading: boolean;
  error: Error | null;
  data: T | null;
  reset: () => void;
}

export function useAsyncRun<T>(
  asyncFunction: (...args: any[]) => Promise<T>,
  options: AsyncRunOptions<T> = {},
): AsyncRunResult<T> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const run = useCallback(
    async (...args: any[]) => {
      // 取消之前的请求
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      setLoading(true);
      setError(null);

      try {
        const result = await asyncFunction(...args);
        setData(result as T);
        options.onSuccess?.(result as T);
        return result as T;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options.onError?.(error);
        message.error(error.message || '操作失败');
        return undefined;
      } finally {
        setLoading(false);
        options.onFinally?.();
      }
    },
    [asyncFunction, options],
  );

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setData(null);
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    run,
    loading,
    error,
    data,
    reset,
  };
}
