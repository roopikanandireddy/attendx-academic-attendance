import sys
import time
from datetime import datetime, timezone
sys.path.insert(0, ".")

from sqlalchemy import event
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.api.dashboard import get_admin_dashboard_data, get_lecturer_dashboard_data, student_dashboard

db_queries = []
db_durations = []

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.perf_counter()
    db_queries.append(statement)

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = (time.perf_counter() - context._query_start_time) * 1000.0
    db_durations.append(total)

db = SessionLocal()
admin = db.query(User).filter(User.role == "admin").first()
student = db.query(User).filter(User.role == "student").first()
lecturer = db.query(User).filter(User.role == "lecturer").first()

print("=" * 60)
print("MODULE 5: DASHBOARD QUERY OPTIMIZATION BENCHMARK (LOCAL)")
print("=" * 60)

# 1. Admin Dashboard Benchmark
runs = 5
admin_counts = []
admin_db_times = []
admin_total_times = []

for _ in range(runs):
    db_queries.clear()
    db_durations.clear()
    t0 = time.perf_counter()
    data = get_admin_dashboard_data(admin, db)
    t1 = time.perf_counter()
    admin_counts.append(len(db_queries))
    admin_db_times.append(sum(db_durations))
    admin_total_times.append((t1 - t0) * 1000.0)

avg_admin_count = sum(admin_counts) / len(admin_counts)
avg_admin_db = sum(admin_db_times) / len(admin_db_times)
avg_admin_tot = sum(admin_total_times) / len(admin_total_times)

print(f"\n[ADMIN DASHBOARD]")
print(f"Queries: {avg_admin_count:.0f} (Baseline: ~220) -> Reduction: {((220 - avg_admin_count)/220*100):.1f}%")
print(f"Database time: {avg_admin_db:.2f} ms (Baseline: ~110.45 ms)")
print(f"Endpoint time: {avg_admin_tot:.2f} ms")

# 2. Student Dashboard Benchmark
student_counts = []
student_db_times = []
student_total_times = []

for _ in range(runs):
    db_queries.clear()
    db_durations.clear()
    t0 = time.perf_counter()
    data = student_dashboard(student, db)
    t1 = time.perf_counter()
    student_counts.append(len(db_queries))
    student_db_times.append(sum(db_durations))
    student_total_times.append((t1 - t0) * 1000.0)

avg_stu_count = sum(student_counts) / len(student_counts)
avg_stu_db = sum(student_db_times) / len(student_db_times)
avg_stu_tot = sum(student_total_times) / len(student_total_times)

print(f"\n[STUDENT DASHBOARD]")
print(f"Queries: {avg_stu_count:.0f} (Baseline: ~31) -> Reduction: {((31 - avg_stu_count)/31*100):.1f}%")
print(f"Database time: {avg_stu_db:.2f} ms (Baseline: ~19.63 ms)")
print(f"Endpoint time: {avg_stu_tot:.2f} ms")

# 3. Lecturer Dashboard Benchmark
lecturer_counts = []
lecturer_db_times = []
lecturer_total_times = []

for _ in range(runs):
    db_queries.clear()
    db_durations.clear()
    t0 = time.perf_counter()
    data = get_lecturer_dashboard_data(lecturer, db)
    t1 = time.perf_counter()
    lecturer_counts.append(len(db_queries))
    lecturer_db_times.append(sum(db_durations))
    lecturer_total_times.append((t1 - t0) * 1000.0)

avg_lec_count = sum(lecturer_counts) / len(lecturer_counts)
avg_lec_db = sum(lecturer_db_times) / len(lecturer_db_times)
avg_lec_tot = sum(lecturer_total_times) / len(lecturer_total_times)

print(f"\n[LECTURER DASHBOARD]")
print(f"Queries: {avg_lec_count:.0f} (Baseline: ~32) -> Reduction: {((32 - avg_lec_count)/32*100):.1f}%")
print(f"Database time: {avg_lec_db:.2f} ms (Baseline: ~25.92 ms)")
print(f"Endpoint time: {avg_lec_tot:.2f} ms")

print("\n" + "=" * 60)
db.close()
