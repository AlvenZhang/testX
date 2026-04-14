-- AI Test Platform 数据库初始化脚本
-- 运行: mysql -u root -p < init.sql

CREATE DATABASE IF NOT EXISTS aitest DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE aitest;

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    git_url VARCHAR(500) COMMENT 'Git仓库地址',
    config JSON COMMENT '项目配置，包含test_types和default_framework',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

-- 项目成员权限表
CREATE TABLE IF NOT EXISTS project_members (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    user_id VARCHAR(36) NOT NULL COMMENT '用户ID',
    role ENUM('viewer', 'editor', 'executor', 'admin') DEFAULT 'viewer' COMMENT '角色：查看者/编辑者/执行者/管理员',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY uk_project_user (project_id, user_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目成员表';

-- 需求表
CREATE TABLE IF NOT EXISTS requirements (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    title VARCHAR(500) NOT NULL COMMENT '需求标题',
    description TEXT COMMENT '需求描述',
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium' COMMENT '优先级',
    type ENUM('function', 'api', 'ui') DEFAULT 'function' COMMENT '需求类型',
    status ENUM('pending', 'cases_generated', 'code_generated', 'tested') DEFAULT 'pending' COMMENT '状态',
    version INT DEFAULT 1 COMMENT '版本号',
    metadata JSON COMMENT '额外元数据',
    attachment_url VARCHAR(500) COMMENT '需求文档URL',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求表';

-- 需求版本历史表
CREATE TABLE IF NOT EXISTS requirement_versions (
    id VARCHAR(36) PRIMARY KEY,
    requirement_id VARCHAR(36) NOT NULL COMMENT '需求ID',
    version INT NOT NULL COMMENT '版本号',
    title VARCHAR(500) COMMENT '标题',
    description TEXT COMMENT '描述',
    diff JSON COMMENT '变更内容',
    created_by VARCHAR(36) COMMENT '创建人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE,
    INDEX idx_requirement_id (requirement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='需求版本历史表';

-- 代码关联表
CREATE TABLE IF NOT EXISTS code_changes (
    id VARCHAR(36) PRIMARY KEY,
    requirement_id VARCHAR(36) NOT NULL COMMENT '需求ID',
    change_type ENUM('git_commit', 'git_pr', 'manual') DEFAULT 'manual' COMMENT '变更类型',
    git_url VARCHAR(500) COMMENT 'Git地址',
    commit_hash VARCHAR(40) COMMENT '提交hash',
    diff_content TEXT COMMENT 'Diff内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE,
    INDEX idx_requirement_id (requirement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码关联表';

-- 测试用例表
CREATE TABLE IF NOT EXISTS test_cases (
    id VARCHAR(36) PRIMARY KEY,
    requirement_id VARCHAR(36) NOT NULL COMMENT '需求ID',
    case_id VARCHAR(50) NOT NULL COMMENT '用例编号',
    title VARCHAR(500) NOT NULL COMMENT '用例标题',
    steps TEXT COMMENT 'JSON数组格式的步骤',
    expected_result TEXT COMMENT '预期结果',
    priority ENUM('low', 'medium', 'high') DEFAULT 'medium' COMMENT '优先级',
    status ENUM('active', 'deprecated') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE,
    INDEX idx_requirement_id (requirement_id),
    UNIQUE KEY uk_case_id (case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例表';

-- 测试方案表
CREATE TABLE IF NOT EXISTS test_plans (
    id VARCHAR(36) PRIMARY KEY,
    requirement_id VARCHAR(36) NOT NULL COMMENT '需求ID',
    test_scope TEXT COMMENT '测试范围',
    test_types JSON COMMENT '测试类型数组',
    test_strategy TEXT COMMENT '测试策略',
    risk_points TEXT COMMENT '风险点',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE,
    INDEX idx_requirement_id (requirement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试方案表';

-- 测试代码表
CREATE TABLE IF NOT EXISTS test_code (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    requirement_id VARCHAR(36) COMMENT '需求ID',
    test_case_ids JSON COMMENT '关联的用例ID数组',
    framework ENUM('pytest', 'testng', 'playwright') NOT NULL COMMENT '测试框架',
    code_content TEXT NOT NULL COMMENT '代码内容',
    version INT DEFAULT 1 COMMENT '版本号',
    status ENUM('active', 'deprecated') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE SET NULL,
    INDEX idx_project_id (project_id),
    INDEX idx_requirement_id (requirement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试代码表';

-- 测试代码历史表
CREATE TABLE IF NOT EXISTS test_code_history (
    id VARCHAR(36) PRIMARY KEY,
    test_code_id VARCHAR(36) NOT NULL COMMENT '测试代码ID',
    version INT NOT NULL COMMENT '版本号',
    code_content TEXT NOT NULL COMMENT '代码内容',
    change_reason TEXT COMMENT '变更原因',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_code_id) REFERENCES test_code(id) ON DELETE CASCADE,
    INDEX idx_test_code_id (test_code_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试代码历史表';

-- 测试执行记录表
CREATE TABLE IF NOT EXISTS test_runs (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL COMMENT '项目ID',
    test_code_id VARCHAR(36) NOT NULL COMMENT '测试代码ID',
    status ENUM('pending', 'running', 'success', 'failed', 'cancelled') DEFAULT 'pending' COMMENT '执行状态',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    container_id VARCHAR(100) COMMENT 'Docker容器ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (test_code_id) REFERENCES test_code(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试执行记录表';

-- 测试报告表
CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) PRIMARY KEY,
    test_run_id VARCHAR(36) NOT NULL COMMENT '测试执行ID',
    total_cases INT DEFAULT 0 COMMENT '总用例数',
    passed_cases INT DEFAULT 0 COMMENT '通过数',
    failed_cases INT DEFAULT 0 COMMENT '失败数',
    duration_ms INT DEFAULT 0 COMMENT '执行时长(毫秒)',
    report_type ENUM('new_feature', 'regression') DEFAULT 'new_feature' COMMENT '报告类型',
    report_data JSON COMMENT '详细报告内容',
    log_content TEXT COMMENT '日志内容',
    screenshots JSON COMMENT '截图路径数组',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (test_run_id) REFERENCES test_runs(id) ON DELETE CASCADE,
    INDEX idx_test_run_id (test_run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试报告表';

-- AI影响分析记录表
CREATE TABLE IF NOT EXISTS impact_analyses (
    id VARCHAR(36) PRIMARY KEY,
    requirement_id VARCHAR(36) NOT NULL COMMENT '需求ID',
    impacted_requirements JSON COMMENT '受影响的需求列表',
    impacted_test_codes JSON COMMENT '受影响的测试代码',
    impact_levels JSON COMMENT '影响等级',
    report_content TEXT COMMENT '完整分析报告',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requirement_id) REFERENCES requirements(id) ON DELETE CASCADE,
    INDEX idx_requirement_id (requirement_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI影响分析记录表';

-- 操作审计表
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) COMMENT '项目ID',
    user_id VARCHAR(36) COMMENT '用户ID',
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    entity_type VARCHAR(50) COMMENT '实体类型',
    entity_id VARCHAR(36) COMMENT '实体ID',
    before_data JSON COMMENT '变更前数据',
    after_data JSON COMMENT '变更后数据',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计表';
