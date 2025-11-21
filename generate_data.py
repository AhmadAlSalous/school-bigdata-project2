import csv
import json
import os
import random
from datetime import date, timedelta

# -------------------------
# CONFIG: tweak here if needed
# -------------------------
N_STUDENTS = 50000          # bigger than before
N_ATTENDANCE = 2000000      # 2 million attendance records
SEED = 42                   # deterministic for reproducibility

random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "datasets", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

STUDENTS_CSV = os.path.join(RAW_DIR, "students.csv")
CLASSES_CSV = os.path.join(RAW_DIR, "classes.csv")
SEMESTERS_CSV = os.path.join(RAW_DIR, "semesters.csv")
ATTENDANCE_CSV = os.path.join(RAW_DIR, "attendance.csv")

STUDENTS_JSON = os.path.join(RAW_DIR, "students.jsonl")
CLASSES_JSON = os.path.join(RAW_DIR, "classes.jsonl")
SEMESTERS_JSON = os.path.join(RAW_DIR, "semesters.jsonl")
ATTENDANCE_JSON = os.path.join(RAW_DIR, "attendance.jsonl")

# -------------------------
# HELPERS
# -------------------------

FIRST_NAMES_M = [
    "Ahmed", "Omar", "Mohammed", "Hassan", "Khalid", "Yousef", "Ali", "Zayed",
    "Saif", "Salem"
]
FIRST_NAMES_F = [
    "Sara", "Aisha", "Layla", "Fatima", "Mariam", "Noor", "Hind", "Yasmin",
    "Lina", "Reem"
]
LAST_NAMES = [
    "Al Falahi", "Al Saadi", "Al Suwaidi", "Al Mazrouei", "Al Shamsi",
    "Al Murri", "Al Nuaimi", "Al Mansoori", "Al Zarooni", "Al Rashedi"
]
NATIONALITIES = ["Emirati", "Arab", "Indian", "Pakistani", "British", "American"]

def random_date(start: date, end: date) -> date:
    """Random date between start and end (inclusive)."""
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))

# -------------------------
# 1) CLASSES
# -------------------------

def generate_classes():
    """
    Simple model:
      - Grades 1-12
      - Each grade has sections A, B, C
      => class_id: 1..36
    """
    rows = []
    class_id = 1
    for grade in range(1, 13):  # 1 to 12
        for section in ["A", "B", "C"]:
            class_name = f"Grade {grade} - Section {section}"
            rows.append([class_id, class_name, grade])
            class_id += 1
    return rows

def write_classes_csv(path: str, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # no header
        for row in rows:
            writer.writerow(row)

def write_classes_json(path: str, rows):
    with open(path, "w", encoding="utf-8") as f:
        for class_id, class_name, grade_level in rows:
            obj = {
                "class_id": class_id,
                "class_name": class_name,
                "grade_level": grade_level,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# -------------------------
# 2) SEMESTERS
# -------------------------

def generate_semesters():
    """
    Semesters from 2018 to 2024:
      - Spring: Jan 15 – May 31
      - Fall:   Sep  1 – Dec 20
    """
    rows = []
    semester_id = 1
    for year in range(2018, 2025):
        # Spring
        spring_name = f"Spring {year}"
        spring_start = date(year, 1, 15)
        spring_end = date(year, 5, 31)
        rows.append([
            semester_id,
            spring_name,
            spring_start.isoformat(),
            spring_end.isoformat(),
        ])
        semester_id += 1

        # Fall
        fall_name = f"Fall {year}"
        fall_start = date(year, 9, 1)
        fall_end = date(year, 12, 20)
        rows.append([
            semester_id,
            fall_name,
            fall_start.isoformat(),
            fall_end.isoformat(),
        ])
        semester_id += 1

    return rows

def write_semesters_csv(path: str, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

def write_semesters_json(path: str, rows):
    with open(path, "w", encoding="utf-8") as f:
        for semester_id, name, start_date, end_date in rows:
            obj = {
                "semester_id": semester_id,
                "semester_name": name,
                "start_date": start_date,
                "end_date": end_date,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# -------------------------
# 3) STUDENTS
# -------------------------

def generate_students(classes):
    """
    Students:
      - student_id: 1..N_STUDENTS
      - Random name, gender, nationality
      - Random DOB between 1995 and 2015
      - grade_level derived from assigned class
      - class_id references classes
    """
    rows = []
    class_ids = [c[0] for c in classes]   # [class_id, class_name, grade_level]

    # Map class_id -> grade_level for quick lookup
    class_grade = {cid: grade for cid, cname, grade in classes}

    for student_id in range(1, N_STUDENTS + 1):
        gender = random.choice(["M", "F"])
        if gender == "M":
            first_name = random.choice(FIRST_NAMES_M)
        else:
            first_name = random.choice(FIRST_NAMES_F)

        last_name = random.choice(LAST_NAMES)
        nationality = random.choice(NATIONALITIES)

        dob = random_date(date(1995, 1, 1), date(2015, 12, 31))

        class_id = random.choice(class_ids)
        grade_level = class_grade[class_id]

        rows.append([
            student_id,           # student_id
            first_name,           # first_name
            last_name,            # last_name
            gender,               # gender
            nationality,          # nationality
            dob.isoformat(),      # birthdate
            grade_level,          # grade_level
            class_id,             # class_id
        ])

    return rows

def write_students_csv(path: str, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

def write_students_json(path: str, rows):
    with open(path, "w", encoding="utf-8") as f:
        for (
            student_id,
            first_name,
            last_name,
            gender,
            nationality,
            birthdate,
            grade_level,
            class_id,
        ) in rows:
            obj = {
                "student_id": student_id,
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "nationality": nationality,
                "birthdate": birthdate,
                "grade_level": grade_level,
                "class_id": class_id,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# -------------------------
# 4) ATTENDANCE
# -------------------------

def generate_attendance(students, classes, semesters):
    """
    attendance_id, student_id, class_id, attendance_date, grade
    - attendance_date random between min_semester_start and max_semester_end
    - we store grade as the measure (for dashboards)
    """
    rows = []

    min_date = date.fromisoformat(semesters[0][2])      # first semester start
    max_date = date.fromisoformat(semesters[-1][3])     # last semester end

    student_ids = [s[0] for s in students]

    # Build map student_id -> class_id(s)
    student_to_classes = {}
    for s in students:
        sid = s[0]
        class_id = s[-1]
        student_to_classes.setdefault(sid, []).append(class_id)

    for attendance_id in range(1, N_ATTENDANCE + 1):
        sid = random.choice(student_ids)
        cls_id = random.choice(student_to_classes[sid])
        att_date = random_date(min_date, max_date)

        grade = random.randint(40, 100)

        rows.append([
            attendance_id,
            sid,
            cls_id,
            att_date.isoformat(),
            grade,
        ])

        if attendance_id % 200000 == 0:
            print(f"  ...generated {attendance_id} attendance rows")

    return rows

def write_attendance_csv(path: str, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)

def write_attendance_json(path: str, rows):
    with open(path, "w", encoding="utf-8") as f:
        for (
            attendance_id,
            student_id,
            class_id,
            attendance_date,
            grade,
        ) in rows:
            obj = {
                "attendance_id": attendance_id,
                "student_id": student_id,
                "class_id": class_id,
                "attendance_date": attendance_date,
                "grade": grade,
            }
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# -------------------------
# MAIN
# -------------------------

def main():
    print(f"[INFO] Writing raw CSV + JSON into: {RAW_DIR}")

    # 1) Classes
    print("[STEP] Generating classes...")
    classes = generate_classes()
    write_classes_csv(CLASSES_CSV, classes)
    write_classes_json(CLASSES_JSON, classes)
    print(f"  -> classes.csv / classes.jsonl ({len(classes)} rows)")

    # 2) Semesters
    print("[STEP] Generating semesters...")
    semesters = generate_semesters()
    write_semesters_csv(SEMESTERS_CSV, semesters)
    write_semesters_json(SEMESTERS_JSON, semesters)
    print(f"  -> semesters.csv / semesters.jsonl ({len(semesters)} rows)")

    # 3) Students
    print("[STEP] Generating students...")
    students = generate_students(classes)
    write_students_csv(STUDENTS_CSV, students)
    write_students_json(STUDENTS_JSON, students)
    print(f"  -> students.csv / students.jsonl ({len(students)} rows)")

    # 4) Attendance
    print("[STEP] Generating attendance...")
    attendance = generate_attendance(students, classes, semesters)
    write_attendance_csv(ATTENDANCE_CSV, attendance)
    write_attendance_json(ATTENDANCE_JSON, attendance)
    print(f"  -> attendance.csv / attendance.jsonl ({len(attendance)} rows)")

    print("[DONE] Synthetic data generation complete.")

if __name__ == "__main__":
    main()
