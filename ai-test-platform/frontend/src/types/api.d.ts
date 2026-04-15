/**
 * API 相关类型定义
 */

/**
 * 通用响应结构
 */
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

/**
 * 分页请求参数
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
  skip?: number;
  limit?: number;
}

/**
 * 分页响应结构
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * 查询参数
 */
export interface QueryParams {
  [key: string]: string | number | boolean | undefined;
}

/**
 * 请求配置
 */
export interface RequestConfig {
  headers?: Record<string, string>;
  params?: QueryParams;
  timeout?: number;
}

/**
 * 文件上传响应
 */
export interface UploadResponse {
  url: string;
  filename: string;
  size: number;
  type: string;
}

/**
 * WebSocket消息
 */
export interface WebSocketMessage {
  type: 'log' | 'status' | 'error' | 'complete';
  data: any;
  timestamp: string;
}

/**
 * 执行日志消息
 */
export interface ExecutionLogMessage {
  run_id: string;
  level: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
}

/**
 * 执行状态消息
 */
export interface ExecutionStatusMessage {
  run_id: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  progress?: number;
  duration?: number;
}
