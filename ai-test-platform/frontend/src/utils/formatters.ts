/**
 * 格式化工具函数
 */

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 格式化时长（毫秒）
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
  const hours = Math.floor(ms / 3600000);
  const minutes = Math.floor((ms % 3600000) / 60000);
  return `${hours}h ${minutes}m`;
}

/**
 * 格式化相对时间
 */
export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const target = new Date(date);
  const diff = now.getTime() - target.getTime();

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  const weeks = Math.floor(days / 7);
  const months = Math.floor(days / 30);

  if (seconds < 60) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  if (weeks < 4) return `${weeks}周前`;
  if (months < 12) return `${months}个月前`;

  return target.toLocaleDateString();
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

/**
 * 格式化百分比
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 格式化通过率
 */
export function formatPassRate(passed: number, failed: number): string {
  const total = passed + failed;
  if (total === 0) return '-';
  return formatPercentage(passed / total);
}

/**
 * 截断文本
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}

/**
 * 截断SHA
 */
export function truncateSHA(sha: string, length: number = 8): string {
  return sha.slice(0, length);
}

/**
 * 首字母大写
 */
export function capitalize(text: string): string {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * 转换为标题大小写
 */
export function toTitleCase(text: string): string {
  return text.replace(/\b\w/g, char => char.toUpperCase());
}

/**
 * 格式化测试类型
 */
export function formatTestType(type: string): string {
  const typeMap: Record<string, string> = {
    api: '接口测试',
    web: 'Web UI测试',
    mobile: '移动端测试',
    unit: '单元测试',
    integration: '集成测试',
  };
  return typeMap[type] || type;
}

/**
 * 格式化平台
 */
export function formatPlatform(platform: string): string {
  const platformMap: Record<string, string> = {
    android: 'Android',
    ios: 'iOS',
    web: 'Web',
    api: 'API',
  };
  return platformMap[platform] || platform;
}

/**
 * 格式化状态
 */
export function formatStatus(status: string): string {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    running: '执行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消',
    online: '在线',
    offline: '离线',
    busy: '忙碌',
  };
  return statusMap[status] || status;
}
