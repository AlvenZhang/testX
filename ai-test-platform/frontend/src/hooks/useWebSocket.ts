import { useCallback, useEffect, useRef, useState } from 'react';

export interface WebSocketMessage {
  type: 'log' | 'status' | 'error' | 'complete';
  data: string;
  timestamp: number;
}

export interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  messages: WebSocketMessage[];
  connect: (runId: string) => void;
  disconnect: () => void;
  send: (message: string) => void;
  clearMessages: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    autoReconnect = true,
    reconnectInterval = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const runIdRef = useRef<string | null>(null);

  const connect = useCallback((runId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      disconnect();
    }

    runIdRef.current = runId;
    setIsConnecting(true);

    const wsUrl = `ws://localhost:8000/ws/execution/${runId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
      setIsConnecting(false);
      onConnect?.();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const message: WebSocketMessage = {
          type: data.type || 'log',
          data: data.data || event.data,
          timestamp: data.timestamp || Date.now(),
        };
        setMessages((prev) => [...prev, message]);
        onMessage?.(message);
      } catch {
        // 如果不是 JSON，当作普通日志处理
        const message: WebSocketMessage = {
          type: 'log',
          data: event.data,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, message]);
        onMessage?.(message);
      }
    };

    ws.onerror = (error) => {
      onError?.(error);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsConnecting(false);
      onDisconnect?.();

      // 自动重连
      if (autoReconnect && runIdRef.current) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          if (runIdRef.current) {
            connect(runIdRef.current);
          }
        }, reconnectInterval);
      }
    };

    wsRef.current = ws;
  }, [autoReconnect, onConnect, onDisconnect, onError, onMessage, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    runIdRef.current = null;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const send = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isConnecting,
    messages,
    connect,
    disconnect,
    send,
    clearMessages,
  };
}

export default useWebSocket;
