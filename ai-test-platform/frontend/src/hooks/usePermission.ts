import { useState, useEffect, useCallback } from 'react';
import { useUserStore } from '../store/userStore';
import { useProjectStore } from '../store/projectStore';

type Role = 'viewer' | 'editor' | 'executor' | 'admin';

interface Permission {
  canView: boolean;
  canEdit: boolean;
  canExecute: boolean;
  canManage: boolean;
  role: Role | null;
}

export function usePermission(projectId?: string): Permission {
  const { user } = useUserStore();
  const { currentProject } = useProjectStore();
  const [permission, setPermission] = useState<Permission>({
    canView: true,
    canEdit: false,
    canExecute: false,
    canManage: false,
    role: null,
  });

  const checkPermission = useCallback(async () => {
    const targetProjectId = projectId || currentProject?.id;

    if (!user || !targetProjectId) {
      setPermission({
        canView: true,
        canEdit: false,
        canExecute: false,
        canManage: false,
        role: null,
      });
      return;
    }

    // 管理员拥有所有权限
    if (user.role === 'admin') {
      setPermission({
        canView: true,
        canEdit: true,
        canExecute: true,
        canManage: true,
        role: 'admin',
      });
      return;
    }

    // 获取用户在项目中的角色
    try {
      const response = await fetch(`/api/v1/projects/${targetProjectId}/members/me`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const member = await response.json();
        const role = member.role as Role;

        setPermission({
          canView: true,
          canEdit: role === 'editor' || role === 'admin',
          canExecute: role === 'executor' || role === 'admin',
          canManage: role === 'admin',
          role,
        });
      } else {
        setPermission({
          canView: false,
          canEdit: false,
          canExecute: false,
          canManage: false,
          role: null,
        });
      }
    } catch {
      setPermission({
        canView: true,
        canEdit: false,
        canExecute: false,
        canManage: false,
        role: null,
      });
    }
  }, [user, projectId, currentProject]);

  useEffect(() => {
    checkPermission();
  }, [checkPermission]);

  return permission;
}

export function useRequirePermission(requiredRole: Role) {
  const permission = usePermission();

  if (!permission.role) {
    return false;
  }

  const roleHierarchy: Record<Role, number> = {
    viewer: 1,
    editor: 2,
    executor: 3,
    admin: 4,
  };

  return roleHierarchy[permission.role] >= roleHierarchy[requiredRole];
}
