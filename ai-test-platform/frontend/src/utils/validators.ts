/**
 * 验证工具函数
 */

/**
 * 验证必填
 */
export function required(value: any, fieldName: string = '字段'): boolean {
  if (value === null || value === undefined || value === '') {
    return false;
  }
  if (Array.isArray(value) && value.length === 0) {
    return false;
  }
  return true;
}

/**
 * 验证邮箱格式
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * 验证URL格式
 */
export function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证Git仓库URL
 */
export function isValidGitUrl(url: string): boolean {
  const gitPatterns = [
    /^https?:\/\/github\.com\/[\w-]+\/[\w.-]+(\.git)?$/i,
    /^https?:\/\/gitlab\.com\/[\w-]+\/[\w.-]+(\.git)?$/i,
    /^https?:\/\/gitee\.com\/[\w-]+\/[\w.-]+(\.git)?$/i,
    /^git@github\.com:[\w-]+\/[\w.-]+\.git$/i,
    /^git@gitlab\.com:[\w-]+\/[\w.-]+\.git$/i,
  ];
  return gitPatterns.some(pattern => pattern.test(url));
}

/**
 * 验证Git Commit SHA
 */
export function isValidCommitSHA(sha: string): boolean {
  return /^[a-f0-9]{7,40}$/i.test(sha);
}

/**
 * 验证PR/MR编号
 */
export function isValidPRNumber(pr: string | number): boolean {
  const num = typeof pr === 'string' ? parseInt(pr, 10) : pr;
  return Number.isInteger(num) && num > 0;
}

/**
 * 验证手机号（中国大陆）
 */
export function isValidPhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/;
  return phoneRegex.test(phone);
}

/**
 * 验证密码强度
 */
export function isStrongPassword(password: string): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('密码长度至少8位');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('需要包含小写字母');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('需要包含大写字母');
  }
  if (!/\d/.test(password)) {
    errors.push('需要包含数字');
  }
  if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('需要包含特殊字符');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * 验证文件名（不包含非法字符）
 */
export function isValidFileName(fileName: string): boolean {
  const invalidChars = /[<>:"/\\|?*\x00-\x1f]/;
  return !invalidChars.test(fileName) && fileName.length > 0 && fileName.length <= 255;
}

/**
 * 验证文件大小
 */
export function isValidFileSize(size: number, maxSizeMB: number = 10): boolean {
  return size <= maxSizeMB * 1024 * 1024;
}

/**
 * 验证文件类型
 */
export function isValidFileType(
  fileType: string,
  allowedTypes: string[] = ['pdf', 'doc', 'docx', 'md', 'txt'],
): boolean {
  const extension = fileType.split('/').pop()?.toLowerCase() || '';
  return allowedTypes.includes(extension);
}

/**
 * 验证代码片段
 */
export function isValidCodeSnippet(code: string): boolean {
  // 至少10个字符且不是纯空白
  return code.trim().length >= 10;
}

/**
 * 验证JSON字符串
 */
export function isValidJSON(str: string): boolean {
  try {
    JSON.parse(str);
    return true;
  } catch {
    return false;
  }
}

/**
 * 验证优先级
 */
export function isValidPriority(priority: string): boolean {
  return ['low', 'medium', 'high', 'critical'].includes(priority);
}

/**
 * 验证状态
 */
export function isValidStatus(status: string): boolean {
  return ['pending', 'running', 'success', 'failed', 'cancelled'].includes(status);
}

/**
 * 验证平台
 */
export function isValidPlatform(platform: string): boolean {
  return ['android', 'ios', 'web', 'api'].includes(platform);
}

/**
 * 验证测试类型
 */
export function isValidTestType(testType: string): boolean {
  return ['api', 'web', 'mobile', 'unit', 'integration'].includes(testType);
}
