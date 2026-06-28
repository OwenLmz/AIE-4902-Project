"""
Smart Campus — 模拟数据生成脚本
生成内容：
  1. gate_log_simulation.csv     闸机流量 30 天模拟数据（每 30 分钟一条）
  2. seat_status_simulation.csv  座位状态 30 天模拟数据（4 个演示座位，每 30 分钟一条）
  3. import_simulation.sql       可直接在 MySQL 中运行的导入文件

运行方式：
  python generate_sim_data.py

依赖：
  pip install pandas numpy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ── 固定随机种子，保证每次生成结果一致 ──────────────────────────
random.seed(42)
np.random.seed(42)

# ── 基础参数 ─────────────────────────────────────────────────────
START_DATE      = datetime(2025, 4, 1)
END_DATE        = datetime(2025, 4, 30, 23, 30)
CAPACITY        = 2000          # 图书馆总座位数
INTERVAL_MIN    = 30            # 采样间隔（分钟）
DEMO_SEATS      = ['F3-A01', 'F3-A02', 'F3-A03', 'F3-A04']  # 演示区座位

# 考试周区间（影响人流量 +50%）
EXAM_PERIODS = [
    (datetime(2025, 4, 21), datetime(2025, 4, 27)),
]

# ── 辅助函数 ─────────────────────────────────────────────────────
def is_exam_week(dt: datetime) -> int:
    for start, end in EXAM_PERIODS:
        if start.date() <= dt.date() <= end.date():
            return 1
    return 0


def library_open(dt: datetime) -> bool:
    """图书馆 08:00~22:00 开放"""
    return 8 <= dt.hour < 22


def target_occupancy(dt: datetime) -> float:
    """
    根据时段返回目标人数占比（0~1）。
    规律：上午缓升，下午平稳，晚间 19~21 点高峰，考试周 ×1.5，周末 ×0.65。
    """
    if not library_open(dt):
        return 0.0

    # 逐小时基础占比（工作日）
    base_by_hour = {
        8: 0.12, 9: 0.28, 10: 0.42, 11: 0.52,
        12: 0.38, 13: 0.44, 14: 0.55, 15: 0.60,
        16: 0.57, 17: 0.50, 18: 0.44, 19: 0.72,
        20: 0.85, 21: 0.78,
    }
    base = base_by_hour.get(dt.hour, 0.30)

    # 考试周加成
    if is_exam_week(dt):
        base = min(base * 1.5, 0.97)

    # 周末折减
    if dt.weekday() >= 5:   # 5=周六, 6=周日
        base *= 0.65

    # 加入随机扰动（±5%），模拟真实波动
    noise = np.random.normal(0, 0.03)
    return float(np.clip(base + noise, 0.0, 1.0))


def crowding_level(ratio: float) -> str:
    if ratio < 0.50:  return 'low'
    if ratio < 0.75:  return 'medium'
    if ratio < 0.90:  return 'high'
    return 'full'


def seat_state_from_occupancy(occ_ratio: float) -> dict:
    """
    根据全馆占用率，随机生成单个座位状态。
    占用率越高，有物/有人概率越高。
    """
    r = random.random()
    person_prob  = occ_ratio * 0.75   # 有人的概率
    object_prob  = occ_ratio * 0.20   # 有物无人（疑似占座）的概率

    if r < person_prob:
        return {'has_person': 1, 'has_object': 1, 'status': 'occupied',  'suspect_duration': 0}
    if r < person_prob + object_prob:
        # 疑似占座：随机分配一个疑似时长
        duration = random.choice([5, 10, 15, 20, 25, 30, 35, 40])
        if duration >= 20:
            status = 'suspected'
        else:
            status = 'occupied'   # 20 分钟以下还算正常
        return {'has_person': 0, 'has_object': 1, 'status': status, 'suspect_duration': duration}
    return {'has_person': 0, 'has_object': 0, 'status': 'free', 'suspect_duration': 0}


# ═══════════════════════════════════════════════════════════════
# 1. 生成 gate_log（闸机流量）
# ═══════════════════════════════════════════════════════════════
print("正在生成 gate_log 数据...")

gate_rows = []
total_in = 0
cur = START_DATE

while cur <= END_DATE:
    occ = target_occupancy(cur)
    target_num = int(CAPACITY * occ)

    if library_open(cur):
        diff = target_num - total_in
        if diff > 0:
            enter = max(0, diff + random.randint(0, 25))
            exit_ = max(0, random.randint(0, 18))
        else:
            enter = max(0, random.randint(0, 18))
            exit_ = max(0, -diff + random.randint(0, 25))
    else:
        # 闭馆：只出不进
        enter = 0
        exit_ = min(total_in, random.randint(5, 40)) if total_in > 0 else 0

    total_in = int(np.clip(total_in + enter - exit_, 0, CAPACITY))
    ratio    = total_in / CAPACITY

    gate_rows.append({
        'recorded_at':      cur.strftime('%Y-%m-%d %H:%M:%S'),
        'enter_count':      enter,
        'exit_count':       exit_,
        'total_in_library': total_in,
        'crowding_level':   crowding_level(ratio),
        'is_exam_week':     is_exam_week(cur),
        'day_of_week':      cur.weekday() + 1,   # 1=周一, 7=周日
        'hour_of_day':      cur.hour,
    })
    cur += timedelta(minutes=INTERVAL_MIN)

gate_df = pd.DataFrame(gate_rows)
gate_df.to_csv('gate_log_simulation.csv', index=False, encoding='utf-8-sig')
print(f"  ✓ gate_log_simulation.csv — {len(gate_df)} 条记录")


# ═══════════════════════════════════════════════════════════════
# 2. 生成 seat_status_log（演示区 4 个座位）
# ═══════════════════════════════════════════════════════════════
print("正在生成 seat_status_log 数据...")

seat_rows = []
seat_meta = {
    'F3-A01': {'floor': 3, 'zone': 'A'},
    'F3-A02': {'floor': 3, 'zone': 'A'},
    'F3-A03': {'floor': 3, 'zone': 'A'},
    'F3-A04': {'floor': 3, 'zone': 'A'},
}

# 用 gate_df 中每个时间点的拥挤比例驱动座位状态
gate_ratio = {
    row['recorded_at']: row['total_in_library'] / CAPACITY
    for _, row in gate_df.iterrows()
}

for ts, ratio in gate_ratio.items():
    for seat_id in DEMO_SEATS:
        meta  = seat_meta[seat_id]
        state = seat_state_from_occupancy(ratio)
        seat_rows.append({
            'seat_id':          seat_id,
            'floor':            meta['floor'],
            'zone':             meta['zone'],
            'detected_at':      ts,
            'has_person':       state['has_person'],
            'has_object':       state['has_object'],
            'status':           state['status'],
            'suspect_duration': state['suspect_duration'],
        })

seat_df = pd.DataFrame(seat_rows)
seat_df.to_csv('seat_status_simulation.csv', index=False, encoding='utf-8-sig')
print(f"  ✓ seat_status_simulation.csv — {len(seat_df)} 条记录")


# ═══════════════════════════════════════════════════════════════
# 3. 生成可直接运行的 SQL 导入文件
# ═══════════════════════════════════════════════════════════════
print("正在生成 import_simulation.sql...")

def df_to_insert(df: pd.DataFrame, table: str, chunk: int = 200) -> list[str]:
    """把 DataFrame 切成 chunk 行一批的 INSERT 语句"""
    cols = ', '.join(df.columns)
    stmts = []
    for i in range(0, len(df), chunk):
        batch = df.iloc[i:i+chunk]
        vals  = []
        for _, row in batch.iterrows():
            row_vals = []
            for v in row:
                if pd.isna(v):
                    row_vals.append('NULL')
                elif isinstance(v, str):
                    v_esc = v.replace("'", "''")
                    row_vals.append(f"'{v_esc}'")
                else:
                    row_vals.append(str(int(v) if float(v) == int(v) else v))
            vals.append(f"({', '.join(row_vals)})")
        stmts.append(f"INSERT INTO {table} ({cols}) VALUES\n" + ',\n'.join(vals) + ';')
    return stmts

with open('import_simulation.sql', 'w', encoding='utf-8') as f:
    f.write("-- Smart Campus 模拟数据导入文件\n")
    f.write("-- 运行前请先执行 library_schema_fixed.sql 建好表\n")
    f.write("USE smart_campus;\n\n")

    f.write("-- ── gate_log ──────────────────────────────────────\n")
    for stmt in df_to_insert(gate_df, 'gate_log'):
        f.write(stmt + '\n\n')

    f.write("-- ── seat_status_log ───────────────────────────────\n")
    for stmt in df_to_insert(seat_df, 'seat_status_log'):
        f.write(stmt + '\n\n')

print(f"  ✓ import_simulation.sql 生成完成")

# ═══════════════════════════════════════════════════════════════
# 4. 数据质量检查
# ═══════════════════════════════════════════════════════════════
print("\n── 数据质量检查 ──")
print(f"gate_log  总记录: {len(gate_df)}")
print(f"  拥挤等级分布:\n{gate_df['crowding_level'].value_counts().to_string()}")
print(f"  考试周记录数: {gate_df['is_exam_week'].sum()}")
print(f"  馆内人数范围: {gate_df['total_in_library'].min()} ~ {gate_df['total_in_library'].max()}")
print(f"  考试周最高人数: {gate_df[gate_df['is_exam_week']==1]['total_in_library'].max()}")
print(f"  非考试周最高人数: {gate_df[gate_df['is_exam_week']==0]['total_in_library'].max()}")

print(f"\nseat_status_log 总记录: {len(seat_df)}")
print(f"  座位状态分布:\n{seat_df['status'].value_counts().to_string()}")
print(f"  疑似占座记录数: {(seat_df['status']=='suspected').sum()}")
print("\n── 生成完毕 ──")
