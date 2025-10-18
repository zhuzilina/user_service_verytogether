"""
RBAC权限定义系统
基于角色的访问控制权限定义
"""

from enum import Enum
from typing import Dict, List, Set


class Permission(Enum):
    """权限枚举定义"""
    # 用户管理权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"

    # 用户活动权限
    ACTIVITY_READ = "activity:read"
    ACTIVITY_LIST = "activity:list"

    # 角色管理权限
    ROLE_UPDATE = "role:update"
    ROLE_READ = "role:read"

    # 系统管理权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"

    # 竞赛管理权限
    COMPETITION_CREATE = "competition:create"
    COMPETITION_READ = "competition:read"
    COMPETITION_UPDATE = "competition:update"
    COMPETITION_DELETE = "competition:delete"
    COMPETITION_LIST = "competition:list"
    COMPETITION_MANAGE = "competition:manage"

    # 竞赛审核权限
    COMPETITION_REVIEW = "competition:review"
    COMPETITION_APPROVE = "competition:approve"
    COMPETITION_REJECT = "competition:reject"

    # 团队管理权限
    TEAM_CREATE = "team:create"
    TEAM_READ = "team:read"
    TEAM_UPDATE = "team:update"
    TEAM_DELETE = "team:delete"
    TEAM_LIST = "team:list"
    TEAM_MANAGE = "team:manage"

    # 成员管理权限
    MEMBER_ADD = "member:add"
    MEMBER_REMOVE = "member:remove"
    MEMBER_APPROVE = "member:approve"


class RolePermissions:
    """角色权限映射定义"""

    # 超级管理员权限 - 拥有所有权限
    SUPER_ADMIN_PERMISSIONS = {
        perm.value for perm in Permission
    }

    # 学院学科竞赛管理员权限
    COMPETITION_ADMIN_PERMISSIONS = {
        # 用户管理 - 只能查看自己
        Permission.USER_READ.value,

        # 用户活动查看 - 只能查看自己的
        Permission.ACTIVITY_READ.value,

        # 角色查看
        Permission.ROLE_READ.value,

        # 竞赛管理 - 全部权限
        Permission.COMPETITION_CREATE.value,
        Permission.COMPETITION_READ.value,
        Permission.COMPETITION_UPDATE.value,
        Permission.COMPETITION_DELETE.value,
        Permission.COMPETITION_LIST.value,
        Permission.COMPETITION_MANAGE.value,

        # 竞赛审核
        Permission.COMPETITION_REVIEW.value,
        Permission.COMPETITION_APPROVE.value,
        Permission.COMPETITION_REJECT.value,

        # 团队管理
        Permission.TEAM_CREATE.value,
        Permission.TEAM_READ.value,
        Permission.TEAM_UPDATE.value,
        Permission.TEAM_DELETE.value,
        Permission.TEAM_LIST.value,
        Permission.TEAM_MANAGE.value,

        # 成员管理
        Permission.MEMBER_ADD.value,
        Permission.MEMBER_REMOVE.value,
        Permission.MEMBER_APPROVE.value,
    }

    # 学院教师权限
    TEACHER_PERMISSIONS = {
        # 用户管理 - 只能查看自己
        Permission.USER_READ.value,

        # 用户活动查看 - 只能查看自己的
        Permission.ACTIVITY_READ.value,

        # 角色查看
        Permission.ROLE_READ.value,

        # 竞赛管理 - 基础权限
        Permission.COMPETITION_READ.value,
        Permission.COMPETITION_LIST.value,
        Permission.COMPETITION_CREATE.value,
        Permission.COMPETITION_UPDATE.value,

        # 团队管理
        Permission.TEAM_READ.value,
        Permission.TEAM_LIST.value,
        Permission.TEAM_CREATE.value,
        Permission.TEAM_UPDATE.value,

        # 成员管理 - 只能管理自己的团队
        Permission.MEMBER_ADD.value,
        Permission.MEMBER_REMOVE.value,
    }

    # 学院学生权限
    STUDENT_PERMISSIONS = {
        # 用户管理 - 只能查看自己
        Permission.USER_READ.value,

        # 用户活动 - 只能查看自己的
        Permission.ACTIVITY_READ.value,

        # 竞赛管理 - 只能查看和参与
        Permission.COMPETITION_READ.value,
        Permission.COMPETITION_LIST.value,

        # 团队管理 - 只能查看和加入
        Permission.TEAM_READ.value,
        Permission.TEAM_LIST.value,
    }


# 角色权限映射表
ROLE_PERMISSIONS_MAP: Dict[str, Set[str]] = {
    'super_admin': RolePermissions.SUPER_ADMIN_PERMISSIONS,
    'competition_admin': RolePermissions.COMPETITION_ADMIN_PERMISSIONS,
    'teacher': RolePermissions.TEACHER_PERMISSIONS,
    'student': RolePermissions.STUDENT_PERMISSIONS,
}


def get_role_permissions(role: str) -> Set[str]:
    """获取指定角色的权限集合"""
    return ROLE_PERMISSIONS_MAP.get(role, set())


def has_permission(user_role: str, required_permission: str) -> bool:
    """检查用户角色是否具有指定权限"""
    role_permissions = get_role_permissions(user_role)
    return required_permission in role_permissions


def has_any_permission(user_role: str, required_permissions: List[str]) -> bool:
    """检查用户角色是否具有任一指定权限"""
    role_permissions = get_role_permissions(user_role)
    return any(perm in role_permissions for perm in required_permissions)


def has_all_permissions(user_role: str, required_permissions: List[str]) -> bool:
    """检查用户角色是否具有所有指定权限"""
    role_permissions = get_role_permissions(user_role)
    return all(perm in role_permissions for perm in required_permissions)


def get_user_accessible_permissions(user) -> List[str]:
    """获取用户可访问的权限列表"""
    return list(get_role_permissions(user.role))


# 权限组定义 - 用于权限检查
class PermissionGroups:
    """权限组定义"""

    # 用户管理权限组
    USER_MANAGEMENT = {
        Permission.USER_CREATE.value,
        Permission.USER_READ.value,
        Permission.USER_UPDATE.value,
        Permission.USER_DELETE.value,
        Permission.USER_LIST.value,
    }

    # 竞赛管理权限组
    COMPETITION_MANAGEMENT = {
        Permission.COMPETITION_CREATE.value,
        Permission.COMPETITION_READ.value,
        Permission.COMPETITION_UPDATE.value,
        Permission.COMPETITION_DELETE.value,
        Permission.COMPETITION_LIST.value,
        Permission.COMPETITION_MANAGE.value,
    }

    # 团队管理权限组
    TEAM_MANAGEMENT = {
        Permission.TEAM_CREATE.value,
        Permission.TEAM_READ.value,
        Permission.TEAM_UPDATE.value,
        Permission.TEAM_DELETE.value,
        Permission.TEAM_LIST.value,
        Permission.TEAM_MANAGE.value,
    }

    # 系统管理权限组
    SYSTEM_MANAGEMENT = {
        Permission.SYSTEM_CONFIG.value,
        Permission.SYSTEM_MONITOR.value,
        Permission.ROLE_UPDATE.value,
    }

    # 只读权限组
    READ_ONLY = {
        Permission.USER_READ.value,
        Permission.USER_LIST.value,
        Permission.ACTIVITY_READ.value,
        Permission.ACTIVITY_LIST.value,
        Permission.ROLE_READ.value,
        Permission.COMPETITION_READ.value,
        Permission.COMPETITION_LIST.value,
        Permission.TEAM_READ.value,
        Permission.TEAM_LIST.value,
    }