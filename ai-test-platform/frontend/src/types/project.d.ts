/**
 * 项目相关类型定义
 */

/**
 * 项目角色
 */
export type ProjectRole = 'viewer' | 'editor' | 'executor' | 'admin';

/**
 * 项目配置
 */
export interface ProjectConfig {
  test_types?: ('api' | 'web' | 'mobile' | 'unit')[];
  default_framework?: string;
  api_base_url?: string;
  android_package?: string;
  ios_bundle?: string;
  [key: string]: any;
}

/**
 * 项目成员
 */
export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string;
  user?: User;
  role: ProjectRole;
  created_at: string;
  updated_at: string;
}

/**
 * 项目基础信息
 */
export interface ProjectBase {
  name: string;
  description?: string;
  git_url?: string;
  config?: ProjectConfig;
}

/**
 * 创建项目
 */
export interface ProjectCreate extends ProjectBase {
  // 基础字段
}

/**
 * 更新项目
 */
export interface ProjectUpdate {
  name?: string;
  description?: string;
  git_url?: string;
  config?: ProjectConfig;
}

/**
 * 项目列表项
 */
export interface ProjectListItem {
  id: string;
  name: string;
  description?: string;
  git_url?: string;
  config?: ProjectConfig;
  member_count?: number;
  requirement_count?: number;
  created_at: string;
  updated_at: string;
}

/**
 * 项目详情
 */
export interface Project extends ProjectListItem {
  members?: ProjectMember[];
  created_by?: string;
}
