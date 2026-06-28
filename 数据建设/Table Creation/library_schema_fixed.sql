-- ============================================================
-- Smart Campus 
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_campus
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE smart_campus;


-- ============================================================
-- 表 1：座位配置表 seat_config
-- 记录每个座位的基本信息和摄像头坐标
-- ============================================================
CREATE TABLE seat_config (
    seat_id       VARCHAR(20)  NOT NULL            COMMENT '座位编号，如 F3-A12（F3=3楼，A=A区，12=第12号）',
    floor         TINYINT      NOT NULL            COMMENT '楼层，1~5',
    zone          VARCHAR(10)  NOT NULL            COMMENT '区域编号，如 A、B、C',
    camera_id     VARCHAR(20)  NOT NULL            COMMENT '负责拍摄该座位的摄像头编号',
    roi_x1        SMALLINT     NOT NULL            COMMENT '座位在图像中的左上角 x 坐标（像素）',
    roi_y1        SMALLINT     NOT NULL            COMMENT '座位在图像中的左上角 y 坐标（像素）',
    roi_x2        SMALLINT     NOT NULL            COMMENT '座位在图像中的右下角 x 坐标（像素）',
    roi_y2        SMALLINT     NOT NULL            COMMENT '座位在图像中的右下角 y 坐标（像素）',
    is_active     TINYINT(1)   NOT NULL DEFAULT 1  COMMENT '该座位是否启用：1=启用，0=封闭/维修',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',

    PRIMARY KEY (seat_id),
    INDEX idx_floor      (floor),
    INDEX idx_floor_zone (floor, zone),
    INDEX idx_camera     (camera_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='座位基础配置表（含摄像头 ROI 坐标），一次性录入，不频繁变动';


-- ============================================================
-- 表 2：座位状态日志表 seat_status_log
-- 存储每次 AI 推理后写入的识别结果
-- 读请求走 Redis 缓存，此表只做历史存档和疑似占座追溯
-- ============================================================
CREATE TABLE seat_status_log (
    id                 BIGINT       NOT NULL AUTO_INCREMENT  COMMENT '自增主键',
    seat_id            VARCHAR(20)  NOT NULL                 COMMENT '座位编号，关联 seat_config.seat_id',
    floor              TINYINT      NOT NULL                 COMMENT '楼层（冗余存储，方便按楼层聚合查询）',
    zone               VARCHAR(10)  NOT NULL                 COMMENT '区域（冗余存储）',
    detected_at        DATETIME     NOT NULL                 COMMENT '本次识别的时间戳（来自摄像头帧时间）',
    has_person         TINYINT(1)   NOT NULL DEFAULT 0       COMMENT 'YOLO 是否检测到人：1=有人，0=无人',
    has_object         TINYINT(1)   NOT NULL DEFAULT 0       COMMENT 'YOLO 是否检测到物品（书包/电脑/书本等）：1=有，0=无',
    status             VARCHAR(20)  NOT NULL                 COMMENT '座位状态：free=空闲 / occupied=使用中 / suspected=疑似占座 / unavailable=不可用',
    suspect_duration   SMALLINT     NOT NULL DEFAULT 0       COMMENT '疑似占座累计时长（分钟）。有人则归零，有物无人则累加',

    PRIMARY KEY (id),
    INDEX idx_seat_time   (seat_id, detected_at),   -- 查询某座位的历史状态
    INDEX idx_time        (detected_at),             -- 按时间段批量查询
    INDEX idx_floor_time  (floor, detected_at),      -- 按楼层聚合
    INDEX idx_status      (status, detected_at)      -- 快速找疑似占座记录
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='座位状态历史日志（每30分钟写入一次，读请求走Redis缓存）';


-- ============================================================
-- 表 3：闸机流量表 gate_log
-- 记录闸机进出馆数据，用于计算当前馆内总人数
-- 同时作为 XGBoost 人流预测模型的训练数据
-- ============================================================
CREATE TABLE gate_log (
    id               INT         NOT NULL AUTO_INCREMENT  COMMENT '自增主键',
    recorded_at      DATETIME    NOT NULL                 COMMENT '记录时间（每5分钟或10分钟汇总一次）',
    enter_count      SMALLINT    NOT NULL DEFAULT 0       COMMENT '本时段进馆人数',
    exit_count       SMALLINT    NOT NULL DEFAULT 0       COMMENT '本时段出馆人数',
    total_in_library SMALLINT    NOT NULL DEFAULT 0       COMMENT '当前馆内总人数（滚动计算：上次人数+进馆-出馆）',
    crowding_level   VARCHAR(10) NOT NULL                 COMMENT '拥挤等级：low=低 / medium=中 / high=高 / full=满载预警',
    is_exam_week     TINYINT(1)  NOT NULL DEFAULT 0       COMMENT '是否考试周：1=是，0=否（供预测模型使用）',
    day_of_week      TINYINT     NOT NULL                 COMMENT '星期几：1=周一，7=周日（供预测模型使用）',
    hour_of_day      TINYINT     NOT NULL                 COMMENT '小时（0~23，供预测模型使用）',

    PRIMARY KEY (id),
    UNIQUE INDEX idx_recorded_at (recorded_at),    -- 同一时刻只有一条记录
    INDEX idx_exam_week_time (is_exam_week, recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='闸机进出馆流量记录（用于人流展示和 XGBoost 预测模型训练）';


-- ============================================================
-- 表 4：用户表 users
-- 存储学生、管理员、校方三类用户
-- ============================================================
CREATE TABLE users (
    id            INT          NOT NULL AUTO_INCREMENT  COMMENT '自增主键',
    student_id    VARCHAR(20)  NOT NULL                 COMMENT '学号或工号（唯一标识）',
    name          VARCHAR(50)  NOT NULL                 COMMENT '姓名',
    role          VARCHAR(20)  NOT NULL DEFAULT 'student' COMMENT '角色：student=学生 / admin=管理员 / manager=校方',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '账号创建时间',
    last_login_at DATETIME                              COMMENT '最后登录时间',

    PRIMARY KEY (id),
    UNIQUE INDEX idx_student_id (student_id),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='用户账号表（学生、管理员、校方三类角色）';


-- ============================================================
-- 表 5：申诉记录表 appeal
-- 学生对系统误判提出申诉，或举报真实占座行为
-- 管理员处理后写入结果
-- ============================================================
CREATE TABLE appeal (
    id            INT          NOT NULL AUTO_INCREMENT  COMMENT '自增主键',
    seat_id       VARCHAR(20)  NOT NULL                 COMMENT '涉及的座位编号',
    submitted_by  INT          NOT NULL                 COMMENT '提交申诉的用户 id（关联 users.id）',
    submitted_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    issue_type    VARCHAR(30)  NOT NULL                 COMMENT '问题类型：false_alarm=误判申诉 / real_squatter=举报占座 / other=其他',
    description   TEXT                                  COMMENT '申诉描述（学生填写）',
    status        VARCHAR(20)  NOT NULL DEFAULT 'pending' COMMENT '处理状态：pending=待处理 / processing=处理中 / resolved=已处理',
    result        VARCHAR(30)                           COMMENT '处理结果：confirmed=确认占座并释放 / normal_use=正常使用 / false_alarm=系统误判已纠正 / no_action=暂不处理',
    handled_by    INT                                   COMMENT '处理该申诉的管理员 id（关联 users.id）',
    handled_at    DATETIME                              COMMENT '处理完成时间',

    PRIMARY KEY (id),
    INDEX idx_seat_id    (seat_id),
    INDEX idx_status     (status),
    INDEX idx_submitted  (submitted_at),
    INDEX idx_handled_by (handled_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='学生申诉记录表（误判申诉 + 占座举报），管理员处理后写入结果';


-- ============================================================
-- 表 6：管理员处理日志 admin_action_log
-- 管理员对疑似占座的每一次处理动作都留有记录
--  可用于后续优化识别规则和减少误判
-- ============================================================
CREATE TABLE admin_action_log (
    id           INT          NOT NULL AUTO_INCREMENT  COMMENT '自增主键',
    seat_id      VARCHAR(20)  NOT NULL                 COMMENT '被处理的座位编号',
    action       VARCHAR(30)  NOT NULL                 COMMENT '处理动作：release=确认占座释放 / keep=正常使用保留 / hold=暂不处理 / false_alarm=系统误判',
    admin_id     INT          NOT NULL                 COMMENT '操作管理员的 id（关联 users.id）',
    note         VARCHAR(200)                          COMMENT '管理员备注（可选）',
    acted_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    suspect_min_at_action SMALLINT NOT NULL DEFAULT 0  COMMENT '处理时该座位已疑似占座的分钟数（用于评估规则合理性）',

    PRIMARY KEY (id),
    INDEX idx_seat_id  (seat_id),
    INDEX idx_admin    (admin_id),
    INDEX idx_acted_at (acted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='管理员处理疑似占座的操作日志（用于审计和规则优化）';


-- ============================================================
-- 示例数据（用于本地测试）
-- ============================================================

-- 插入座位配置示例（3楼A区，前4个座位）
INSERT INTO seat_config (seat_id, floor, zone, camera_id, roi_x1, roi_y1, roi_x2, roi_y2) VALUES
('F3-A01', 3, 'A', 'CAM-3A', 120, 80,  280, 200),
('F3-A02', 3, 'A', 'CAM-3A', 290, 80,  450, 200),
('F3-A03', 3, 'A', 'CAM-3A', 120, 210, 280, 330),
('F3-A04', 3, 'A', 'CAM-3A', 290, 210, 450, 330);

-- 插入用户示例
INSERT INTO users (student_id, name, role) VALUES
('2021001001', '张同学',   'student'),
('2021001002', '李同学',   'student'),
('LIB-ADMIN1', '王管理员', 'admin'),
('SCHOOL-MGR', '图书馆主任', 'manager');

-- 插入闸机数据示例（工作日早上，模拟人数爬升）
INSERT INTO gate_log (recorded_at, enter_count, exit_count, total_in_library, crowding_level, is_exam_week, day_of_week, hour_of_day) VALUES
('2025-06-16 08:00:00',  15,  2,   13, 'low',    0, 1, 8),
('2025-06-16 08:30:00',  42,  5,   50, 'low',    0, 1, 8),
('2025-06-16 09:00:00',  88, 12,  126, 'low',    0, 1, 9),
('2025-06-16 19:00:00', 210, 45,  680, 'high',   0, 1, 19),
('2025-06-16 20:00:00', 120, 90,  710, 'high',   0, 1, 20),
('2025-06-16 21:30:00',  30, 180, 412, 'medium', 0, 1, 21);

-- 插入座位状态示例（F3-A01 疑似占座 22 分钟）
INSERT INTO seat_status_log (seat_id, floor, zone, detected_at, has_person, has_object, status, suspect_duration) VALUES
('F3-A01', 3, 'A', '2025-06-16 20:00:00', 0, 1, 'suspected', 22),
('F3-A02', 3, 'A', '2025-06-16 20:00:00', 1, 1, 'occupied',   0),
('F3-A03', 3, 'A', '2025-06-16 20:00:00', 0, 0, 'free',        0),
('F3-A04', 3, 'A', '2025-06-16 20:00:00', 0, 1, 'suspected',   8);

-- 插入申诉示例（学生认为 F3-A01 是自己的座位被误判）
INSERT INTO appeal (seat_id, submitted_by, issue_type, description, status) VALUES
('F3-A01', 1, 'false_alarm', '这是我的座位，我去打印文件了，书包还在，不是占座', 'pending');

